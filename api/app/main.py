"""Ponto de entrada da API.

Arranque (a partir da pasta api/):
    uvicorn app.main:app --host 0.0.0.0 --port 8000

Documentação automática: /docs (Swagger UI) e /redoc (ReDoc).

Organização em camadas:
    rotas/        HTTP: validação dos pedidos, permissões e respostas
    servicos/     regras de negócio (zonas, alertas, vigilância, validação, auditoria)
    repositorios/ consultas à base de dados
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import definicoes
from .database import SessaoLocal, migrar, motor
from .rotas import (alertas, auth, catalogo, diagnosticos, gestao, modelos, regioes, validacoes, vigilancia,
                    visitas)
from .seed import semear


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    # Aplica as migrações da base de dados e insere os dados iniciais.
    async with motor.begin() as ligacao:
        await ligacao.run_sync(migrar)
    async with SessaoLocal() as sessao:
        await semear(sessao)
    yield
    await motor.dispose()


app = FastAPI(
    title="API de diagnóstico de culturas",
    version="2.0.0",
    description=(
        "API da plataforma de vigilância fitossanitária do milho e da mandioca em Moçambique. "
        "Recebe os diagnósticos feitos offline na app, gere o catálogo, as zonas (províncias e "
        "distritos), os alertas, a validação pelos técnicos, os pedidos de visita e as versões do "
        "modelo. Autenticação: POST /auth/login e depois o botão **Authorize** com o token."
    ),
    lifespan=ciclo_de_vida,
)

# O painel web (admin/) corre noutra origem: tem de ser autorizado aqui.
app.add_middleware(
    CORSMiddleware,
    allow_origins=definicoes.cors_origens,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

for modulo in (auth, diagnosticos, catalogo, modelos, regioes, gestao, alertas, validacoes, visitas, vigilancia):
    app.include_router(modulo.router)


@app.get("/saude", tags=["Sistema"])
async def saude() -> dict:
    return {"estado": "ok"}
