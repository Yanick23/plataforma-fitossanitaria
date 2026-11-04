"""Pedidos de visita técnica: o agricultor pede, o técnico da zona agenda e resolve."""

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..esquemas import VisitaActualizar, VisitaCriar, VisitaLer
from ..regioes import filtro_zona, zona_de
from ..tabelas import Diagnostico, Distrito, EstadoVisita, Patologia, PedidoVisita, Perfil, Utilizador
from .auditoria import auditar, instantaneo

ACTIVOS = (EstadoVisita.PENDENTE, EstadoVisita.AGENDADA)
# Transições permitidas ao técnico
TRANSICOES = {
    EstadoVisita.PENDENTE: {EstadoVisita.AGENDADA, EstadoVisita.RESOLVIDA, EstadoVisita.CANCELADA},
    EstadoVisita.AGENDADA: {EstadoVisita.AGENDADA, EstadoVisita.RESOLVIDA, EstadoVisita.CANCELADA},
    EstadoVisita.RESOLVIDA: set(),
    EstadoVisita.CANCELADA: set(),
}


def _consulta():
    return (select(PedidoVisita)
            .join(Utilizador, Utilizador.id == PedidoVisita.agricultor_id)
            .outerjoin(Distrito, Distrito.id == PedidoVisita.distrito_id)
            .options(selectinload(PedidoVisita.diagnostico), selectinload(PedidoVisita.agricultor),
                     selectinload(PedidoVisita.tecnico), selectinload(PedidoVisita.distrito)))


async def para_ler(sessao: AsyncSession, visitas: list[PedidoVisita]) -> list[VisitaLer]:
    nomes = {(p.cultura_id, p.codigo): p.nome_local for p in await sessao.scalars(select(Patologia))}
    return [VisitaLer(
        id=v.id, diagnostico_id=v.diagnostico_id, estado=v.estado, mensagem=v.mensagem,
        data_agendada=v.data_agendada, notas_tecnico=v.notas_tecnico, criado_em=v.criado_em,
        actualizado_em=v.actualizado_em, agricultor_nome=v.agricultor.nome,
        agricultor_telefone=v.agricultor.telefone, tecnico_nome=v.tecnico.nome if v.tecnico else None,
        distrito_nome=v.distrito.nome if v.distrito else None, cultura_id=v.diagnostico.cultura_id,
        classe_prevista=v.diagnostico.classe_prevista,
        patologia_nome=nomes.get((v.diagnostico.cultura_id, v.diagnostico.classe_prevista)),
    ) for v in visitas]


async def obter(sessao: AsyncSession, visita_id: int) -> PedidoVisita:
    v = await sessao.scalar(_consulta().where(PedidoVisita.id == visita_id))
    if v is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido de visita não encontrado")
    return v


async def pedir(sessao: AsyncSession, agricultor: Utilizador, dados: VisitaCriar) -> PedidoVisita:
    d = await sessao.get(Diagnostico, str(dados.diagnostico_id))
    if d is None or d.utilizador_id != agricultor.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Diagnóstico não encontrado (sincronize primeiro)")
    activo = await sessao.scalar(select(PedidoVisita.id).where(
        PedidoVisita.diagnostico_id == d.id, PedidoVisita.estado.in_(ACTIVOS)))
    if activo is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um pedido em curso para este diagnóstico")
    v = PedidoVisita(diagnostico_id=d.id, agricultor_id=agricultor.id,
                     distrito_id=d.distrito_id or agricultor.distrito_id,
                     mensagem=(dados.mensagem or "").strip() or None)
    sessao.add(v)
    await sessao.flush()
    auditar(sessao, agricultor, "visita.pedir", "visita", v.id)
    await sessao.commit()
    return v


def _na_zona_do_pessoal(utilizador: Utilizador):
    zona = zona_de(utilizador)
    return or_(filtro_zona(zona, PedidoVisita.distrito_id, Distrito.provincia_codigo, Utilizador.area),
               PedidoVisita.tecnico_id == utilizador.id)


async def listar_pessoal(sessao: AsyncSession, utilizador: Utilizador,
                         estado: EstadoVisita | None) -> list[PedidoVisita]:
    consulta = _consulta().where(_na_zona_do_pessoal(utilizador)).order_by(PedidoVisita.criado_em.desc())
    if estado:
        consulta = consulta.where(PedidoVisita.estado == estado)
    return list(await sessao.scalars(consulta))


async def listar_do_agricultor(sessao: AsyncSession, agricultor: Utilizador) -> list[PedidoVisita]:
    return list(await sessao.scalars(_consulta().where(PedidoVisita.agricultor_id == agricultor.id)
                                     .order_by(PedidoVisita.criado_em.desc())))


async def actualizar(sessao: AsyncSession, utilizador: Utilizador, visita_id: int,
                     dados: VisitaActualizar) -> None:
    pode = await sessao.scalar(_consulta().where(PedidoVisita.id == visita_id, _na_zona_do_pessoal(utilizador)))
    if pode is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido de visita não encontrado na sua zona")
    v = pode
    antes = instantaneo(v, ("estado", "data_agendada", "notas_tecnico", "tecnico_id"))
    campos = dados.model_fields_set
    if "estado" in campos and dados.estado is not None:
        if dados.estado not in TRANSICOES[v.estado]:
            raise HTTPException(status.HTTP_409_CONFLICT,
                                f"Não é possível passar de {v.estado.value} para {dados.estado.value}")
        if dados.estado == EstadoVisita.AGENDADA and not (dados.data_agendada or v.data_agendada):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Indique a data da visita")
        v.estado = dados.estado
        if dados.estado in (EstadoVisita.AGENDADA, EstadoVisita.RESOLVIDA):
            v.tecnico_id = utilizador.id
    if "data_agendada" in campos:
        v.data_agendada = dados.data_agendada
    if "notas_tecnico" in campos:
        v.notas_tecnico = (dados.notas_tecnico or "").strip() or None
    auditar(sessao, utilizador, "visita.actualizar", "visita", v.id, antes=antes,
            depois=instantaneo(v, ("estado", "data_agendada", "notas_tecnico", "tecnico_id")))
    await sessao.commit()


async def cancelar_pelo_agricultor(sessao: AsyncSession, agricultor: Utilizador, visita_id: int) -> None:
    v = await sessao.get(PedidoVisita, visita_id)
    if v is None or v.agricultor_id != agricultor.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido de visita não encontrado")
    if v.estado not in ACTIVOS:
        raise HTTPException(status.HTTP_409_CONFLICT, "Este pedido já está fechado")
    v.estado = EstadoVisita.CANCELADA
    auditar(sessao, agricultor, "visita.cancelar", "visita", v.id)
    await sessao.commit()


def e_pessoal(u: Utilizador) -> bool:
    return u.perfil in (Perfil.TECNICO, Perfil.ADMINISTRADOR)
