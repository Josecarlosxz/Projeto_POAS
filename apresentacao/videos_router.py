from fastapi import APIRouter

from negocio.videos_service import videos as _videos, buscar_videos as _buscar_videos

router = APIRouter()

@router.get("/api/videos/{esporte}")
def videos(esporte: str):
    return _videos(esporte)

@router.get("/api/buscar-videos")
def buscar_videos(q: str):
    return _buscar_videos(q)
