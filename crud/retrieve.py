from PIL import Image
from crud import inquiry
from pathlib import Path
from schema import retrieve as retrieve_schema
from urllib.parse import quote
from typing import List,Optional,Tuple,Dict
from loguru import logger
from fastapi import UploadFile,File,status,HTTPException
from starlette.concurrency import run_in_threadpool
from model import retrieve as retrieve_model
from sqlalchemy import select,text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import os
from uuid import uuid4
from utils import vgg16_feature_extraction,data_collection,openclip_feature_extraction
from torch.utils import data
import torch
from torch.nn import functional as F
import random
from pathlib import Path
import numpy as np
import faiss
from collections import defaultdict

async def fetch_image_from_folder(folder:str,config_path:Optional[str])->List[retrieve_schema.ImageInfo]:
    """
    Args:
        folder: 目录地址
        config_path: 配置文件路径
    Returns:
        ImageInfo列表
    """
    config=inquiry.load_config(config_file=config_path)
    image_extensions=config.get("image_extensions")
    folder=Path(folder)
    # 判断目录是否存在
    if not folder.exists():
        logger.error(f"{folder} does not exist!")
        raise FileExistsError(f"{folder} does not exist!") from None
    images=list()
    # 递归的获取目录中的所有文件子目录中的所有文件
    for file in folder.rglob(pattern="*"):
        if file.is_file() and file.suffix.lower() in image_extensions:
            name=file.name
            image_url=f"/retrieve/get/localImage?image={quote(str(file))}"
            image_info=retrieve_schema.ImageInfo(name=name,image_url=image_url)
            images.append(image_info)
    return images

async def loading_image(config_path:str,folder:str,images:List[UploadFile]=File(...))->List[retrieve_schema.ImageInfo]:
    """
    Args:
        config_path: 配置文件路径
        folder: 选择的文件路径
        images: 从前端获取的文件信息
    Returns:
        处理之后的图片信息
    """
    config = inquiry.load_config(config_file=config_path)
    gallery_dir=config.get("gallery_dir")
    image_extensions = config.get("image_extensions")
    thumbnail_height=config["thumbnail"]["size"]["height"]
    thumbnail_width=config["thumbnail"]["size"]["width"]
    # 图片保存在gallery_dir目录的子目录里面，子目录名由选择的目录名决定
    gallery_dir_path=Path(__file__).parent.parent.joinpath(gallery_dir,folder)
    upload_images=list()
    # 如果目录不存在，创建
    if not gallery_dir_path.exists():
        logger.warning(f"{str(gallery_dir_path)} does not exist!")
        gallery_dir_path.mkdir(parents=True,exist_ok=True)
    # 遍历所有的文件数据
    for index,image in enumerate(images):
        image_path=Path(image.filename)
        ext=image_path.suffix.lower()
        if ext not in image_extensions:
            continue
        try:
            dest=gallery_dir_path.joinpath(f"{index:0>4}_{image_path.name}")
            # 将图片流式保存在后端，避免大文件占用内存
            with open(dest,"wb") as file:
                chunk=await image.read(size=1024*1024)
                while chunk:
                    file.write(chunk)
                    chunk=await image.read(size=1024*1024)
            # 从已落盘的文件生成缩略图（上传流已读到 EOF，不能再读）
            with Image.open(dest) as pil_img:
                max_size = (thumbnail_width, thumbnail_height)
                # Image.LANCZOS 是高质量的插值算法，用于缩小图片时保留更多细节
                pil_img.thumbnail(size=max_size, resample=Image.LANCZOS)
                # 缩略图的路径
                thumbnail_path=gallery_dir_path.joinpath(f"{index:0>4}_thumbnail_{image_path.name}")
                # 保存缩略图
                pil_img.save(thumbnail_path)
            upload_images.append(
                retrieve_schema.ImageInfo(
                    name=image.filename,
                    image_url=f"/{gallery_dir}/{folder}/{dest.name}",
                    thumbnail=f"/{gallery_dir}/{folder}/{thumbnail_path.name}",
                )
            )
        except Exception as error:
            # 单张图片处理失败不影响整批上传
            logger.error(f"Failed to load image {image.filename}: {error}")
    return upload_images

# 更新folders表
async def add_folder_data(folder:str,db:AsyncSession)->str:
    """
    Args:
        folder: 前端需要登录的目录
        db: 数据库对象
    Returns:
        缩略图存放目录
    """
    stmt=select(
        retrieve_model.Folders.indicate
    ).where(
        retrieve_model.Folders.folder_path == folder
    )
    result= await db.execute(stmt)
    indicate=result.scalar_one_or_none()
    if not indicate:
        # 随机唯一indicate
        indicate=uuid4().hex
        folder_data=retrieve_model.Folders(
            folder_path=folder,
            name=os.path.basename(folder),
            indicate=indicate,
        )
        db.add(folder_data)
        try:
            await db.commit()
            logger.info(f"Successfully added folder {folder}")
        except SQLAlchemyError:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Failed to log in to {folder}")
    return indicate

def _generate_thumbnail_image_sync(file_path: str,thumbnail_path: str,thumbnail_config: Dict)->str:
    """PIL 解码/缩放/保存是 CPU 密集的同步操作
    Args:
        file_path: 原始图片路径
        thumbnail_path: 缩略图路径
        thumbnail_config: 缩略图配置
    Returns:
        str: 最终生成的缩略图路径
    """
    height = thumbnail_config["size"]["height"]
    width = thumbnail_config["size"]["width"]
    with Image.open(file_path) as pil_img:
        max_size = (width, height)
        pil_img.thumbnail(
            size=max_size,
            resample=Image.LANCZOS
        )
        try:
            pil_img.save(thumbnail_path)
        except OSError:
            logger.warning(
                f"Failed to save thumbnail {thumbnail_path}, "
                f"image mode is {pil_img.mode}"
            )
            # 改成 PNG
            thumbnail_path = (
                os.path.splitext(thumbnail_path)[0] + ".png"
            )
            # PNG 对 RGBA 等模式支持比较好
            pil_img.save(thumbnail_path)
    return thumbnail_path

async def generate_thumbnail_image(file_path: str,thumbnail_path: str,thumbnail_config: Dict)->str:
    """生成缩略图并保存（在线程池中执行，避免阻塞事件循环）
    Args:
        file_path: 原始图片路径
        thumbnail_path: 缩略图路径
        thumbnail_config: 缩略图配置
    Returns:
        str: 最终生成的缩略图路径
    """
    return await run_in_threadpool(
        _generate_thumbnail_image_sync,
        file_path,
        thumbnail_path,
        thumbnail_config,
    )

# 登录folder中的图片数据
async def loging_folder_images(thumbnail_dir:str,folder:str,config_path:str,db:AsyncSession):
    """
    Args:
        folder: 需要操作的目录
        thumbnail_dir: 缩略图存放目录
        config_path: 配置文件路径
        db: 数据库对象
    """
    # 获取配置
    config=inquiry.load_config(config_file=config_path)
    # 缩略图存放目录
    gallery_dir=config["gallery_dir"]
    upload_dir=Path(__file__).parent.parent.joinpath(gallery_dir).resolve()
    thumbnail_folder_path=upload_dir.joinpath(thumbnail_dir)
    folder_path = Path(folder)
    # 获取对应的folder_id
    stmt=select(
        retrieve_model.Folders.id
    ).where(
        retrieve_model.Folders.indicate == thumbnail_dir,
    )
    result = await db.execute(stmt)
    folder_id=result.scalar()
    # image扩展名配置
    image_extensions=config.get("image_extensions")
    # thumbnail配置
    thumbnail_config=config["thumbnail"]
    # thumbnail dir 不存在，收集folder下的所有图片
    if not thumbnail_folder_path.exists():
        logger.info(f"Upload {folder} images")
        # 创建目录
        thumbnail_folder_path.mkdir(parents=True,exist_ok=True)
        for index,file in enumerate(folder_path.rglob("*")):
            if file.is_file():
                if file.suffix.lower() in image_extensions:
                    thumbnail_path=thumbnail_folder_path.joinpath(f"{index:0>4}_thumbnail_{file.name}")
                    thumbnail_path=await generate_thumbnail_image(file_path=str(file),thumbnail_path=str(thumbnail_path),thumbnail_config=thumbnail_config)
                    image_data=retrieve_model.Images(
                        folder_id=folder_id,
                        path=str(file),
                        name=file.name,
                        extension=file.suffix.lower(),
                        thumbnail_path=f"/upload/{thumbnail_dir}/{Path(thumbnail_path).name}"
                    )
                    db.add(image_data)
                    await db.commit()
    # thumbnail dir 存在，更新thumbnail dir下的数据
    else:
        logger.info(f"Update {folder} images")
        stmt=select(
            retrieve_model.Images.path
        ).where(
            retrieve_model.Images.folder_id==folder_id,
        )
        result = await db.execute(stmt)
        db_paths=result.scalars().all()
        file_paths=[str(path) for path in folder_path.rglob("*") if path.is_file() and path.suffix.lower() in image_extensions]
        set_db_paths=set(db_paths)
        missing_paths=[Path(file_path) for file_path in file_paths if file_path not in set_db_paths]
        for missing_path in missing_paths:
            thumbnail_path=thumbnail_folder_path.joinpath(f"thumbnail_{missing_path.name}")
            await generate_thumbnail_image(file_path=str(missing_path),thumbnail_path=str(thumbnail_path),thumbnail_config=thumbnail_config)
            image_data=retrieve_model.Images(
                folder_id=folder_id,
                path=str(missing_path),
                name=missing_path.name,
                extension=missing_path.suffix.lower(),
                thumbnail_path=f"/upload/{thumbnail_dir}/thumbnail_{missing_path.name}"
            )
            db.add(image_data)
            await db.commit()

async def fetch_images(folder:str,page:int,page_size:int,db:AsyncSession):
    offset=(page-1)*page_size
    stmt = (
        select(retrieve_model.Images)
        .join(
            retrieve_model.Folders,
            retrieve_model.Folders.id == retrieve_model.Images.folder_id
        )
        .where(
            retrieve_model.Folders.folder_path == folder
        )
        .limit(
            limit=page_size
        )
        .offset(
            offset=offset
        )
    )
    result=await db.execute(stmt)
    images=result.scalars().all()
    if len(images)==0:
        logger.warning(f"No more pictures!")
        return None
    return images

# 获取模型
async def fetch_model(db:AsyncSession):
    stmt=select(
        retrieve_model.Models.model
    )
    result=await db.execute(stmt)
    models=result.scalars().all()
    return models

async def image_path_to_folder_id(image_path:str,db:AsyncSession)->int:
    """
    Args:
        image_path: 图片路径
        db: 数据库
    Returns:
        目录id
    """
    stmt = select(retrieve_model.Images.folder_id).where(
        retrieve_model.Images.path == image_path
    )
    result = await db.execute(stmt)
    folder_id=result.scalar_one_or_none()
    if folder_id is None:
        logger.error(f"Image missing {image_path}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Image missing {image_path}")
    return folder_id

# 根据目录id获取目录路径
async def folder_id_to_path(folder_id:int,db:AsyncSession)->str:
    stmt=select(
        retrieve_model.Folders.folder_path
    ).where(
        retrieve_model.Folders.id == folder_id
    )
    result=await db.execute(statement=stmt)
    folder_path=result.scalar_one_or_none()
    if folder_path is None:
        logger.error(f"Folder missing {folder_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Folder missing {folder_id}")
    return folder_path

# 获取目录中所有的图片
async def fetch_image_collection(folder_id:int,db:AsyncSession):
    stmt=select(
        retrieve_model.Images.path
    ).where(
        retrieve_model.Images.folder_id == folder_id
    )
    result=await db.execute(stmt)
    image_collection=result.scalars().all()
    return image_collection

async def insert_dat_(dataset:List,db:AsyncSession):
    try:
        db.add_all(dataset)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Insert data error !")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Insert data error !")

# 保存vgg16特征向量
async def vgg16_image_feature_vector(image_path:str,config_file:str,db:AsyncSession):
    """
    将vgg16模型获取的特征向量存放到目录中，目录格式如下：
    |- vector # 根目录
      |- model # 获取特征向量的模型名称
        |- folder_id # image_path对应的目录的id
          |- image_name.npy # 存放的特长向量
          |- ...

    Args:
        image_path: 随机一张集合里面的图片
        config_file: 配置文件路径
        db: 数据库
    """
    # 登录配置文件
    config=inquiry.load_config(config_file=config_file)
    # 存放需要插入的数据
    images_feature=list()
    # 获取特征向量存放的目录
    vector_dir=config["vector_dir"]
    # 特征向量存放目录下的模型目录
    model_dir="vgg16"
    feature_extract = vgg16_feature_extraction.Vgg16FeatureExtractor(config_path=config_file)
    # 设备选择
    device = feature_extract.device
    random_image_path=image_path
    folder_id=await image_path_to_folder_id(image_path=random_image_path,db=db)
    # 获取image_collection
    image_collection=await fetch_image_collection(folder_id=folder_id,db=db)
    # 目录路径构建
    folder_path=await folder_id_to_path(folder_id=folder_id,db=db)
    base_dir=Path(__file__).parent.parent
    save_dir=base_dir.joinpath(vector_dir,model_dir,f"{folder_id}")
    images_to_process=await _select_update_or_insert(save_dir=save_dir,images=image_collection,folder=folder_path)
    if not images_to_process:
        logger.info(f"No need to update and no need to insert")
        return
    image_collection_dateset = data_collection.VggDataset(image_collection=images_to_process, need_transform=True)
    # 获取target的张量
    # target_dataset=data_collection.VggDataset(image_collection=[target_image],need_transform=True)
    # target_date=target_dataset[0][1]
    # target_date=target_date.unsqueeze(dim=0)
    # 模型登录
    vgg16=feature_extract.load_vgg16()
    module=data_collection.FeatureStripping(base_model=vgg16)
    # 转化为测试模式
    module.eval()
    # 获取target的特征矩阵
    # with torch.no_grad():
    #     target_feature_vector=module(target_date)
    #     target_feature_vector=F.normalize(target_feature_vector,dim=1,p=2).squeeze(0)
    path_vector=list()
    image_collection_dataloader=data.DataLoader(
        dataset=image_collection_dateset,
        batch_size=16,
        num_workers=2,
    )
    for image_paths, images in image_collection_dataloader:
        images=images.to(device=device)
        module=module.to(device=device)
        with (torch.no_grad()):
            feature_vectors=module(images)
            for image_path,vector in zip(image_paths,feature_vectors):
                # similarity=vgg16_feature_extraction.cosine_similarity(target=target_feature_vector,feature=vector)
                path_vector.append((image_path,vector.cpu().numpy()))
    # path_similarity=sorted(path_similarity,key=lambda item:path_similarity[item],reverse=True)
    for item in path_vector:
        relative_path = os.path.relpath(item[0],folder_path)
        vector=item[1]
        # 修改npy命名方法，***.npy->***.jpg.npy
        # file_name=os.path.splitext(relative_path)[0]+".npy"
        file_name=relative_path+".npy"
        save_path=save_dir.joinpath(file_name)
        save_path.parent.mkdir(parents=True,exist_ok=True)
        np.save(file=save_path,arr=vector)
        images_feature.append(
            retrieve_model.ImageFeatures(
                model="vgg16",
                path=item[0],
                feature=str(save_path)
            )
        )
    # 保存feature数据
    await insert_dat_(dataset=images_feature,db=db)

async def batch_insert_feature(image_features:torch.Tensor,image_paths:List,folder_path:str,save_dir:Path):
    feature_collection=list()
    if image_features.dim()<2:
        logger.error(f"Incorrect feature data dimension!")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Incorrect feature data dimension!")
    # 判断特征向量长度和路径长度是否一致
    if image_features.size(0)!=len(image_paths):
        logger.error(f"The number of features doesn't equal the number of paths")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"The number of features doesn't equal the number of paths")
    for image_feature, image_path in zip(image_features, image_paths):
        # 分离计算图+cpu+numpy
        image_feature=image_feature.detach().cpu().numpy()
        relative_path = os.path.relpath(image_path, folder_path)
        relative_path = relative_path+".npy"
        save_path=save_dir.joinpath(relative_path)
        # 保证父目录存在
        save_path.parent.mkdir(parents=True,exist_ok=True)
        # 保存特征向量
        np.save(file=save_path,arr=image_feature)
        feature_collection.append(
            retrieve_model.ImageFeatures(
                model="openclip",
                path=image_path,
                feature=str(save_path)
            )
        )
    return feature_collection

async def _select_update_or_insert(save_dir:Path,images:List[str],folder:str)->List[str]:
    """目录不存在，表示数据从未插入过，直接全部插入
    Args:
        save_dir: 保存特征向量的目录
        images: 图片路径列表
        folder: 图片目录
    Returns:
        过滤之后的目录
    """
    # update or insert
    if not save_dir.exists():
        save_dir.mkdir(parents=True)
        images_to_process=images
    else:
        # 获取已经存在的图片
        existing_files = set()
        for file_npy in save_dir.rglob("*.npy"):
            # file_npy save dir/***/**.jpg.npy
            relative_name = file_npy.relative_to(save_dir) # relative_name: ***/**.jpg.npy
            relative_name = relative_name.with_suffix("") # relative_name: ***/**.jpg
            existing_files.add(str(relative_name)) # existing_files: [***/**.jpg,...]
        images_to_process = list()
        # 判断是否有需要更新的文件
        for image_path in images:
            # image_path: folder/***/**.jpg
            relative_path=os.path.relpath(image_path,folder) # relative_path: ***/**.jpg
            # relative_name=os.path.splitext(relative_path)[0]
            if relative_path not in existing_files:
                images_to_process.append(image_path)
    return images_to_process

# 使用clip获取特征向量
async def openclip_image_feature_vector(image_path:str,config_file:str,db:AsyncSession):
    config=inquiry.load_config(config_file=config_file)
    # 获取图片列表
    folder_id = await image_path_to_folder_id(image_path=image_path,db=db)
    folder_path=await folder_id_to_path(folder_id=folder_id,db=db)
    images = await fetch_image_collection(folder_id=folder_id,db=db)
    # 登录模型
    clip_model=openclip_feature_extraction.ClipModel(config=config)
    # 设备
    device=clip_model.device
    model,preprocess=clip_model.load_clip_model()
    model.eval()
    model=model.to(device=device)
    # 特征向量目录
    vector_dir_name=config["vector_dir"]
    vector_dir=Path(__file__).parent.parent.joinpath(vector_dir_name,"openclip",str(folder_id))
    # 获取需要获取特征向量的图片
    images=await _select_update_or_insert(
        save_dir=vector_dir,
        images=images,
        folder=folder_path,
    )
    # 返回images为空表示不需要任何的更新
    if not images:
        logger.info(f"No need to update and no need to insert")
        return
    # 获取dataset
    images_dataset = openclip_feature_extraction.ClipDataset(images=images,transform=preprocess)
    images_dataloader = data.DataLoader(dataset=images_dataset,batch_size=16,num_workers=2)
    with torch.no_grad(), torch.autocast(device_type=device.type):
        for images, image_paths in images_dataloader:
            images=images.to(device=device)
            image_features=model.encode_image(images)
            image_features=F.normalize(input=image_features,dim=-1,p=2)
            feature_collection=await batch_insert_feature(
                image_features=image_features,
                image_paths=image_paths,
                folder_path=folder_path,
                save_dir=vector_dir,
            )
            await insert_dat_(dataset=feature_collection,db=db)

async def feature_by_image_path_form_vgg16(image_path:str,config_file:str)->np.ndarray:
    """
    Args:
        image_path: 图片路径
        config_file: 配置文件
    Returns:
        numpy数组，一维
    """
    feature_extract = vgg16_feature_extraction.Vgg16FeatureExtractor(config_path=config_file)
    device = feature_extract.device
    vgg16=feature_extract.load_vgg16()
    module=data_collection.FeatureStripping(base_model=vgg16)
    module.eval()
    target_image_dateset=data_collection.VggDataset([image_path],need_transform=True)
    _,target_image=target_image_dateset[0]
    target_image=target_image.unsqueeze(0)
    with torch.no_grad():
        module=module.to(device=device)
        target_image=target_image.to(device=device)
        target_feature=module(target_image)
    target_feature=target_feature.squeeze(0).cpu().numpy()
    return target_feature

# 获取特征向量来根据openclip
async def feature_by_image_path_from_openclip(image_path:str,config)->np.ndarray:
    """
    Args:
        image_path: 图片路径
        config: 配置文件
    Returns:
        特征向量，numpy数组形式
    """
    # config=inquiry.load_config(config_file=config_file)
    clip_model=openclip_feature_extraction.ClipModel(config=config)
    # 获取设备
    device=clip_model.device
    model,preprocess=clip_model.load_clip_model()
    model.eval()
    # 将模型移动到设备上
    model=model.to(device=device)
    image=Image.open(image_path).convert("RGB")
    image=preprocess(image).unsqueeze(0)
    # 将数据移动到设备上
    image=image.to(device=device)
    with torch.no_grad(), torch.autocast(device_type=device.type):
        image_feature=model.encode_image(image)
        image_feature=F.normalize(input=image_feature,dim=-1,p=2)
    image_feature=image_feature.squeeze(dim=0).cpu().numpy()
    return image_feature

# 效率低的搜索方法
async def slow_search_images(target_image:str,image_path:str,config_file:str,db:AsyncSession,method:str):
    config=inquiry.load_config(config_file=config_file)
    vector_dir=config["vector_dir"]
    folder_id=await image_path_to_folder_id(image_path=image_path,db=db)
    base_dir=Path(__file__).parent.parent
    save_dir=base_dir.joinpath(vector_dir,method,f"{folder_id}")
    if method=="vgg16":
        target_feature=await feature_by_image_path_form_vgg16(image_path=target_image,config_file=config_file)
    elif method=="openclip":
        target_feature=await feature_by_image_path_from_openclip(image_path=target_image, config=config)
    else:
        logger.error(f"The functionality for this model has not yet been implemented.")
        raise Exception(f"The functionality for this model has not yet been implemented.") from None
    file_and_feature=list()
    for item in save_dir.rglob("*.npy"):
        file_and_feature.append(
            (
                item, # 特征向量路径
                np.load(file=item)
            )
        )
    file_and_similarity=list(
        map(
            lambda item: (item[0], vgg16_feature_extraction.array_cosine_similarity(target_feature, item[1])),
            file_and_feature,
        )
    )
    file_and_similarity_sort=sorted(file_and_similarity, key=lambda item: item[1], reverse=True)
    stmt=(select(
        retrieve_model.ImageFeatures.feature,
        retrieve_model.Images.path,
        retrieve_model.Images.thumbnail_path,
        retrieve_model.Images.name,
        retrieve_model.Images.extension, # 扩展名
    ).join(
        retrieve_model.ImageFeatures,
        retrieve_model.Images.path == retrieve_model.ImageFeatures.path,
    ).where(
        retrieve_model.ImageFeatures.feature.in_(
            list(
                map(lambda item: str(item[0]),file_and_similarity_sort),
            )
        )
    ))
    result=await db.execute(stmt)
    paths=result.all()
    path_map = {
        feature: (image_path, thumbnail_path, name, extension)
        for feature, image_path, thumbnail_path, name, extension in paths
    }
    result=list()
    for feature_file, similarity in file_and_similarity_sort:
        image_path, thumbnail_path, name, extension = path_map.get(str(feature_file), (None, None,None, None))
        if image_path is None:
            continue
        result.append(
            {
                "feature":str(feature_file),
                "thumbnail":thumbnail_path,
                "image":image_path,
                "name":name,
                "extension":extension,
                "similarity":similarity,
            }
        )
    return result

# FAISS快速查找
async def swift_search_images(target_image:str,image_path:str,config_file:str,db:AsyncSession,method:str,top:int):
    config=inquiry.load_config(config_file=config_file)
    vector_dir=config["vector_dir"]
    folder_id = await image_path_to_folder_id(image_path=image_path,db=db)
    # folder = await folder_id_to_path(folder_id=folder_id,db=db)
    root_dir=Path(__file__).parent.parent
    save_dir=root_dir.joinpath(vector_dir,method,f"{folder_id}")
    if method=="vgg16":
        target_feature=await feature_by_image_path_form_vgg16(image_path=target_image,config_file=config_file)
    elif method=="openclip":
        target_feature=await feature_by_image_path_from_openclip(image_path=target_image,config=config)
    else:
        logger.error(f"The functionality for this model has not yet been implemented.")
        raise Exception(f"The functionality for this model has not yet been implemented.") from None
    # (512,)->(1,512)
    target_feature=np.expand_dims(target_feature,axis=0)
    paths_features=list()
    for item in save_dir.rglob("*.npy"):
        paths_features.append(
            (
                item,
                np.load(file=item)
            )
        )
    paths,features=map(list, zip(*paths_features)) if paths_features else ([],[])
    features=np.stack(features,axis=0)
    dimension=features.shape[-1]
    vector_database=faiss.IndexFlatIP(dimension)
    vector_database.add(features)
    logger.info(f"The number of eigenvectors is {vector_database.ntotal}!")
    similarity, indices = vector_database.search(target_feature, k=top)
    paths=[paths[index] for index in indices[0]]
    # 获取对应方相似度
    similarity=similarity[0]
    # 路径和相似度配对成字典（特征向量路径：相似度）
    paths_similarity=list(zip(paths,similarity))
    # 根据相似度排序(faiss已排序)
    # paths_similarity=sorted(paths_similarity,key=lambda item: item[1], reverse=True)
    stmt=select(
        retrieve_model.ImageFeatures.feature,
        retrieve_model.Images.path,
        retrieve_model.Images.thumbnail_path,
        retrieve_model.Images.name,
        retrieve_model.Images.extension,
    ).join(
        retrieve_model.ImageFeatures,
        retrieve_model.Images.path == retrieve_model.ImageFeatures.path,
    ).where(
        retrieve_model.ImageFeatures.feature.in_(
            list(
                map(lambda item: str(item[0]),paths_similarity)
            )
        )
    )
    result=await db.execute(statement=stmt)
    images_information=result.all()
    path_map=defaultdict()
    for feature, path, thumbnail, name, extension in images_information:
        path_map[feature]=(
            path,thumbnail,name,extension
        )
    result=list()
    for path, similarity in paths_similarity:
        image_path,thumbnail,name,extension = path_map.get(str(path),(None,None,None,None))
        result.append(
            {
                "feature": str(path),
                "thumbnail": thumbnail,
                "image": image_path,
                "name": name,
                "extension": extension,
                "similarity": float(similarity),
            }
        )
    return result

# 获取模型
async def fetch_models(db:AsyncSession):
    stmt=select(
        retrieve_model.Models.model
    )
    result=await db.execute(statement=stmt)
    models=result.scalars().all()
    return models