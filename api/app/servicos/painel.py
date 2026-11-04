"""Indicadores do painel, sempre limitados à zona de quem os pede."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..esquemas import Contagem, DiaContagem, DistritoContagem, Resumo
from ..regioes import condicao_utilizador_na_zona, filtro_zona, zona_de
from ..repositorios.diagnosticos import PatologiaPrevista
from ..tabelas import (Alerta, Cultura, Diagnostico, Distrito, Perfil, Provincia, TipoPatologia, Utilizador)

LIMIAR_CONFIANCA = 0.60  # o mesmo da app (RF05)


def _diagnosticos_da_zona(zona, *colunas):
    return (select(*colunas).select_from(Diagnostico)
            .join(Utilizador, Utilizador.id == Diagnostico.utilizador_id)
            .outerjoin(Distrito, Distrito.id == Diagnostico.distrito_id)
            .outerjoin(PatologiaPrevista, and_(PatologiaPrevista.cultura_id == Diagnostico.cultura_id,
                                               PatologiaPrevista.codigo == Diagnostico.classe_prevista))
            .where(filtro_zona(zona, Diagnostico.distrito_id, Distrito.provincia_codigo, Utilizador.area)))


async def descricao_zona(sessao: AsyncSession, utilizador: Utilizador) -> str:
    zona = zona_de(utilizador)
    if zona.nacional:
        return "Moçambique"
    if zona.distrito_id:
        d = await sessao.get(Distrito, zona.distrito_id)
        return f"{d.nome}, {(await sessao.get(Provincia, d.provincia_codigo)).nome}" if d else "—"
    if zona.provincia_codigo:
        p = await sessao.get(Provincia, zona.provincia_codigo)
        return f"Província de {p.nome}" if p else zona.provincia_codigo
    return zona.area_texto or "Sem zona atribuída"


async def resumo(sessao: AsyncSession, utilizador: Utilizador, dias: int = 30) -> Resumo:
    zona = zona_de(utilizador)
    agora = datetime.now(timezone.utc)
    inicio, inicio_anterior = agora - timedelta(days=dias), agora - timedelta(days=2 * dias)

    async def contar(*condicoes) -> int:
        return await sessao.scalar(_diagnosticos_da_zona(zona, func.count(Diagnostico.id)).where(*condicoes)) or 0

    def contar_utilizadores(perfil: Perfil, *condicoes):
        return select(func.count(Utilizador.id)).where(
            Utilizador.perfil == perfil, condicao_utilizador_na_zona(zona), *condicoes)

    agricultores = await sessao.scalar(contar_utilizadores(Perfil.AGRICULTOR)) or 0
    novos = await sessao.scalar(contar_utilizadores(Perfil.AGRICULTOR, Utilizador.criado_em >= inicio)) or 0
    tecnicos = await sessao.scalar(contar_utilizadores(Perfil.TECNICO)) if not zona.nacional else \
        await sessao.scalar(select(func.count(Utilizador.id)).where(Utilizador.perfil == Perfil.TECNICO))
    alertas_activos = await sessao.scalar(select(func.count(Alerta.id)).where(
        Alerta.arquivado.is_(False), or_(Alerta.expira_em.is_(None), Alerta.expira_em > agora),
        filtro_zona(zona, Alerta.distrito_id, Alerta.provincia_codigo)))

    # Série diária do período
    dia = func.date(Diagnostico.data)
    linhas = await sessao.execute(_diagnosticos_da_zona(
        zona, dia.label("dia"), func.count(Diagnostico.id),
        func.sum(case((PatologiaPrevista.tipo == TipoPatologia.PRAGA, 1), else_=0)),
        func.sum(case((PatologiaPrevista.tipo == TipoPatologia.DOENCA, 1), else_=0)),
    ).where(Diagnostico.data >= inicio).group_by(dia))
    por_dia_bd = {str(d): (t, p or 0, q or 0) for d, t, p, q in linhas}
    por_dia = []
    for i in range(dias, -1, -1):
        chave = (agora - timedelta(days=i)).date().isoformat()
        t, p, q = por_dia_bd.get(chave, (0, 0, 0))
        por_dia.append(DiaContagem(dia=chave, total=t, pragas=p, doencas=q))

    # Classes e culturas no período
    nomes = {(c, k): n for c, k, n in await sessao.execute(
        select(PatologiaPrevista.cultura_id, PatologiaPrevista.codigo, PatologiaPrevista.nome_local))}
    culturas = {c.id: c.nome for c in await sessao.scalars(select(Cultura))}
    por_classe = [
        Contagem(chave=f"{c}:{k}", nome=f"{nomes.get((c, k), k)} ({culturas.get(c, c).lower()})", total=t)
        for c, k, t in await sessao.execute(_diagnosticos_da_zona(
            zona, Diagnostico.cultura_id, Diagnostico.classe_prevista, func.count(Diagnostico.id))
            .where(Diagnostico.data >= inicio)
            .group_by(Diagnostico.cultura_id, Diagnostico.classe_prevista)
            .order_by(func.count(Diagnostico.id).desc()))
    ]
    por_cultura = [
        Contagem(chave=c, nome=culturas.get(c, c), total=t)
        for c, t in await sessao.execute(_diagnosticos_da_zona(zona, Diagnostico.cultura_id, func.count(Diagnostico.id))
                                         .where(Diagnostico.data >= inicio).group_by(Diagnostico.cultura_id))
    ]

    # Por distrito (para o mapa): diagnósticos no período e agricultores registados
    agric = defaultdict(int)
    for distrito_id, n in await sessao.execute(
            select(Utilizador.distrito_id, func.count(Utilizador.id))
            .where(Utilizador.perfil == Perfil.AGRICULTOR, Utilizador.distrito_id.is_not(None),
                   condicao_utilizador_na_zona(zona))
            .group_by(Utilizador.distrito_id)):
        agric[distrito_id] = n
    diag = {}
    for distrito_id, t, pd in await sessao.execute(_diagnosticos_da_zona(
            zona, Diagnostico.distrito_id, func.count(Diagnostico.id),
            func.sum(case((PatologiaPrevista.tipo != TipoPatologia.SAUDAVEL, 1), else_=0)))
            .where(Diagnostico.data >= inicio, Diagnostico.distrito_id.is_not(None))
            .group_by(Diagnostico.distrito_id)):
        diag[distrito_id] = (t, pd or 0)
    ids = set(agric) | set(diag)
    distritos = {d.id: d for d in await sessao.scalars(select(Distrito).where(Distrito.id.in_(ids)))} if ids else {}
    por_distrito = sorted(
        (DistritoContagem(distrito_id=i, distrito=distritos[i].nome, provincia_codigo=distritos[i].provincia_codigo,
                          total=diag.get(i, (0, 0))[0], pragas_doencas=diag.get(i, (0, 0))[1],
                          agricultores=agric.get(i, 0))
         for i in ids if i in distritos),
        key=lambda x: (-x.pragas_doencas, -x.total, x.distrito))

    return Resumo(
        zona=await descricao_zona(sessao, utilizador),
        agricultores=agricultores, agricultores_novos_30d=novos, tecnicos=tecnicos or 0,
        diagnosticos=await contar(),
        diagnosticos_30d=await contar(Diagnostico.data >= inicio),
        diagnosticos_30d_anteriores=await contar(Diagnostico.data >= inicio_anterior, Diagnostico.data < inicio),
        confianca_baixa_30d=await contar(Diagnostico.data >= inicio, Diagnostico.confianca < LIMIAR_CONFIANCA),
        alertas_activos=alertas_activos or 0,
        por_dia=por_dia, por_classe=por_classe, por_cultura=por_cultura, por_distrito=por_distrito,
    )
