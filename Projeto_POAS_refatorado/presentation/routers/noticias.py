from fastapi import APIRouter
from fastapi.responses import JSONResponse

from application import noticias_service

router = APIRouter()


@router.get("/api/noticias")
def obter_noticias():
    resultado = noticias_service.obter_noticias_gerais()
    if isinstance(resultado, dict) and "erro" in resultado:
        return JSONResponse(status_code=500, content=resultado)
    return resultado


@router.get("/api/basquete")
def basquete():
    return noticias_service.obter_noticias_por_esporte("basquete")


@router.get("/api/ufc")
def ufc():
    return noticias_service.obter_noticias_por_esporte("ufc")


@router.get("/api/futebol-americano")
def futebol_americano():
    return noticias_service.obter_noticias_por_esporte("futebol_americano")


@router.get("/api/formula1")
def formula1():
    return noticias_service.obter_noticias_por_esporte("formula1")


@router.get("/api/buscar-noticias")
def buscar_noticias(q: str):
    try:
        return noticias_service.buscar_noticias_por_termo(q)
    except RuntimeError as erro:
        return JSONResponse(
            status_code=500,
            content={"erro": "Falha ao buscar notícias", "detalhes": str(erro)},
        )
