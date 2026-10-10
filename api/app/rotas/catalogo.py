"""Culturas e patologias (RF11). Leitura para todos; escrita só para o administrador."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import obter_sessao
from ..esquemas import (CulturaCriar, CulturaEscrever, CulturaLer, PatologiaCriar, PatologiaEscrever,
                        PatologiaLer)
from ..seguranca import Administrador
from ..tabelas import Cultura, Patologia

router = APIRouter(tags=["Catálogo"])
Sessao = Annotated[AsyncSession, Depends(obter_sessao)]


@router.get("/culturas", response_model=list[CulturaLer])
async def listar_culturas(sessao: Sessao) -> list[Cultura]:
    return list(await sessao.scalars(select(Cultura).order_by(Cultura.id)))


@router.post("/culturas", response_model=CulturaLer, status_code=status.HTTP_201_CREATED)
async def criar_cultura(dados: CulturaCriar, _: Administrador, sessao: Sessao) -> Cultura:
    if await sessao.get(Cultura, dados.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Cultura já existe")
    cultura = Cultura(**dados.model_dump())
    sessao.add(cultura)
    await sessao.commit()
    return cultura


@router.put("/culturas/{cultura_id}", response_model=CulturaLer)
async def actualizar_cultura(cultura_id: str, dados: CulturaEscrever, _: Administrador,
                             sessao: Sessao) -> Cultura:
    cultura = await sessao.get(Cultura, cultura_id)
    if cultura is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cultura não encontrada")
    for campo, valor in dados.model_dump().items():
        setattr(cultura, campo, valor)
    await sessao.commit()
    return cultura


@router.get("/patologias", response_model=list[PatologiaLer])
async def listar_patologias(sessao: Sessao, cultura: str | None = None) -> list[Patologia]:
    consulta = select(Patologia).order_by(Patologia.cultura_id, Patologia.codigo)
    if cultura:
        consulta = consulta.where(Patologia.cultura_id == cultura)
    return list(await sessao.scalars(consulta))


@router.post("/patologias", response_model=PatologiaLer, status_code=status.HTTP_201_CREATED)
async def criar_patologia(dados: PatologiaCriar, _: Administrador, sessao: Sessao) -> Patologia:
    if await sessao.get(Cultura, dados.cultura_id) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Cultura inexistente")
    patologia = Patologia(**dados.model_dump())
    sessao.add(patologia)
    try:
        await sessao.commit()
    except IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe essa patologia nesta cultura") from None
    return patologia


@router.put("/patologias/{patologia_id}", response_model=PatologiaLer)
async def actualizar_patologia(patologia_id: int, dados: PatologiaEscrever, _: Administrador,
                               sessao: Sessao) -> Patologia:
    patologia = await sessao.get(Patologia, patologia_id)
    if patologia is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patologia não encontrada")
    for campo, valor in dados.model_dump().items():
        setattr(patologia, campo, valor)
    await sessao.commit()
    return patologia


@router.delete("/patologias/{patologia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def apagar_patologia(patologia_id: int, _: Administrador, sessao: Sessao) -> None:
    patologia = await sessao.get(Patologia, patologia_id)
    if patologia is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patologia não encontrada")
    await sessao.delete(patologia)
    await sessao.commit()
