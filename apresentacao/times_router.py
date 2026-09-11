from fastapi import APIRouter

from negocio.times_service import buscar_times as _buscar_times

router = APIRouter()

# --- API TIMES ---

@router.get("/api/times/{nome}")
def buscar_times(nome: str):
    return _buscar_times(nome)
