"""Consultas de diagnósticos com zona, filtros e paginação."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from sqlalchemy import Select, and_, func, select
from sqlalchemy.orm import aliased, selectinload

from ..regioes import Zona, filtro_zona
from ..tabelas import Diagnostico, Distrito, Patologia, TipoPatologia, Utilizador, Validacao


class EstadoValidacao(str, Enum):
    PENDENTE = "PENDENTE"      # ainda não revisto por um técnico
    CONFIRMADO = "CONFIRMADO"  # o técnico concordou com o modelo
    CORRIGIDO = "CORRIGIDO"    # o técnico corrigiu a classe


@dataclass
class FiltrosDiagnostico:
    cultura: str | None = None
    classe: str | None = None
    tipo: TipoPatologia | None = None
    provincia: str | None = None
    distrito_id: int | None = None
    desde: datetime | None = None
    ate: datetime | None = None
    confianca_max: float | None = None
    validacao: EstadoValidacao | None = None
    utilizador_id: int | None = None


PatologiaPrevista = aliased(Patologia)


def consulta_base() -> Select:
    """Diagnóstico + agricultor + distrito + patologia prevista (carregados juntos)."""
    return (
        select(Diagnostico)
        .join(Diagnostico.utilizador)
        .outerjoin(Distrito, Distrito.id == Diagnostico.distrito_id)
        .outerjoin(PatologiaPrevista, and_(PatologiaPrevista.cultura_id == Diagnostico.cultura_id,
                                           PatologiaPrevista.codigo == Diagnostico.classe_prevista))
        .outerjoin(Validacao, Validacao.diagnostico_id == Diagnostico.id)
        .options(selectinload(Diagnostico.utilizador), selectinload(Diagnostico.imagem),
                 selectinload(Diagnostico.distrito), selectinload(Diagnostico.validacao).selectinload(Validacao.tecnico))
    )


def na_zona(consulta: Select, zona: Zona) -> Select:
    return consulta.where(filtro_zona(zona, Diagnostico.distrito_id, Distrito.provincia_codigo, Utilizador.area))


def com_filtros(consulta: Select, f: FiltrosDiagnostico) -> Select:
    condicoes = []
    if f.cultura:
        condicoes.append(Diagnostico.cultura_id == f.cultura)
    if f.classe:
        condicoes.append(Diagnostico.classe_prevista == f.classe)
    if f.tipo:
        condicoes.append(PatologiaPrevista.tipo == f.tipo)
    if f.provincia:
        condicoes.append(Distrito.provincia_codigo == f.provincia)
    if f.distrito_id:
        condicoes.append(Diagnostico.distrito_id == f.distrito_id)
    if f.desde:
        condicoes.append(Diagnostico.data >= f.desde)
    if f.ate:
        condicoes.append(Diagnostico.data <= f.ate)
    if f.confianca_max is not None:
        condicoes.append(Diagnostico.confianca <= f.confianca_max)
    if f.utilizador_id:
        condicoes.append(Diagnostico.utilizador_id == f.utilizador_id)
    if f.validacao == EstadoValidacao.PENDENTE:
        condicoes.append(Validacao.diagnostico_id.is_(None))
    elif f.validacao == EstadoValidacao.CONFIRMADO:
        condicoes.append(Validacao.correcto.is_(True))
    elif f.validacao == EstadoValidacao.CORRIGIDO:
        condicoes.append(Validacao.correcto.is_(False))
    return consulta.where(*condicoes)


def total(consulta: Select) -> Select:
    return select(func.count()).select_from(consulta.order_by(None).subquery())


def estado_validacao(d: Diagnostico) -> EstadoValidacao:
    if d.validacao is None:
        return EstadoValidacao.PENDENTE
    return EstadoValidacao.CONFIRMADO if d.validacao.correcto else EstadoValidacao.CORRIGIDO
