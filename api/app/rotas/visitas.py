"""Pedidos de visita técnica."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import obter_sessao
from ..esquemas import VisitaActualizar, VisitaCriar, VisitaLer
from ..seguranca import Pessoal, UtilizadorActual
from ..servicos import visitas as servico
from ..tabelas import EstadoVisita

router = APIRouter(tags=["Visitas"])
Sessao = Annotated[AsyncSession, Depends(obter_sessao)]


@router.post("/visitas", response_model=VisitaLer, status_code=status.HTTP_201_CREATED)
async def pedir(dados: VisitaCriar, utilizador: UtilizadorActual, sessao: Sessao) -> VisitaLer:
    """O agricultor pede ajuda a partir de um diagnóstico já sincronizado."""
    v = await servico.pedir(sessao, utilizador, dados)
    return (await servico.para_ler(sessao, [await servico.obter(sessao, v.id)]))[0]


@router.get("/visitas/minhas", response_model=list[VisitaLer])
async def minhas(utilizador: UtilizadorActual, sessao: Sessao) -> list[VisitaLer]:
    return await servico.para_ler(sessao, await servico.listar_do_agricultor(sessao, utilizador))


@router.post("/visitas/{visita_id}/cancelar", status_code=status.HTTP_204_NO_CONTENT)
async def cancelar(visita_id: int, utilizador: UtilizadorActual, sessao: Sessao) -> None:
    await servico.cancelar_pelo_agricultor(sessao, utilizador, visita_id)


@router.get("/visitas", response_model=list[VisitaLer])
async def listar(utilizador: Pessoal, sessao: Sessao, estado: EstadoVisita | None = None) -> list[VisitaLer]:
    """Pedidos da zona do técnico (o administrador vê todos)."""
    return await servico.para_ler(sessao, await servico.listar_pessoal(sessao, utilizador, estado))


@router.patch("/visitas/{visita_id}", response_model=VisitaLer)
async def actualizar(visita_id: int, dados: VisitaActualizar, utilizador: Pessoal, sessao: Sessao) -> VisitaLer:
    """Agendar (com data), resolver ou cancelar, e escrever notas."""
    await servico.actualizar(sessao, utilizador, visita_id, dados)
    sessao.expire_all()
    return (await servico.para_ler(sessao, [await servico.obter(sessao, visita_id)]))[0]
