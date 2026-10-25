"""Culturas e patologias (RF11). Leitura para todos; escrita só para o administrador (com auditoria)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import obter_sessao
from ..esquemas import (CulturaCriar, CulturaEscrever, CulturaLer, PatologiaCriar, PatologiaEscrever,
                        PatologiaLer)
from ..seguranca import Administrador
from ..servicos.auditoria import auditar, instantaneo
from ..tabelas import Cultura, Patologia

router = APIRouter(tags=["Catálogo"])
Sessao = Annotated[AsyncSession, Depends(obter_sessao)]

CAMPOS_PATOLOGIA = ("cultura_id", "codigo", "nome_local", "nome_cientifico", "tipo", "recomendacao")


@router.get("/culturas", response_model=list[CulturaLer])
async def listar_culturas(sessao: Sessao) -> list[Cultura]:
    return list(await sessao.scalars(select(Cultura).order_by(Cultura.id)))


@router.post("/culturas", response_model=CulturaLer, status_code=status.HTTP_201_CREATED)
async def criar_cultura(dados: CulturaCriar, admin: Administrador, sessao: Sessao) -> Cultura:
    if await sessao.get(Cultura, dados.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Cultura já existe")
    cultura = Cultura(**dados.model_dump())
    sessao.add(cultura)
    auditar(sessao, admin, "cultura.criar", "cultura", cultura.id, depois=dados.model_dump())
    await sessao.commit()
    return cultura


@router.put("/culturas/{cultura_id}", response_model=CulturaLer)
async def actualizar_cultura(cultura_id: str, dados: CulturaEscrever, admin: Administrador,
                             sessao: Sessao) -> Cultura:
    cultura = await sessao.get(Cultura, cultura_id)
    if cultura is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cultura não encontrada")
    antes = instantaneo(cultura, ("nome", "nome_cientifico"))
    for campo, valor in dados.model_dump().items():
        setattr(cultura, campo, valor)
    auditar(sessao, admin, "cultura.actualizar", "cultura", cultura.id, antes=antes, depois=dados.model_dump())
    await sessao.commit()
    return cultura


@router.get("/patologias", response_model=list[PatologiaLer])
async def listar_patologias(sessao: Sessao, cultura: str | None = None) -> list[Patologia]:
    consulta = select(Patologia).order_by(Patologia.cultura_id, Patologia.codigo)
    if cultura:
        consulta = consulta.where(Patologia.cultura_id == cultura)
    return list(await sessao.scalars(consulta))


@router.post("/patologias", response_model=PatologiaLer, status_code=status.HTTP_201_CREATED)
async def criar_patologia(dados: PatologiaCriar, admin: Administrador, sessao: Sessao) -> Patologia:
    if await sessao.get(Cultura, dados.cultura_id) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Cultura inexistente")
    patologia = Patologia(**dados.model_dump())
    sessao.add(patologia)
    try:
        await sessao.flush()
    except IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe essa patologia nesta cultura") from None
    auditar(sessao, admin, "patologia.criar", "patologia", patologia.id,
            depois=instantaneo(patologia, CAMPOS_PATOLOGIA))
    await sessao.commit()
    return patologia


@router.put("/patologias/{patologia_id}", response_model=PatologiaLer)
async def actualizar_patologia(patologia_id: int, dados: PatologiaEscrever, admin: Administrador,
                               sessao: Sessao) -> Patologia:
    patologia = await sessao.get(Patologia, patologia_id)
    if patologia is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patologia não encontrada")
    antes = instantaneo(patologia, CAMPOS_PATOLOGIA)
    for campo, valor in dados.model_dump().items():
        setattr(patologia, campo, valor)
    auditar(sessao, admin, "patologia.actualizar", "patologia", patologia.id, antes=antes,
            depois=instantaneo(patologia, CAMPOS_PATOLOGIA))
    await sessao.commit()
    return patologia


@router.delete("/patologias/{patologia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def apagar_patologia(patologia_id: int, admin: Administrador, sessao: Sessao) -> None:
    patologia = await sessao.get(Patologia, patologia_id)
    if patologia is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patologia não encontrada")
    auditar(sessao, admin, "patologia.apagar", "patologia", patologia.id,
            antes=instantaneo(patologia, CAMPOS_PATOLOGIA))
    await sessao.delete(patologia)
    await sessao.commit()
