"""Relatórios: eficácia das recomendações, pragas de declaração obrigatória e boletim fitossanitário."""

import csv
import io
from collections import Counter, defaultdict
from datetime import datetime, timezone

from fastapi import HTTPException, status

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..esquemas import Boletim, Declaracao, EficaciaPatologia, LinhaBoletim
from ..regioes import Zona, condicao_utilizador_na_zona, filtro_zona, zona_contem, zona_de
from ..repositorios import diagnosticos as repo
from ..repositorios.diagnosticos import FiltrosDiagnostico
from ..seguranca import anonimizado, pseudonimo
from ..tabelas import (Alerta, Cultura, Diagnostico, Distrito, Provincia, EstadoVisita, Patologia, PedidoVisita, Perfil, ResultadoTratamento,
                       Seguiu, Seguimento, TipoPatologia, Utilizador)
from . import alertas as servico_alertas
from .painel import descricao_de
from .vigilancia import surtos


def classe_final(d: Diagnostico) -> str:
    return d.validacao.classe_confirmada if d.validacao else d.classe_prevista


async def _patologias(sessao: AsyncSession) -> dict[tuple[str, str], Patologia]:
    return {(p.cultura_id, p.codigo): p for p in await sessao.scalars(select(Patologia))}


async def zona_escolhida(sessao: AsyncSession, u: Utilizador, provincia: str | None,
                         distrito_id: int | None) -> Zona:
    """A zona do boletim: a de quem pede, ou uma província/distrito dentro dela."""
    propria = zona_de(u)
    if distrito_id is not None:
        d = await sessao.get(Distrito, distrito_id)
        if d is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Distrito inexistente")
        if not zona_contem(propria, None, d.id, d.provincia_codigo):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Este distrito não é da sua zona")
        return Zona(distrito_id=d.id)
    if provincia is not None:
        if await sessao.get(Provincia, provincia) is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Província inexistente")
        if not zona_contem(propria, provincia, None, None):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Esta província não é da sua zona")
        return Zona(provincia_codigo=provincia)
    return propria


async def _diagnosticos(sessao: AsyncSession, u: Utilizador, desde: datetime | None, ate: datetime | None,
                        zona: Zona | None = None):
    consulta = repo.com_filtros(repo.na_zona(repo.consulta_base(), zona or zona_de(u)),
                                FiltrosDiagnostico(desde=desde, ate=ate))
    return list(await sessao.scalars(consulta.order_by(Diagnostico.data.desc())))


def _eficacia(diags: list[Diagnostico], pats: dict) -> list[EficaciaPatologia]:
    contas = defaultdict(lambda: [0, 0, 0])  # respostas, seguiram, melhoraram (dos que seguiram)
    for d in diags:
        s = d.seguimento
        if s is None:
            continue
        c = contas[(d.cultura_id, classe_final(d))]
        c[0] += 1
        if s.seguiu in (Seguiu.SIM, Seguiu.PARCIAL):
            c[1] += 1
            c[2] += int(s.resultado == ResultadoTratamento.MELHOROU)
    return sorted((EficaciaPatologia(cultura_id=cu, classe=k, nome=pats[(cu, k)].nome_local if (cu, k) in pats else k,
                                     respostas=r, seguiram=sg, melhoraram=m, eficacia=round(m / sg, 4) if sg else None)
                   for (cu, k), (r, sg, m) in contas.items()), key=lambda e: -e.respostas)


async def eficacia(sessao: AsyncSession, u: Utilizador, desde: datetime | None = None) -> list[EficaciaPatologia]:
    return _eficacia(await _diagnosticos(sessao, u, desde, None), await _patologias(sessao))


def _declaracoes(diags: list[Diagnostico], pats: dict, anonimo: bool = False) -> list[Declaracao]:
    saida = []
    for d in diags:
        p = pats.get((d.cultura_id, classe_final(d)))
        if p is None or not p.declaracao_obrigatoria:
            continue
        saida.append(Declaracao(
            diagnostico_id=d.id, cultura_id=d.cultura_id, classe=p.codigo, patologia_nome=p.nome_local,
            estado="CONFIRMADO" if d.validacao else "SUSPEITA", confianca=d.confianca, data=d.data,
            distrito_nome=d.distrito.nome if d.distrito else None,
            provincia_codigo=d.distrito.provincia_codigo if d.distrito else None,
            agricultor_nome=pseudonimo(d.utilizador_id) if anonimo else d.utilizador.nome,
            agricultor_telefone="" if anonimo else d.utilizador.telefone))
    return saida


async def declaracoes(sessao: AsyncSession, u: Utilizador, desde: datetime | None = None) -> list[Declaracao]:
    """Casos de pragas/doenças de declaração obrigatória: confirmados pelo técnico ou suspeitos (só o modelo)."""
    return _declaracoes(await _diagnosticos(sessao, u, desde, None), await _patologias(sessao), anonimizado(u))


async def boletim(sessao: AsyncSession, u: Utilizador, inicio: datetime, fim: datetime,
                  zona: Zona | None = None) -> Boletim:
    zona = zona or zona_de(u)
    diags = await _diagnosticos(sessao, u, inicio, fim, zona)
    pats = await _patologias(sessao)
    pragas_doencas = [d for d in diags if (p := pats.get((d.cultura_id, classe_final(d)))) and p.tipo != TipoPatologia.SAUDAVEL]

    por_classe = Counter((d.cultura_id, classe_final(d)) for d in pragas_doencas)
    por_distrito = Counter(d.distrito.nome for d in pragas_doencas if d.distrito)
    validados = [d for d in diags if d.validacao]
    culturas = {c.id: c.nome for c in await sessao.scalars(select(Cultura))}
    novos = await sessao.scalar(select(func.count(Utilizador.id)).where(
        Utilizador.perfil == Perfil.AGRICULTOR, condicao_utilizador_na_zona(zona),
        Utilizador.criado_em >= inicio, Utilizador.criado_em <= fim)) or 0

    alertas = list(await sessao.scalars(select(Alerta).options(selectinload(Alerta.autor), selectinload(Alerta.patologia))
        .where(Alerta.criado_em >= inicio, Alerta.criado_em <= fim,
               filtro_zona(zona, Alerta.distrito_id, Alerta.provincia_codigo)).order_by(Alerta.criado_em)))
    visitas = list(await sessao.scalars(
        select(PedidoVisita).outerjoin(Distrito, Distrito.id == PedidoVisita.distrito_id)
        .join(Utilizador, Utilizador.id == PedidoVisita.agricultor_id)
        .where(PedidoVisita.criado_em >= inicio, PedidoVisita.criado_em <= fim,
               filtro_zona(zona, PedidoVisita.distrito_id, Distrito.provincia_codigo, Utilizador.area))))
    resolvidas = [v for v in visitas if v.estado == EstadoVisita.RESOLVIDA]
    dias = [(v.actualizado_em - v.criado_em).total_seconds() / 86400 for v in resolvidas]

    return Boletim(
        zona=await descricao_de(sessao, zona), inicio=inicio, fim=fim, gerado_em=datetime.now(timezone.utc),
        diagnosticos=len(diags), diagnosticos_pragas_doencas=len(pragas_doencas),
        agricultores_activos=len({d.utilizador_id for d in diags}), agricultores_novos=novos,
        taxa_confianca_baixa=round(sum(d.confianca < 0.6 for d in diags) / len(diags), 4) if diags else None,
        validados=len(validados),
        exactidao_campo=round(sum(d.validacao.correcto for d in validados) / len(validados), 4) if validados else None,
        alertas_enviados=len(alertas), visitas_pedidas=len(visitas), visitas_resolvidas=len(resolvidas),
        dias_medios_resolucao=round(sum(dias) / len(dias), 1) if dias else None,
        principais_pragas=[LinhaBoletim(nome=f"{pats[k].nome_local} ({culturas.get(k[0], k[0])})" if k in pats else k[1], valor=n)
                           for k, n in por_classe.most_common(8)],
        distritos_mais_afectados=[LinhaBoletim(nome=n, valor=v) for n, v in por_distrito.most_common(8)],
        alertas=await servico_alertas.para_ler(sessao, alertas),
        surtos=await surtos(sessao, u, agora=fim, zona=zona),
        declaracoes=_declaracoes(diags, pats, anonimizado(u)),
        eficacia=_eficacia(diags, pats),
    )


async def boletim_csv(sessao: AsyncSession, u: Utilizador, inicio: datetime, fim: datetime,
                      zona: Zona | None = None) -> str:
    """Contagens por distrito, cultura e praga/doença no período (para folha de cálculo)."""
    diags = await _diagnosticos(sessao, u, inicio, fim, zona)
    pats = await _patologias(sessao)
    contas = Counter()
    for d in diags:
        k = classe_final(d)
        contas[(d.distrito.provincia_codigo if d.distrito else "", d.distrito.nome if d.distrito else "",
                d.cultura_id, k, pats[(d.cultura_id, k)].nome_local if (d.cultura_id, k) in pats else k,
                int(d.validacao is not None))] += 1
    saida = io.StringIO()
    w = csv.writer(saida)
    w.writerow(["provincia", "distrito", "cultura", "classe", "nome_local", "validado_pelo_tecnico", "diagnosticos"])
    for chave, n in sorted(contas.items()):
        w.writerow([*chave, n])
    return "﻿" + saida.getvalue()  # BOM: o Excel abre os acentos correctamente

