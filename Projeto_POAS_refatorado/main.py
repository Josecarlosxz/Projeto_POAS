import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

from infrastructure.database import create_db
from presentation.routers import auth, campeonatos, noticias, pages, simulador, times, videos


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    yield


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.exception_handler(Exception)
async def validation_exception_handler(request: Request, exc: Exception):
    return PlainTextResponse(str(traceback.format_exc()), status_code=500)


app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(noticias.router)
app.include_router(videos.router)
app.include_router(times.router)
app.include_router(simulador.router)
app.include_router(campeonatos.router)
