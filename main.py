from contextlib import asynccontextmanager
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

from acesso_dados.database import create_db

from apresentacao import (
    paginas_router,
    auth_router,
    noticias_router,
    videos_router,
    times_router,
    campeonatos_router,
    simulador_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    yield

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.exception_handler(Exception)
async def validation_exception_handler(request: Request, exc: Exception):
    return PlainTextResponse(str(traceback.format_exc()), status_code=500)

app.include_router(paginas_router.router)
app.include_router(auth_router.router)
app.include_router(noticias_router.router)
app.include_router(videos_router.router)
app.include_router(times_router.router)
app.include_router(campeonatos_router.router)
app.include_router(simulador_router.router)
