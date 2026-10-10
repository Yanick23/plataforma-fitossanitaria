"""Ponto de entrada da API.

Arranque (a partir da pasta api/):
    uvicorn app.main:app --host 0.0.0.0 --port 8000

Documentação automática: /docs (Swagger UI) e /redoc (ReDoc).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import Base, SessaoLocal, motor
from .rotas import auth, catalogo, diagnosticos, modelos
from .seed import semear


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    # Cria as tabelas que faltarem e insere os dados iniciais.
    async with motor.begin() as ligacao:
        await ligacao.run_sync(Base.metadata.create_all)
    async with SessaoLocal() as sessao:
        await semear(sessao)
    yield
    await motor.dispose()


app = FastAPI(
    title="AgroDiagnóstico API",
    version="1.0.0",
    description=(
        "API da plataforma de diagnóstico de doenças e pragas em milho e mandioca. "
        "Recebe os diagnósticos feitos offline na app, gere o catálogo de patologias, "
        "distribui novas versões do modelo e gera mapas Grad-CAM. "
        "Autenticação: POST /auth/login e depois o botão **Authorize** com o token."
    ),
    lifespan=ciclo_de_vida,
)

app.include_router(auth.router)
app.include_router(diagnosticos.router)
app.include_router(catalogo.router)
app.include_router(modelos.router)


@app.get("/saude", tags=["Sistema"])
async def saude() -> dict:
    return {"estado": "ok"}
