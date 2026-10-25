"""Vigilância fitossanitária: mapa de ocorrências e sinais de surto."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import obter_sessao
from ..esquemas import Declaracao, Ocorrencia, Surto
from ..repositorios.diagnosticos import FiltrosDiagnostico
from ..seguranca import Pessoal
from ..servicos import relatorios, vigilancia as servico
from ..tabelas import TipoPatologia

router = APIRouter(prefix="/vigilancia", tags=["Vigilância"])
Sessao = Annotated[AsyncSession, Depends(obter_sessao)]


@router.get("/ocorrencias", response_model=list[Ocorrencia])
async def ocorrencias(utilizador: Pessoal, sessao: Sessao, cultura: str | None = None, classe: str | None = None,
                      tipo: TipoPatologia | None = None, desde: datetime | None = None,
                      ate: datetime | None = None) -> list[Ocorrencia]:
    """Diagnósticos por distrito com os filtros escolhidos (alimenta o mapa)."""
    return await servico.ocorrencias(sessao, utilizador, FiltrosDiagnostico(
        cultura=cultura, classe=classe, tipo=tipo, desde=desde, ate=ate))


@router.get("/surtos", response_model=list[Surto])
async def surtos(utilizador: Pessoal, sessao: Sessao,
                 janela_dias: Annotated[int, Query(ge=1, le=60)] = 7,
                 semanas_base: Annotated[int, Query(ge=1, le=26)] = 4,
                 min_casos: Annotated[int, Query(ge=1, le=100)] = 3,
                 factor: Annotated[float, Query(ge=1, le=20)] = 2.0) -> list[Surto]:
    """Subidas anormais de uma praga/doença num distrito (sinal para o técnico decidir se envia alerta)."""
    return await servico.surtos(sessao, utilizador, janela_dias, semanas_base, min_casos, factor)


@router.get("/declaracoes", response_model=list[Declaracao])
async def declaracoes(utilizador: Pessoal, sessao: Sessao, desde: datetime | None = None) -> list[Declaracao]:
    """Casos de pragas/doenças de declaração obrigatória na zona: confirmados pelo técnico ou suspeitos."""
    return await relatorios.declaracoes(sessao, utilizador, desde)
