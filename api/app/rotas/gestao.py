"""Gestão (painel web): resumo, diagnósticos, utilizadores e auditoria."""

from datetime import date, datetime, time, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import obter_sessao
from ..esquemas import (AuditoriaLer, Boletim, EficaciaPatologia, NovaPalavraPasse, PaginaAuditoria, PaginaDiagnosticos, PaginaUtilizadores,
                        Resumo, UtilizadorActualizar, UtilizadorAdminLer)
from ..regioes import zona_de
from ..repositorios import diagnosticos as repo
from ..repositorios.diagnosticos import EstadoValidacao, FiltrosDiagnostico
from ..seguranca import Administrador, Pessoal
from ..servicos import painel, relatorios, utilizadores
from ..servicos.diagnosticos import mapa_patologias, para_admin
from ..tabelas import Diagnostico, Perfil, RegistoAuditoria, TipoPatologia

router = APIRouter(prefix="/gestao", tags=["Gestão"])
Sessao = Annotated[AsyncSession, Depends(obter_sessao)]
Limite = Annotated[int, Query(ge=1, le=200)]
Deslocamento = Annotated[int, Query(ge=0)]


@router.get("/resumo", response_model=Resumo)
async def resumo(utilizador: Pessoal, sessao: Sessao, dias: Annotated[int, Query(ge=7, le=365)] = 30) -> Resumo:
    """Indicadores da zona de quem pede (o administrador vê o país todo)."""
    return await painel.resumo(sessao, utilizador, dias)


@router.get("/diagnosticos", response_model=PaginaDiagnosticos)
async def diagnosticos(utilizador: Pessoal, sessao: Sessao, cultura: str | None = None, classe: str | None = None,
                       tipo: TipoPatologia | None = None, provincia: str | None = None,
                       distrito_id: int | None = None, desde: datetime | None = None, ate: datetime | None = None,
                       confianca_max: Annotated[float | None, Query(ge=0, le=1)] = None,
                       validacao: EstadoValidacao | None = None, utilizador_id: int | None = None,
                       ordem: Annotated[str, Query(pattern="^(recentes|confianca)$")] = "recentes",
                       limite: Limite = 50, deslocamento: Deslocamento = 0) -> PaginaDiagnosticos:
    """Diagnósticos da zona, com filtros. ordem=confianca põe primeiro os menos certos (fila de validação)."""
    f = FiltrosDiagnostico(cultura=cultura, classe=classe, tipo=tipo, provincia=provincia, distrito_id=distrito_id,
                           desde=desde, ate=ate, confianca_max=confianca_max, validacao=validacao,
                           utilizador_id=utilizador_id)
    consulta = repo.com_filtros(repo.na_zona(repo.consulta_base(), zona_de(utilizador)), f)
    total = await sessao.scalar(repo.total(consulta)) or 0
    ordenacao = (Diagnostico.confianca.asc(), Diagnostico.data.desc()) if ordem == "confianca" \
        else (Diagnostico.data.desc(),)
    itens = list(await sessao.scalars(consulta.order_by(*ordenacao).limit(limite).offset(deslocamento)))
    patologias = await mapa_patologias(sessao)
    return PaginaDiagnosticos(total=total, itens=[para_admin(d, patologias) for d in itens])


@router.get("/utilizadores", response_model=PaginaUtilizadores)
async def listar_utilizadores(utilizador: Pessoal, sessao: Sessao, q: str | None = None,
                              perfil: Perfil | None = None, provincia: str | None = None,
                              distrito_id: int | None = None, activo: bool | None = None,
                              limite: Limite = 50, deslocamento: Deslocamento = 0) -> PaginaUtilizadores:
    """Administrador: todas as contas. Técnico: os agricultores da sua zona."""
    total, itens = await utilizadores.listar(sessao, utilizador, q, perfil, provincia, distrito_id, activo,
                                             limite, deslocamento)
    return PaginaUtilizadores(total=total, itens=itens)


@router.patch("/utilizadores/{utilizador_id}", response_model=UtilizadorAdminLer)
async def actualizar_utilizador(utilizador_id: int, dados: UtilizadorActualizar, admin: Administrador,
                                sessao: Sessao) -> UtilizadorAdminLer:
    """Mudar nome, perfil, zona (distrito ou província) ou activar/desactivar a conta."""
    alvo = await utilizadores.actualizar(sessao, admin, utilizador_id, dados)
    return (await utilizadores.para_admin(sessao, [alvo]))[0]


@router.post("/utilizadores/{utilizador_id}/palavra-passe", status_code=status.HTTP_204_NO_CONTENT)
async def repor_palavra_passe(utilizador_id: int, dados: NovaPalavraPasse, admin: Administrador,
                              sessao: Sessao) -> None:
    await utilizadores.repor_palavra_passe(sessao, admin, utilizador_id, dados.palavra_passe)


@router.get("/auditoria", response_model=PaginaAuditoria)
async def auditoria(_: Administrador, sessao: Sessao, accao: str | None = None, entidade: str | None = None,
                    utilizador_id: int | None = None, limite: Limite = 50,
                    deslocamento: Deslocamento = 0) -> PaginaAuditoria:
    consulta = select(RegistoAuditoria).options(selectinload(RegistoAuditoria.utilizador))
    if accao:
        consulta = consulta.where(RegistoAuditoria.accao.startswith(accao))
    if entidade:
        consulta = consulta.where(RegistoAuditoria.entidade == entidade)
    if utilizador_id:
        consulta = consulta.where(RegistoAuditoria.utilizador_id == utilizador_id)
    total = await sessao.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    linhas = await sessao.scalars(consulta.order_by(RegistoAuditoria.criado_em.desc(), RegistoAuditoria.id.desc())
                                  .limit(limite).offset(deslocamento))
    return PaginaAuditoria(total=total, itens=[AuditoriaLer(
        id=r.id, utilizador_nome=r.utilizador.nome if r.utilizador else None, accao=r.accao,
        entidade=r.entidade, entidade_id=r.entidade_id, detalhes=r.detalhes, criado_em=r.criado_em)
        for r in linhas])


def _periodo(inicio: date | None, fim: date | None) -> tuple[datetime, datetime]:
    """Por omissão, os últimos 30 dias. As datas são dias inteiros (do início do 1.º ao fim do último)."""
    hoje = datetime.now(timezone.utc).date()
    fim = fim or hoje
    inicio = inicio or fim - timedelta(days=29)
    if inicio > fim:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A data de início é posterior à de fim")
    return (datetime.combine(inicio, time.min, tzinfo=timezone.utc),
            datetime.combine(fim, time.max, tzinfo=timezone.utc))


@router.get("/boletim", response_model=Boletim)
async def boletim(utilizador: Pessoal, sessao: Sessao, inicio: date | None = None, fim: date | None = None) -> Boletim:
    """Boletim fitossanitário da zona no período (o painel imprime-o em PDF)."""
    return await relatorios.boletim(sessao, utilizador, *_periodo(inicio, fim))


@router.get("/boletim.csv", response_class=Response, responses={200: {"content": {"text/csv": {}}}})
async def boletim_csv(utilizador: Pessoal, sessao: Sessao, inicio: date | None = None,
                      fim: date | None = None) -> Response:
    a, b = _periodo(inicio, fim)
    nome = f"boletim_{a:%Y%m%d}_{b:%Y%m%d}.csv"
    return Response(await relatorios.boletim_csv(sessao, utilizador, a, b), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{nome}"'})


@router.get("/eficacia", response_model=list[EficaciaPatologia])
async def eficacia(utilizador: Pessoal, sessao: Sessao, desde: datetime | None = None) -> list[EficaciaPatologia]:
    """Das respostas dos agricultores: quem seguiu a recomendação e a planta melhorou, por praga."""
    return await relatorios.eficacia(sessao, utilizador, desde)
