from fastapi import APIRouter

from negocio.noticias_service import (
    obter_noticias as _obter_noticias,
    basquete as _basquete,
    ufc as _ufc,
    futebol_americano as _futebol_americano,
    formula1 as _formula1,
    buscar_noticias as _buscar_noticias,
)

router = APIRouter()

# --- API NOTÍCIAS ---

@router.get("/api/noticias")
def obter_noticias():
    return _obter_noticias()

@router.get("/api/basquete")
def basquete():
    return _basquete()

@router.get("/api/ufc")
def ufc():
    return _ufc()

@router.get("/api/futebol-americano")
def futebol_americano():
    return _futebol_americano()

@router.get("/api/formula1")
def formula1():
    return _formula1()

# --- API BARRA DE BUSCA ---
@router.get("/api/buscar-noticias")
def buscar_noticias(q: str):
    return _buscar_noticias(q)
