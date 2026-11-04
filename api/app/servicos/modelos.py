"""Versões do modelo: piloto por distrito, porta de qualidade e monitorização (deriva)."""

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..esquemas import Monitorizacao, PortaQualidade, SemanaModelo, SinalDeriva
from ..tabelas import Diagnostico, EstadoModelo, ModeloML, Utilizador, Validacao

MIN_VALIDACOES = 10      # validações mínimas para a porta de qualidade decidir
LIMIAR_CONFIANCA = 0.60  # o mesmo da app
SUBIDA_DERIVA = 0.10     # +10 pontos na proporção de confiança baixa = sinal de deriva
MIN_RECENTES = 20        # diagnósticos mínimos nas 2 semanas recentes para avaliar deriva


def distritos(m: ModeloML) -> list[int]:
    return json.loads(m.distritos_piloto) if m.distritos_piloto else []


async def para_utilizador(sessao: AsyncSession, cultura: str, u: Utilizador) -> ModeloML | None:
    """A versão que este utilizador deve usar: a piloto do seu distrito, se houver; senão a publicada."""
    modelos = list(await sessao.scalars(select(ModeloML).where(
        ModeloML.cultura_id == cultura, ModeloML.estado != EstadoModelo.RETIRADO).order_by(ModeloML.versao.desc())))
    for m in modelos:
        if m.estado == EstadoModelo.PUBLICADO:
            return m
        if m.estado == EstadoModelo.PILOTO and u.distrito_id in distritos(m):
            return m
    return None


async def exactidao_versao(sessao: AsyncSession, cultura: str, versao: int) -> tuple[int, float | None]:
    validados, correctos = (await sessao.execute(
        select(func.count(Validacao.diagnostico_id),
               func.coalesce(func.sum(case((Validacao.correcto.is_(True), 1), else_=0)), 0))
        .join(Diagnostico, Diagnostico.id == Validacao.diagnostico_id)
        .where(Diagnostico.cultura_id == cultura, Diagnostico.versao_modelo == versao))).one()
    return validados, (round(correctos / validados, 4) if validados else None)


async def porta_qualidade(sessao: AsyncSession, m: ModeloML) -> PortaQualidade:
    """Pode passar de piloto a publicado? Precisa de MIN_VALIDACOES e de não ser pior do que a versão publicada."""
    n, ex = await exactidao_versao(sessao, m.cultura_id, m.versao)
    ref = await sessao.scalar(select(ModeloML).where(
        ModeloML.cultura_id == m.cultura_id, ModeloML.estado == EstadoModelo.PUBLICADO, ModeloML.versao != m.versao)
        .order_by(ModeloML.versao.desc()))
    ref_n, ref_ex = await exactidao_versao(sessao, m.cultura_id, ref.versao) if ref else (0, None)

    if n < MIN_VALIDACOES:
        motivo, ok = f"A versão piloto tem {n} validações em campo; são precisas pelo menos {MIN_VALIDACOES}.", False
    elif ref is None or ref_n < MIN_VALIDACOES or ref_ex is None:
        motivo, ok = "Não há versão publicada com validações suficientes para comparar; aprovado pela exactidão em campo do piloto.", True
    elif ex is not None and ex >= ref_ex:
        motivo, ok = f"Exactidão em campo {ex:.1%} ≥ {ref_ex:.1%} da v{ref.versao}.", True
    else:
        motivo, ok = f"Exactidão em campo {ex:.1%} < {ref_ex:.1%} da v{ref.versao}: o piloto é pior.", False
    return PortaQualidade(versao=m.versao, validados=n, exactidao=ex, referencia_versao=ref.versao if ref else None,
                          referencia_exactidao=ref_ex, aprovado=ok, motivo=motivo)


def _segunda(d: datetime) -> str:
    d = d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    return (d - timedelta(days=d.weekday())).date().isoformat()


async def monitorizacao(sessao: AsyncSession, cultura: str, semanas: int = 12) -> Monitorizacao:
    desde = datetime.now(timezone.utc) - timedelta(weeks=semanas)
    linhas = await sessao.execute(
        select(Diagnostico.data, Diagnostico.versao_modelo, Diagnostico.confianca, Validacao.correcto)
        .outerjoin(Validacao, Validacao.diagnostico_id == Diagnostico.id)
        .where(Diagnostico.cultura_id == cultura, Diagnostico.data >= desde))
    grupos = defaultdict(lambda: {"n": 0, "conf": 0.0, "baixa": 0, "val": 0, "ok": 0})
    por_versao = defaultdict(list)  # versão -> [(data, baixa)]
    for data, versao, confianca, correcto in linhas:
        g = grupos[(_segunda(data), versao)]
        g["n"] += 1
        g["conf"] += confianca
        g["baixa"] += int(confianca < LIMIAR_CONFIANCA)
        if correcto is not None:
            g["val"] += 1
            g["ok"] += int(correcto)
        por_versao[versao].append((data if data.tzinfo else data.replace(tzinfo=timezone.utc), confianca < LIMIAR_CONFIANCA))

    semanas_out = [SemanaModelo(semana=s, versao=v, diagnosticos=g["n"], confianca_media=round(g["conf"] / g["n"], 4),
                                taxa_baixa=round(g["baixa"] / g["n"], 4), validados=g["val"],
                                exactidao=round(g["ok"] / g["val"], 4) if g["val"] else None)
                   for (s, v), g in sorted(grupos.items(), key=lambda x: (x[0][0], x[0][1] or 0))]

    sinais = []
    corte = datetime.now(timezone.utc) - timedelta(weeks=2)
    for versao, registos in por_versao.items():
        if versao is None:
            continue
        registos.sort()
        recentes = [b for d, b in registos if d >= corte]
        iniciais = [b for d, b in registos if d < registos[0][0] + timedelta(weeks=4) and d < corte]
        if not iniciais or not recentes:
            continue
        t0, t1 = sum(iniciais) / len(iniciais), sum(recentes) / len(recentes)
        deriva = len(recentes) >= MIN_RECENTES and t1 - t0 >= SUBIDA_DERIVA
        explicacao = (f"Confiança baixa passou de {t0:.0%} (primeiras semanas) para {t1:.0%} (últimas 2 semanas)"
                      + ("" if len(recentes) >= MIN_RECENTES else f"; poucos dados recentes ({len(recentes)})"))
        sinais.append(SinalDeriva(versao=versao, taxa_baixa_inicial=round(t0, 4), taxa_baixa_recente=round(t1, 4),
                                  diagnosticos_recentes=len(recentes), deriva=deriva, explicacao=explicacao))
    return Monitorizacao(cultura_id=cultura, semanas=semanas_out, sinais=sinais)
