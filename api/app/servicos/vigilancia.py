"""Vigilância: ocorrências por distrito (mapa) e detecção de surtos.

Regra de surto (por distrito, cultura e praga/doença; folhas saudáveis não contam):
    casos nos últimos `janela_dias` >= `min_casos`  e
    casos >= `factor` x média por janela nas `semanas_base` semanas anteriores
    (com média 0, basta chegar a `min_casos`).
Nível URGENTE quando a subida é de 4 vezes ou mais (ou 2 x min_casos sem histórico); senão AVISO.
É um sinal para o técnico decidir; não envia nada sozinho.
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..esquemas import Ocorrencia, Surto
from ..regioes import zona_de
from ..repositorios import diagnosticos as repo
from ..repositorios.diagnosticos import FiltrosDiagnostico, PatologiaPrevista
from ..tabelas import Diagnostico, Distrito, NivelAlerta, TipoPatologia, Utilizador


async def ocorrencias(sessao: AsyncSession, utilizador: Utilizador, f: FiltrosDiagnostico) -> list[Ocorrencia]:
    base = repo.com_filtros(repo.na_zona(repo.consulta_base(), zona_de(utilizador)), f)
    sub = base.with_only_columns(Diagnostico.distrito_id).where(Diagnostico.distrito_id.is_not(None)).subquery()
    linhas = await sessao.execute(
        select(Distrito.id, Distrito.nome, Distrito.provincia_codigo, func.count())
        .join(sub, sub.c.distrito_id == Distrito.id)
        .group_by(Distrito.id, Distrito.nome, Distrito.provincia_codigo)
        .order_by(func.count().desc()))
    return [Ocorrencia(distrito_id=i, distrito=n, provincia_codigo=p, total=t) for i, n, p, t in linhas]


async def surtos(sessao: AsyncSession, utilizador: Utilizador, janela_dias: int = 7, semanas_base: int = 4,
                 min_casos: int = 3, factor: float = 2.0, agora: datetime | None = None) -> list[Surto]:
    agora = agora or datetime.now(timezone.utc)
    inicio_janela = agora - timedelta(days=janela_dias)
    inicio_base = inicio_janela - timedelta(days=7 * semanas_base)

    consulta = repo.na_zona(repo.consulta_base(), zona_de(utilizador)).with_only_columns(
        Diagnostico.distrito_id, Diagnostico.cultura_id, Diagnostico.classe_prevista, Diagnostico.data,
        PatologiaPrevista.nome_local, PatologiaPrevista.tipo,
    ).where(Diagnostico.data >= inicio_base, Diagnostico.distrito_id.is_not(None),
            PatologiaPrevista.tipo != TipoPatologia.SAUDAVEL)

    recentes, anteriores, info = defaultdict(int), defaultdict(int), {}
    for distrito_id, cultura, classe, data, nome, tipo in await sessao.execute(consulta):
        chave = (distrito_id, cultura, classe)
        info[chave] = (nome, tipo)
        data = data if data.tzinfo else data.replace(tzinfo=timezone.utc)
        if data >= inicio_janela:
            recentes[chave] += 1
        else:
            anteriores[chave] += 1

    janelas_base = (7 * semanas_base) / janela_dias
    distritos = {d.id: d for d in await sessao.scalars(
        select(Distrito).where(Distrito.id.in_({k[0] for k in recentes})))} if recentes else {}
    resultado = []
    for chave, casos in recentes.items():
        media = anteriores.get(chave, 0) / janelas_base
        if casos < min_casos or (media > 0 and casos < factor * media):
            continue
        razao = round(casos / media, 2) if media > 0 else None
        urgente = (razao is not None and razao >= 4) or (razao is None and casos >= 2 * min_casos)
        distrito = distritos[chave[0]]
        nome, tipo = info[chave]
        resultado.append(Surto(
            distrito_id=distrito.id, distrito=distrito.nome, provincia_codigo=distrito.provincia_codigo,
            cultura_id=chave[1], classe=chave[2], patologia_nome=nome, tipo=tipo, casos_recentes=casos,
            media_anterior=round(media, 2), razao=razao,
            nivel=NivelAlerta.URGENTE if urgente else NivelAlerta.AVISO))
    return sorted(resultado, key=lambda s: (s.nivel != NivelAlerta.URGENTE, -s.casos_recentes))
