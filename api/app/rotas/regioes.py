"""Províncias e distritos de Moçambique (públicos: a app usa-os no registo)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import obter_sessao
from ..esquemas import DistritoLer, ProvinciaLer
from ..tabelas import Distrito, Provincia

router = APIRouter(tags=["Regiões"])
Sessao = Annotated[AsyncSession, Depends(obter_sessao)]


@router.get("/provincias", response_model=list[ProvinciaLer])
async def listar_provincias(sessao: Sessao) -> list[Provincia]:
    return list(await sessao.scalars(select(Provincia).order_by(Provincia.nome)))


@router.get("/distritos", response_model=list[DistritoLer])
async def listar_distritos(sessao: Sessao, provincia: str | None = None) -> list[Distrito]:
    consulta = select(Distrito).order_by(Distrito.provincia_codigo, Distrito.nome)
    if provincia:
        consulta = consulta.where(Distrito.provincia_codigo == provincia)
    return list(await sessao.scalars(consulta))
