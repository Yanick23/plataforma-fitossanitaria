"""Campanhas de vigilância activa (funcionalidade 12).

O técnico pede aos agricultores de uma zona que fotografem uma cultura durante alguns dias, mesmo
que pareça saudável. Responder = sincronizar pelo menos um diagnóstico dessa cultura, nessa zona,
no período da campanha. Assim a vigilância deixa de depender só de quem já tem um problema, e o
técnico sabe também onde a praga NÃO está.
"""

from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..esquemas import CampanhaAgricultorLer, CampanhaCriar, CampanhaLer
from ..regioes import zona_contem, zona_de
from ..repositorios.diagnosticos import PatologiaPrevista
from ..tabelas import (Campanha, Cultura, Diagnostico, Distrito, Patologia, Perfil, TipoPatologia, Utilizador)
from . import sms
from .alertas import _destinatarios, destinatarios, nome_zona, validar_destino
from .auditoria import auditar, instantaneo

DURACAO_MAXIMA_DIAS = 60


def hoje() -> date:
    return datetime.now(timezone.utc).date()


def estado(c: Campanha, dia: date | None = None) -> str:
    dia = dia or hoje()
    if c.cancelada:
        return "CANCELADA"
    if dia < c.inicio:
        return "AGENDADA"
    return "ACTIVA" if dia <= c.fim else "TERMINADA"


def _periodo(c: Campanha) -> tuple[datetime, datetime]:
    return (datetime.combine(c.inicio, time.min, tzinfo=timezone.utc),
            datetime.combine(c.fim, time.max, tzinfo=timezone.utc))


def _diagnosticos_da_campanha(c: Campanha):
    """Condição: diagnósticos da cultura, no período, de agricultores que a campanha abrange."""
    inicio, fim = _periodo(c)
    return and_(Diagnostico.cultura_id == c.cultura_id, Diagnostico.data >= inicio, Diagnostico.data <= fim,
                Diagnostico.utilizador_id.in_(select(Utilizador.id).where(
                    _destinatarios(c.provincia_codigo, c.distrito_id))))


async def criar(sessao: AsyncSession, autor: Utilizador, dados: CampanhaCriar) -> Campanha:
    provincia_codigo, distrito_id = await validar_destino(sessao, autor, dados.provincia_codigo, dados.distrito_id)
    if await sessao.get(Cultura, dados.cultura_id) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Cultura inexistente")
    if dados.patologia_id is not None:
        p = await sessao.get(Patologia, dados.patologia_id)
        if p is None or p.cultura_id != dados.cultura_id:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A praga/doença não é desta cultura")
    if dados.fim < dados.inicio:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A data de fim é anterior à de início")
    if dados.fim < hoje():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A campanha já teria terminado")
    if (dados.fim - dados.inicio).days > DURACAO_MAXIMA_DIAS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            f"Uma campanha dura no máximo {DURACAO_MAXIMA_DIAS} dias")

    c = Campanha(titulo=dados.titulo.strip(), mensagem=dados.mensagem.strip(), cultura_id=dados.cultura_id,
                 patologia_id=dados.patologia_id, provincia_codigo=provincia_codigo, distrito_id=distrito_id,
                 inicio=dados.inicio, fim=dados.fim, autor_id=autor.id)
    sessao.add(c)
    await sessao.flush()
    depois = instantaneo(c, ("titulo", "cultura_id", "patologia_id", "provincia_codigo", "distrito_id",
                             "inicio", "fim"))
    if dados.enviar_sms:
        texto = sms.texto_sms("Campanha", c.titulo,
                              f"{c.mensagem} Até {c.fim:%d/%m}. Use a app Diagnóstico de culturas.")
        depois["sms"] = sms.registar(sessao, await destinatarios(sessao, provincia_codigo, distrito_id), texto,
                                     campanha_id=c.id)
    auditar(sessao, autor, "campanha.criar", "campanha", c.id, depois=depois)
    await sessao.commit()
    return c


def _visiveis(utilizador: Utilizador):
    """Campanhas que a equipa vê: as da sua zona (o administrador e o investigador vêem todas)."""
    zona = zona_de(utilizador)
    if zona.nacional:
        return Campanha.id.is_not(None)
    if zona.distrito_id:
        return Campanha.distrito_id == zona.distrito_id
    if zona.provincia_codigo:
        return or_(Campanha.provincia_codigo == zona.provincia_codigo,
                   Campanha.distrito_id.in_(select(Distrito.id).where(Distrito.provincia_codigo == zona.provincia_codigo)))
    return Campanha.id.is_(None)


async def para_ler(sessao: AsyncSession, c: Campanha) -> CampanhaLer:
    alvo = await sessao.scalar(select(func.count(Utilizador.id)).where(
        _destinatarios(c.provincia_codigo, c.distrito_id))) or 0
    cond = _diagnosticos_da_campanha(c)
    responderam = await sessao.scalar(select(func.count(func.distinct(Diagnostico.utilizador_id))).where(cond)) or 0
    total = await sessao.scalar(select(func.count(Diagnostico.id)).where(cond)) or 0
    casos = await sessao.scalar(
        select(func.count(Diagnostico.id)).join(PatologiaPrevista, and_(
            PatologiaPrevista.cultura_id == Diagnostico.cultura_id, PatologiaPrevista.codigo == Diagnostico.classe_prevista))
        .where(cond, PatologiaPrevista.tipo != TipoPatologia.SAUDAVEL)) or 0
    casos_pat = None
    if c.patologia:
        casos_pat = await sessao.scalar(select(func.count(Diagnostico.id)).where(
            cond, Diagnostico.classe_prevista == c.patologia.codigo)) or 0
    resumo = await sms.resumo(sessao, campanha_id=c.id)
    return CampanhaLer(
        id=c.id, titulo=c.titulo, mensagem=c.mensagem, cultura_id=c.cultura_id, patologia_id=c.patologia_id,
        patologia_nome=c.patologia.nome_local if c.patologia else None, provincia_codigo=c.provincia_codigo,
        distrito_id=c.distrito_id, zona=await nome_zona(sessao, c.provincia_codigo, c.distrito_id),
        inicio=c.inicio, fim=c.fim, estado=estado(c), autor_nome=c.autor.nome, criado_em=c.criado_em,
        agricultores=alvo, responderam=responderam, taxa_resposta=round(responderam / alvo, 4) if alvo else None,
        diagnosticos=total, casos_praga_doenca=casos, casos_patologia=casos_pat,
        sms=resumo if resumo.total else None)


def _consulta():
    return select(Campanha).options(selectinload(Campanha.autor), selectinload(Campanha.patologia))


async def obter(sessao: AsyncSession, campanha_id: int) -> Campanha:
    c = await sessao.scalar(_consulta().where(Campanha.id == campanha_id))
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campanha não encontrada")
    return c


async def listar(sessao: AsyncSession, utilizador: Utilizador, incluir_antigas: bool) -> list[CampanhaLer]:
    consulta = _consulta().where(_visiveis(utilizador)).order_by(Campanha.inicio.desc(), Campanha.id.desc())
    if not incluir_antigas:
        consulta = consulta.where(Campanha.cancelada.is_(False), Campanha.fim >= hoje() - timedelta(days=30))
    return [await para_ler(sessao, c) for c in await sessao.scalars(consulta)]


async def cancelar(sessao: AsyncSession, utilizador: Utilizador, campanha_id: int) -> None:
    c = await obter(sessao, campanha_id)
    provincia_do_distrito = (await sessao.get(Distrito, c.distrito_id)).provincia_codigo if c.distrito_id else None
    coordenador_da_zona = utilizador.perfil == Perfil.COORDENADOR and zona_contem(
        zona_de(utilizador), c.provincia_codigo, c.distrito_id, provincia_do_distrito)
    if utilizador.perfil != Perfil.ADMINISTRADOR and c.autor_id != utilizador.id and not coordenador_da_zona:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Só o autor, o coordenador da província ou o administrador podem cancelar")
    c.cancelada = True
    auditar(sessao, utilizador, "campanha.cancelar", "campanha", c.id)
    await sessao.commit()


def _activas_para(u: Utilizador, dia: date):
    """Campanhas que chegam a um agricultor: do seu distrito, da sua província ou nacionais, a decorrer."""
    provincia = select(Distrito.provincia_codigo).where(Distrito.id == u.distrito_id).scalar_subquery()
    destino = or_(
        and_(Campanha.distrito_id.is_(None), Campanha.provincia_codigo.is_(None)),
        and_(Campanha.distrito_id.is_not(None), Campanha.distrito_id == u.distrito_id),
        and_(Campanha.distrito_id.is_(None), Campanha.provincia_codigo == provincia),
    )
    return and_(destino, Campanha.cancelada.is_(False), Campanha.inicio <= dia, Campanha.fim >= dia)


async def minhas(sessao: AsyncSession, u: Utilizador) -> list[CampanhaAgricultorLer]:
    dia = hoje()
    resultado = []
    for c in await sessao.scalars(_consulta().where(_activas_para(u, dia)).order_by(Campanha.fim)):
        inicio, fim = _periodo(c)
        respondeu = await sessao.scalar(select(Diagnostico.id).where(
            Diagnostico.utilizador_id == u.id, Diagnostico.cultura_id == c.cultura_id,
            Diagnostico.data >= inicio, Diagnostico.data <= fim).limit(1)) is not None
        resultado.append(CampanhaAgricultorLer(
            id=c.id, titulo=c.titulo, mensagem=c.mensagem, cultura_id=c.cultura_id,
            patologia_codigo=c.patologia.codigo if c.patologia else None,
            zona=await nome_zona(sessao, c.provincia_codigo, c.distrito_id), inicio=c.inicio, fim=c.fim,
            respondeu=respondeu))
    return resultado
