"""Risco meteorológico (funcionalidade 9): condições do tempo favoráveis a pragas e doenças.

Para cada distrito da zona com agricultores, pede-se à Open-Meteo a previsão horária dos próximos
7 dias (temperatura, humidade relativa e chuva) no centro do distrito. Resume-se cada dia e aplica-se
uma regra simples por praga/doença. O resultado é um SINAL de condições favoráveis para o técnico
decidir se avisa os agricultores; não é uma previsão de que a doença vai aparecer, e as regras não
foram validadas com dados de Moçambique.

As regras seguem a literatura indicada em `fontes`. Os números marcados como «limiar de projecto»
foram escolhidos para a plataforma e devem ser calibrados com os técnicos e com os casos validados.
"""

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx
from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import definicoes
from ..esquemas import RegraRisco, RiscoDistrito, RiscoMeteorologico
from ..regioes import condicao_utilizador_na_zona, zona_de
from ..tabelas import Distrito, Patologia, Perfil, PrevisaoMeteo, Utilizador

log = logging.getLogger(__name__)

FICHEIRO_CENTROS = Path(__file__).resolve().parent.parent / "centroides_distritos.json"
VARIAVEIS = ("temperature_2m", "relative_humidity_2m", "precipitation")
LOTE = 50  # distritos por pedido à Open-Meteo
FONTE = "Previsão horária de 7 dias da Open-Meteo (open-meteo.com), no centro de cada distrito."
AVISO = ("Condições favoráveis segundo regras simples da literatura, não uma previsão de que a doença vai "
         "aparecer. As regras ainda não foram validadas com casos de Moçambique.")


# --- Resumo diário -----------------------------------------------------------------

@dataclass
class Dia:
    data: date
    temperatura_media: float
    horas_hr90: int          # horas com humidade relativa >= 90 % (aproximação do orvalho / folha molhada)
    horas_hr95: int
    horas_hr90_22_30: int    # horas com HR >= 90 % e 22 <= T <= 30 °C
    chuva_mm: float


def resumir(horaria: dict) -> list[Dia]:
    """Agrupa a previsão horária por dia local (a Open-Meteo devolve a hora de Maputo)."""
    por_dia: dict[str, list[tuple[float, float, float]]] = {}
    for t, temp, hr, chuva in zip(horaria["time"], horaria["temperature_2m"], horaria["relative_humidity_2m"],
                                  horaria["precipitation"]):
        if temp is None or hr is None:
            continue
        por_dia.setdefault(t[:10], []).append((temp, hr, chuva or 0.0))
    dias = []
    for d, horas in sorted(por_dia.items()):
        if len(horas) < 18:  # dia incompleto no fim da previsão
            continue
        dias.append(Dia(
            data=date.fromisoformat(d),
            temperatura_media=round(sum(h[0] for h in horas) / len(horas), 1),
            horas_hr90=sum(h[1] >= 90 for h in horas),
            horas_hr95=sum(h[1] >= 95 for h in horas),
            horas_hr90_22_30=sum(h[1] >= 90 and 22 <= h[0] <= 30 for h in horas),
            chuva_mm=round(sum(h[2] for h in horas), 1),
        ))
    return dias[:7]


# --- Regras ---------------------------------------------------------------------------

@dataclass
class Avaliacao:
    nivel: str          # ALTO ou MEDIO
    motivo: str
    dias_favoraveis: int


@dataclass
class Regra:
    cultura_id: str
    classe: str
    condicao: str
    fontes: list[str]
    avaliar: Callable[[list[Dia]], Avaliacao | None]
    evidencia: str = "moderada"   # moderada | fraca
    limiares_de_projecto: list[str] = field(default_factory=list)


def _maior_sequencia(marcas: list[bool]) -> int:
    melhor = actual = 0
    for m in marcas:
        actual = actual + 1 if m else 0
        melhor = max(melhor, actual)
    return melhor


def _queima_da_folha(dias: list[Dia]) -> Avaliacao | None:
    fav = [15 <= d.temperatura_media <= 30 and d.horas_hr90 >= 9 for d in dias]
    n = sum(fav)
    if n < 2:
        return None
    return Avaliacao("ALTO" if n >= 3 else "MEDIO",
                     f"{n} dia(s) com temperatura entre 15 e 30 °C e 9 h ou mais de humidade ≥ 90%", n)


def _mancha_cinzenta(dias: list[Dia]) -> Avaliacao | None:
    fav = [d.horas_hr90_22_30 >= 12 for d in dias]
    n, seguidos = sum(fav), _maior_sequencia(fav)
    if n == 0:
        return None
    return Avaliacao("ALTO" if seguidos >= 2 else "MEDIO",
                     f"{n} dia(s) com 12 h ou mais de humidade ≥ 90% entre 22 e 30 °C"
                     + (f" ({seguidos} seguidos)" if seguidos >= 2 else ""), n)


def _mancha_castanha(dias: list[Dia]) -> Avaliacao | None:
    fav = [d.horas_hr95 >= 12 and d.temperatura_media >= 20 for d in dias]
    n = sum(fav)
    if n < 2:
        return None
    return Avaliacao("ALTO" if n >= 4 else "MEDIO",
                     f"{n} dia(s) quentes (média ≥ 20 °C) com 12 h ou mais de humidade ≥ 95%", n)


def _acaro_verde(dias: list[Dia]) -> Avaliacao | None:
    chuva = round(sum(d.chuva_mm for d in dias), 1)
    secos = sum(d.chuva_mm < 1 for d in dias)
    if chuva >= 10:
        return None
    return Avaliacao("ALTO" if chuva < 2 else "MEDIO",
                     f"semana seca: {str(chuva).replace('.', ',')} mm de chuva prevista em {len(dias)} dias", secos)


REGRAS: list[Regra] = [
    Regra("milho", "queima_da_folha",
          "Dia favorável: temperatura média entre 15 e 30 °C e pelo menos 9 h com humidade ≥ 90% "
          "(aproximação do orvalho). Risco médio com 2 dias favoráveis em 7; alto com 3 ou mais.",
          ["Infecção por Exserohilum turcicum entre 15 e 30 °C, com óptimo perto de 20 °C; a esporulação "
           "precisa de pelo menos 9 h de orvalho (Phytopathology 73:722, 1983; Phytopathology 79:1243, 1989).",
           "https://en.wikipedia.org/wiki/Northern_corn_leaf_blight"],
          _queima_da_folha, limiares_de_projecto=["humidade ≥ 90% como aproximação do orvalho", "2 e 3 dias"]),
    Regra("milho", "mancha_da_folha",
          "Dia favorável: pelo menos 12 h com humidade ≥ 90% e temperatura entre 22 e 30 °C. Risco médio "
          "com 1 dia; alto com 2 ou mais dias seguidos.",
          ["Mancha cinzenta (Cercospora spp.): humidade ≥ 90% e folha molhada durante 12 h ou mais, "
           "idealmente 2–3 dias seguidos (Purdue Extension BP-56; University of Nebraska CropWatch).",
           "Horas com 22 ≤ T ≤ 30 °C e HR ≥ 95% como preditor (Plant Disease 86:1127, 2002).",
           "https://extension.purdue.edu/extmedia/BP/BP-56.html",
           "https://cropwatch.unl.edu/plant-disease/corn/gray-leaf-spot/"],
          _mancha_cinzenta),
    Regra("mandioca", "mancha_castanha",
          "Dia favorável: temperatura média ≥ 20 °C e pelo menos 12 h com humidade ≥ 95%. Risco médio "
          "com 2 dias; alto com 4 ou mais.",
          ["Cercosporidium henningsii: os esporos germinam entre 80 e 100% de humidade, melhor a 100%; "
           "mais esporos na época húmida (tese KNUST, 1991: ir.knust.edu.gh/handle/123456789/3590).",
           "Calor e humidade favorecem a doença (Vikaspedia, IPM da mandioca)."],
          _mancha_castanha, evidencia="fraca",
          limiares_de_projecto=["média ≥ 20 °C", "12 h com HR ≥ 95%", "2 e 4 dias"]),
    Regra("mandioca", "acaro_verde",
          "Semana seca: risco médio com menos de 10 mm de chuva prevista em 7 dias; alto com menos de 2 mm.",
          ["Mononychellus tanajoa: as populações sobem na época seca e a chuva forte reduz-as "
           "(Akinlosotu, 1982; Gutierrez et al., 1988, Journal of Applied Ecology 25:941; Hanna et al., 2005)."],
          _acaro_verde, limiares_de_projecto=["10 mm e 2 mm em 7 dias"]),
]


# --- Previsões (Open-Meteo e cache na base) --------------------------------------------

def em_utc(d: datetime) -> datetime:
    """O SQLite devolve as datas sem fuso; são sempre UTC."""
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def centros() -> dict[tuple[str, str], tuple[float, float]]:
    dados = json.loads(FICHEIRO_CENTROS.read_text(encoding="utf-8"))
    return {(d["provincia"], d["nome"]): (d["latitude"], d["longitude"]) for d in dados["distritos"]}


async def descarregar(coordenadas: list[tuple[float, float]]) -> list[dict]:
    """Previsão horária de 7 dias para vários pontos num só pedido (a ordem é a das coordenadas)."""
    parametros = {
        "latitude": ",".join(str(c[0]) for c in coordenadas),
        "longitude": ",".join(str(c[1]) for c in coordenadas),
        "hourly": ",".join(VARIAVEIS), "forecast_days": 7, "timezone": "Africa/Maputo",
    }
    async with httpx.AsyncClient(timeout=20) as cliente:
        r = await cliente.get(definicoes.meteo_url, params=parametros)
        r.raise_for_status()
        corpo = r.json()
    lista = corpo if isinstance(corpo, list) else [corpo]
    return [{k: p["hourly"][k] for k in ("time", *VARIAVEIS)} for p in lista]


async def previsoes(sessao: AsyncSession, distritos: list[Distrito],
                    agora: datetime) -> tuple[dict[int, PrevisaoMeteo], str | None]:
    """Previsão de cada distrito: a guardada, se ainda for recente; senão pede-se uma nova.
    Se a Open-Meteo falhar, usa-se a última guardada e devolve-se o erro para o painel o dizer."""
    guardadas = {p.distrito_id: p for p in await sessao.scalars(
        select(PrevisaoMeteo).where(PrevisaoMeteo.distrito_id.in_([d.id for d in distritos])))} if distritos else {}
    limite = agora - timedelta(hours=definicoes.meteo_validade_horas)

    def recente(p: PrevisaoMeteo) -> bool:
        return em_utc(p.obtida_em) >= limite

    em_falta = [d for d in distritos if d.id not in guardadas or not recente(guardadas[d.id])]
    pontos = centros()
    em_falta = [d for d in em_falta if (d.provincia_codigo, d.nome) in pontos]
    erro = None
    for i in range(0, len(em_falta), LOTE):
        lote = em_falta[i:i + LOTE]
        try:
            respostas = await descarregar([pontos[(d.provincia_codigo, d.nome)] for d in lote])
        except (httpx.HTTPError, KeyError, ValueError) as e:
            log.warning("Open-Meteo indisponível: %s", e)
            erro = "Não foi possível obter a previsão nova (sem ligação à Open-Meteo); mostra-se a última guardada."
            break
        for d, horaria in zip(lote, respostas):
            p = guardadas.get(d.id) or PrevisaoMeteo(distrito_id=d.id)
            p.obtida_em, p.dados = agora, json.dumps(horaria)
            guardadas[d.id] = p
            sessao.add(p)
    await sessao.commit()
    return guardadas, erro


# --- Risco por distrito ------------------------------------------------------------------

async def distritos_com_agricultores(sessao: AsyncSession, u: Utilizador) -> list[Distrito]:
    ids = select(distinct(Utilizador.distrito_id)).where(
        Utilizador.perfil == Perfil.AGRICULTOR, Utilizador.activo.is_(True), Utilizador.distrito_id.is_not(None),
        condicao_utilizador_na_zona(zona_de(u)))
    return list(await sessao.scalars(select(Distrito).where(Distrito.id.in_(ids)).order_by(Distrito.nome)))


async def risco(sessao: AsyncSession, u: Utilizador, agora: datetime | None = None) -> RiscoMeteorologico:
    agora = agora or datetime.now(timezone.utc)
    distritos = await distritos_com_agricultores(sessao, u)
    guardadas, erro = await previsoes(sessao, distritos, agora)
    patologias = {(p.cultura_id, p.codigo): p for p in await sessao.scalars(select(Patologia))}
    regras = [r for r in REGRAS if (r.cultura_id, r.classe) in patologias]

    itens, obtidas = [], []
    for d in distritos:
        p = guardadas.get(d.id)
        if p is None:
            continue
        obtidas.append(em_utc(p.obtida_em))
        dias = resumir(json.loads(p.dados))
        if not dias:
            continue
        for r in regras:
            a = r.avaliar(dias)
            if a is None:
                continue
            pat = patologias[(r.cultura_id, r.classe)]
            itens.append(RiscoDistrito(
                distrito_id=d.id, distrito=d.nome, provincia_codigo=d.provincia_codigo, cultura_id=r.cultura_id,
                classe=r.classe, patologia_id=pat.id, patologia_nome=pat.nome_local, nivel=a.nivel,
                motivo=a.motivo, dias_favoraveis=a.dias_favoraveis, de=dias[0].data, ate=dias[-1].data,
                evidencia=r.evidencia, previsao_obtida_em=em_utc(p.obtida_em)))
    itens.sort(key=lambda x: (x.nivel != "ALTO", -x.dias_favoraveis, x.distrito, x.patologia_nome))
    return RiscoMeteorologico(
        gerado_em=agora, fonte=FONTE, aviso=AVISO, erro=erro,
        distritos_avaliados=len([d for d in distritos if d.id in guardadas]),
        distritos_com_agricultores=len(distritos),
        previsao_mais_antiga=min(obtidas) if obtidas else None,
        itens=itens,
        regras=[RegraRisco(cultura_id=r.cultura_id, classe=r.classe,
                           patologia_nome=patologias[(r.cultura_id, r.classe)].nome_local, condicao=r.condicao,
                           fontes=r.fontes, evidencia=r.evidencia, limiares_de_projecto=r.limiares_de_projecto)
                for r in regras],
    )
