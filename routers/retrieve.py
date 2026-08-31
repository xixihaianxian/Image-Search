from fastapi import APIRouter,UploadFile,File
from schema import retrieve as schema_retrieve, response as schema_response
from fastapi.responses import FileResponse
from pathlib import Path
from crud import retrieve as crud_retrieve
from typing import List

router = APIRouter(prefix="/retrieve",tags=["retrieve"])

@router.get("/get/localImage")
async def get_local_images(image:str):
    image_path = Path(image)
    return FileResponse(path=image_path)

# 直接映射（导致内存压力）
@router.post("/log/local/gallery")
async def log_gallery(folder:schema_retrieve.LocalDir):
    folder=folder.folder
    config_path=Path(__file__).parent.parent.joinpath("config","config.yml")
    images=await crud_retrieve.fetch_image_from_folder(folder=folder,config_path=config_path)
    images=list(map(lambda item: item.model_dump(by_alias=True), images))
    return schema_response.success_response(
        message="success",
        data=images
    )

# 纯后端加载
@router.post("/upload/gallery")
async def upload_gallery(images:List[UploadFile]=File(...)):
    config_path = Path(__file__).parent.parent.joinpath("config", "config.yml")
    response=await crud_retrieve.loading_image(images=images,config_path=str(config_path))
    return schema_response.success_response(
        message="success",
        data=[item.model_dump(by_alias=True) for item in response]
    )

# 后端加载缩略图，不需要对原图进行迁移
@router.post("./upload/local/gallery")
async def upload_local_gallery(folder:schema_retrieve.LocalDir):
    folder=folder.folder
    pass