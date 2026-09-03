from PIL import Image
from crud import inquiry
from pathlib import Path
from schema import retrieve as retrieve_schema
from urllib.parse import quote
from typing import List,Optional,Tuple,Dict
from loguru import logger
from fastapi import UploadFile,File,status,HTTPException
from model import retrieve as retrieve_model
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import os
from uuid import uuid4

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

async def generate_thumbnail_image(file_path: str,thumbnail_path: str,thumbnail_config: Dict):
    """生成缩略图并保存
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