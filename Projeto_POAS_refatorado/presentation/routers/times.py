from fastapi import APIRouter

from application import times_service

router = APIRouter()


@router.get("/api/times/{nome}")
def buscar_times(nome: str):
    return times_service.buscar_time(nome)
