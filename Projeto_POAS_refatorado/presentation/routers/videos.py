from fastapi import APIRouter
from fastapi.responses import JSONResponse

from application import videos_service

router = APIRouter()


@router.get("/api/videos/{esporte}")
def videos(esporte: str):
    return videos_service.buscar_videos_por_esporte(esporte)


@router.get("/api/buscar-videos")
def buscar_videos(q: str):
    try:
        return videos_service.buscar_videos_por_termo(q)
    except RuntimeError as erro:
        return JSONResponse(
            status_code=500,
            content={"erro": "Falha ao buscar vídeos", "detalhes": str(erro)},
        )
