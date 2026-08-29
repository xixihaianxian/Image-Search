from fastapi import APIRouter
from shcema import retrieve
from fastapi.responses import HTMLResponse,FileResponse
from crud import inquiry
from pathlib import Path

router = APIRouter(prefix="/retrieve",tags=["retrieve"])

@router.get("/get/localImages")
async def get_local_images(dir_info:retrieve.LogLocal):
    file_path = Path(dir_info.dir_path)
    return FileResponse(path=file_path)

@router.post("/log/local/gallery")
async def loa_gallery(dir_info:retrieve.LogLocal):
    pass