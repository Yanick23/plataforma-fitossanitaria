"""Alertas por zona: o pessoal envia, os agricultores recebem na sincronização."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import obter_sessao
from ..esquemas import AlcanceAlerta, AlertaAgricultorLer, AlertaCriar, AlertaLer
from ..seguranca import Pessoal, UtilizadorActual
from ..servicos import alertas as servico
from ..tabelas import Alerta

router = APIRouter(tags=["Alertas"])
Sessao = Annotated[AsyncSession, Depends(obter_sessao)]


@router.get("/alertas/alcance", response_model=AlcanceAlerta)
async def alcance(utilizador: Pessoal, sessao: Sessao, provincia: str | None = None,
                  distrito_id: int | None = None) -> AlcanceAlerta:
    """Quantos agricultores recebem um alerta para esta zona (antes de o enviar)."""
    provincia, distrito_id = await servico.validar_destino(sessao, utilizador, provincia, distrito_id)
    zona, n = await servico.alcance(sessao, provincia, distrito_id)
    return AlcanceAlerta(zona=zona, destinatarios=n)


@router.post("/alertas", response_model=AlertaLer, status_code=status.HTTP_201_CREATED)
async def criar(dados: AlertaCriar, utilizador: Pessoal, sessao: Sessao) -> AlertaLer:
    """Técnico: só para a sua zona. Administrador: distrito, província ou país (sem zona = país todo)."""
    alerta = await servico.criar(sessao, utilizador, dados)
    alerta = await sessao.scalar(select(Alerta).where(Alerta.id == alerta.id)
                                 .options(selectinload(Alerta.autor), selectinload(Alerta.patologia)))
    return (await servico.para_ler(sessao, [alerta]))[0]


@router.get("/alertas", response_model=list[AlertaLer])
async def listar(utilizador: Pessoal, sessao: Sessao, arquivados: bool = False) -> list[AlertaLer]:
    return await servico.listar_pessoal(sessao, utilizador, arquivados)


@router.post("/alertas/{alerta_id}/arquivar", status_code=status.HTTP_204_NO_CONTENT)
async def arquivar(alerta_id: int, utilizador: Pessoal, sessao: Sessao) -> None:
    await servico.arquivar(sessao, utilizador, alerta_id)


@router.get("/alertas/meus", response_model=list[AlertaAgricultorLer])
async def meus(utilizador: UtilizadorActual, sessao: Sessao) -> list[AlertaAgricultorLer]:
    """Alertas activos para o distrito/província do agricultor e os nacionais (a app pede-os na sincronização)."""
    return await servico.meus(sessao, utilizador)


@router.post("/alertas/{alerta_id}/lido", status_code=status.HTTP_204_NO_CONTENT)
async def marcar_lido(alerta_id: int, utilizador: UtilizadorActual, sessao: Sessao) -> None:
    await servico.marcar_lido(sessao, utilizador, alerta_id)
