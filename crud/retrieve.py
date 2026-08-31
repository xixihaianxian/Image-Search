from PIL import Image
from crud import inquiry
from pathlib import Path
from schema import retrieve
from urllib.parse import quote
from typing import List,Optional
from loguru import logger
from fastapi import UploadFile,File
import io

async def fetch_image_from_folder(folder:str,config_path:Optional[str])->List[retrieve.ImageInfo]:
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
            image_info=retrieve.ImageInfo(name=name,image_url=image_url)
            images.append(image_info)
    return images

async def loading_image(config_path:str,folder:str,images:List[UploadFile]=File(...))->List[retrieve.ImageInfo]:
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
                retrieve.ImageInfo(
                    name=image.filename,
                    image_url=f"/{gallery_dir}/{folder}/{dest.name}",
                    thumbnail=f"/{gallery_dir}/{folder}/{thumbnail_path.name}",
                )
            )
        except Exception as error:
            # 单张图片处理失败不影响整批上传
            logger.error(f"Failed to load image {image.filename}: {error}")
    return upload_images