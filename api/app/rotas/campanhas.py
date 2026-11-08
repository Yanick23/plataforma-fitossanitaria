"""Campanhas de vigilância activa, novidades para a app (notificações) e calendário agrícola."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import obter_sessao
from ..esquemas import Calendario, CampanhaAgricultorLer, CampanhaCriar, CampanhaLer, Novidades
from ..seguranca import Leitor, Pessoal, UtilizadorActual
from ..servicos import calendario as servico_calendario, campanhas as servico, novidades as servico_novidades, sms
from ..tabelas import Distrito

router = APIRouter(tags=["Campanhas, novidades e calendário"])
Sessao = Annotated[AsyncSession, Depends(obter_sessao)]


@router.post("/campanhas", response_model=CampanhaLer, status_code=status.HTTP_201_CREATED)
async def criar(dados: CampanhaCriar, utilizador: Pessoal, sessao: Sessao, tarefas: BackgroundTasks) -> CampanhaLer:
    """O técnico pede aos agricultores da sua zona que fotografem uma cultura durante alguns dias."""
    c = await servico.criar(sessao, utilizador, dados)
    if dados.enviar_sms:
        tarefas.add_task(sms.enviar_em_segundo_plano, campanha_id=c.id)
    return await servico.para_ler(sessao, await servico.obter(sessao, c.id))


@router.get("/campanhas", response_model=list[CampanhaLer])
async def listar(utilizador: Leitor, sessao: Sessao, antigas: bool = False) -> list[CampanhaLer]:
    """Campanhas da zona com o progresso (agricultores, quantos responderam, casos encontrados)."""
    return await servico.listar(sessao, utilizador, antigas)


@router.get("/campanhas/minhas", response_model=list[CampanhaAgricultorLer])
async def minhas(utilizador: UtilizadorActual, sessao: Sessao) -> list[CampanhaAgricultorLer]:
    """Campanhas a decorrer na zona do agricultor (a app mostra-as no ecrã inicial)."""
    return await servico.minhas(sessao, utilizador)


@router.post("/campanhas/{campanha_id}/cancelar", status_code=status.HTTP_204_NO_CONTENT)
async def cancelar(campanha_id: int, utilizador: Pessoal, sessao: Sessao) -> None:
    await servico.cancelar(sessao, utilizador, campanha_id)


@router.get("/novidades", response_model=Novidades)
async def novidades(utilizador: UtilizadorActual, sessao: Sessao, desde: datetime | None = None) -> Novidades:
    """O que mudou para o agricultor desde `desde`; a app consulta-o em segundo plano e notifica."""
    return await servico_novidades.novidades(sessao, utilizador, desde)


@router.get("/calendario", response_model=Calendario)
async def calendario(utilizador: UtilizadorActual, sessao: Sessao, provincia: str | None = None) -> Calendario:
    """Calendário agrícola de uma província: actividades, época de sementeira e avisos de cada mês.
    Sem `provincia`, usa a província da conta."""
    codigo = provincia or utilizador.provincia_codigo
    if codigo is None and utilizador.distrito_id:
        codigo = (await sessao.get(Distrito, utilizador.distrito_id)).provincia_codigo
    if codigo is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Indique a província")
    return await servico_calendario.calendario(sessao, codigo)
