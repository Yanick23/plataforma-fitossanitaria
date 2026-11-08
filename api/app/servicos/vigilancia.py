"""Vigilância: ocorrências por distrito (mapa) e detecção de surtos.

Regra de surto (por distrito, cultura e praga/doença; folhas saudáveis não contam):
    casos nos últimos `janela_dias` >= `min_casos`  e
    casos >= `factor` x média por janela nas `semanas_base` semanas anteriores
    (com média 0, basta chegar a `min_casos`).
Nível URGENTE quando a subida é de 4 vezes ou mais (ou 2 x min_casos sem histórico); senão AVISO.
É um sinal para o técnico decidir; não envia nada sozinho. O técnico confirma (e envia alerta) ou
descarta o sinal; a decisão vale para a janela em que foi tomada.
"""

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..esquemas import DecisaoSurtoEscrever, Ocorrencia, SemanaContagem, Surto
from ..regioes import Zona, zona_contem, zona_de
from ..repositorios import diagnosticos as repo
from ..repositorios.diagnosticos import FiltrosDiagnostico, PatologiaPrevista
from ..tabelas import (Cultura, DecisaoSinal, DecisaoSurto, Diagnostico, Distrito, NivelAlerta, TipoPatologia,
                       Utilizador)
from .auditoria import auditar


async def ocorrencias(sessao: AsyncSession, utilizador: Utilizador, f: FiltrosDiagnostico) -> list[Ocorrencia]:
    """Diagnósticos por distrito com os filtros; e a tendência (últimos 7 dias contra os 7 anteriores),
    com os mesmos filtros de cultura, praga, tipo e confiança, mas sem o período escolhido."""
    zona = zona_de(utilizador)
    base = repo.com_filtros(repo.na_zona(repo.consulta_base(), zona), f)
    sub = base.with_only_columns(Diagnostico.distrito_id).where(Diagnostico.distrito_id.is_not(None)).subquery()
    linhas = list(await sessao.execute(
        select(Distrito.id, Distrito.nome, Distrito.provincia_codigo, func.count())
        .join(sub, sub.c.distrito_id == Distrito.id)
        .group_by(Distrito.id, Distrito.nome, Distrito.provincia_codigo)
        .order_by(func.count().desc())))

    agora = datetime.now(timezone.utc)
    semana, quinzena = agora - timedelta(days=7), agora - timedelta(days=14)
    sem_periodo = FiltrosDiagnostico(**{**f.__dict__, "desde": quinzena, "ate": None})
    tendencia = repo.com_filtros(repo.na_zona(repo.consulta_base(), zona), sem_periodo).with_only_columns(
        Diagnostico.distrito_id,
        func.sum(case((Diagnostico.data >= semana, 1), else_=0)),
        func.sum(case((Diagnostico.data < semana, 1), else_=0)),
    ).where(Diagnostico.distrito_id.is_not(None)).group_by(Diagnostico.distrito_id)
    por_distrito = {d: (int(a or 0), int(b or 0)) for d, a, b in await sessao.execute(tendencia)}
    return [Ocorrencia(distrito_id=i, distrito=n, provincia_codigo=p, total=t,
                       ultimos_7d=por_distrito.get(i, (0, 0))[0], anteriores_7d=por_distrito.get(i, (0, 0))[1])
            for i, n, p, t in linhas]


def segunda_feira(d: date) -> date:
    return d - timedelta(days=d.weekday())


async def tendencia(sessao: AsyncSession, utilizador: Utilizador, f: FiltrosDiagnostico,
                    semanas: int = 8) -> list[SemanaContagem]:
    """Diagnósticos por semana (segunda a domingo) na zona, das últimas `semanas`, com os filtros."""
    hoje = datetime.now(timezone.utc).date()
    primeira = segunda_feira(hoje) - timedelta(weeks=semanas - 1)
    filtros = FiltrosDiagnostico(**{**f.__dict__, "desde": datetime.combine(primeira, datetime.min.time(),
                                                                            tzinfo=timezone.utc), "ate": None})
    consulta = repo.com_filtros(repo.na_zona(repo.consulta_base(), zona_de(utilizador)), filtros).with_only_columns(
        Diagnostico.data, PatologiaPrevista.tipo)
    contas: dict[date, list[int]] = {primeira + timedelta(weeks=i): [0, 0] for i in range(semanas)}
    for data, tipo in await sessao.execute(consulta):
        data = data if data.tzinfo else data.replace(tzinfo=timezone.utc)
        chave = segunda_feira(data.date())
        if chave in contas:
            contas[chave][0] += 1
            contas[chave][1] += int(tipo is not None and tipo != TipoPatologia.SAUDAVEL)
    return [SemanaContagem(semana=k, total=t, pragas_doencas=p) for k, (t, p) in sorted(contas.items())]


async def surtos(sessao: AsyncSession, utilizador: Utilizador, janela_dias: int = 7, semanas_base: int = 4,
                 min_casos: int = 3, factor: float = 2.0, agora: datetime | None = None,
                 zona: Zona | None = None) -> list[Surto]:
    agora = agora or datetime.now(timezone.utc)
    inicio_janela = agora - timedelta(days=janela_dias)
    inicio_base = inicio_janela - timedelta(days=7 * semanas_base)

    consulta = repo.na_zona(repo.consulta_base(), zona or zona_de(utilizador)).with_only_columns(
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
    # Decisões do técnico tomadas nesta janela (a mais recente de cada sinal)
    if resultado:
        decisoes = {}
        for d in await sessao.scalars(select(DecisaoSinal).options(selectinload(DecisaoSinal.utilizador)).where(
                DecisaoSinal.criado_em >= inicio_janela, DecisaoSinal.criado_em <= agora + timedelta(minutes=1),
                DecisaoSinal.distrito_id.in_({s.distrito_id for s in resultado})).order_by(DecisaoSinal.criado_em)):
            decisoes[(d.distrito_id, d.cultura_id, d.classe)] = d
        for s in resultado:
            d = decisoes.get((s.distrito_id, s.cultura_id, s.classe))
            if d:
                s.decisao, s.decisao_nota = d.decisao.value, d.nota
                s.decidido_por, s.decidido_em = d.utilizador.nome, d.criado_em
    return sorted(resultado, key=lambda s: (s.decisao == "DESCARTADO", s.nivel != NivelAlerta.URGENTE,
                                            -s.casos_recentes))


async def decidir(sessao: AsyncSession, utilizador: Utilizador, dados: DecisaoSurtoEscrever) -> None:
    """O técnico confirma ou descarta um sinal de surto de um distrito da sua zona."""
    distrito = await sessao.get(Distrito, dados.distrito_id)
    if distrito is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Distrito inexistente")
    if await sessao.get(Cultura, dados.cultura_id) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Cultura inexistente")
    if not zona_contem(zona_de(utilizador), None, distrito.id, distrito.provincia_codigo):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Este distrito não é da sua zona")
    nota = (dados.nota or "").strip() or None
    d = DecisaoSinal(distrito_id=distrito.id, cultura_id=dados.cultura_id, classe=dados.classe,
                     decisao=DecisaoSurto(dados.decisao), nota=nota, utilizador_id=utilizador.id)
    sessao.add(d)
    await sessao.flush()
    auditar(sessao, utilizador, "surto.decidir", "surto", d.id, depois={
        "distrito": distrito.nome, "cultura_id": dados.cultura_id, "classe": dados.classe,
        "decisao": dados.decisao, "nota": nota})
    await sessao.commit()
