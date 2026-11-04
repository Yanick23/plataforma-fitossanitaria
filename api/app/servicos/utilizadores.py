"""Gestão de contas pelo pessoal: listar, mudar perfil e zona, desactivar, repor palavra-passe.

Administrador: todas as contas e todos os perfis.
Coordenador provincial: só agricultores e técnicos da sua província, e só lhes dá esses dois perfis.
Técnico: só vê os agricultores da sua zona.
"""

from fastapi import HTTPException, status
from sqlalchemy import false, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..esquemas import UtilizadorActualizar, UtilizadorAdminLer
from ..regioes import condicao_utilizador_na_zona, resolver_zona, zona_de
from ..seguranca import gerar_hash
from ..tabelas import Diagnostico, Distrito, Perfil, Provincia, Utilizador
from .auditoria import auditar, instantaneo

CAMPOS_AUDITADOS = ("nome", "perfil", "distrito_id", "provincia_codigo", "activo")


async def listar(sessao: AsyncSession, pedinte: Utilizador, q: str | None, perfil: Perfil | None,
                 provincia: str | None, distrito_id: int | None, activo: bool | None,
                 limite: int, deslocamento: int) -> tuple[int, list[UtilizadorAdminLer]]:
    zona = zona_de(pedinte)
    if pedinte.perfil == Perfil.COORDENADOR:  # agricultores e técnicos da província (com ou sem distrito)
        consulta = select(Utilizador).where(_na_provincia(pedinte.provincia_codigo),
                                            Utilizador.perfil.in_(PERFIS_DO_COORDENADOR))
    else:
        consulta = select(Utilizador).where(condicao_utilizador_na_zona(zona))
    if pedinte.perfil == Perfil.TECNICO:  # o técnico só gere (vê) os agricultores da sua zona
        consulta = consulta.where(Utilizador.perfil == Perfil.AGRICULTOR)
    if q:
        termo = f"%{q.strip()}%"
        consulta = consulta.where(or_(Utilizador.nome.ilike(termo), Utilizador.telefone.ilike(termo)))
    if perfil:
        consulta = consulta.where(Utilizador.perfil == perfil)
    if distrito_id:
        consulta = consulta.where(Utilizador.distrito_id == distrito_id)
    elif provincia:
        consulta = consulta.where(Utilizador.provincia_codigo == provincia)
    if activo is not None:
        consulta = consulta.where(Utilizador.activo.is_(activo))

    total = await sessao.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    contas = list(await sessao.scalars(consulta.order_by(Utilizador.criado_em.desc())
                                       .limit(limite).offset(deslocamento)))
    return total, await para_admin(sessao, contas)


async def para_admin(sessao: AsyncSession, contas: list[Utilizador]) -> list[UtilizadorAdminLer]:
    if not contas:
        return []
    ids = [u.id for u in contas]
    n_diag = dict((await sessao.execute(select(Diagnostico.utilizador_id, func.count())
                                        .where(Diagnostico.utilizador_id.in_(ids))
                                        .group_by(Diagnostico.utilizador_id))).all())
    distritos = {d.id: d.nome for d in await sessao.scalars(select(Distrito).where(
        Distrito.id.in_({u.distrito_id for u in contas if u.distrito_id})))}
    provincias = {p.codigo: p.nome for p in await sessao.scalars(select(Provincia))}
    return [UtilizadorAdminLer(
        id=u.id, nome=u.nome, telefone=u.telefone, perfil=u.perfil, area=u.area, distrito_id=u.distrito_id,
        provincia_codigo=u.provincia_codigo, activo=u.activo, criado_em=u.criado_em,
        distrito_nome=distritos.get(u.distrito_id), provincia_nome=provincias.get(u.provincia_codigo),
        diagnosticos=n_diag.get(u.id, 0)) for u in contas]


# Perfis que o coordenador provincial pode ver, criar e alterar.
PERFIS_DO_COORDENADOR = (Perfil.AGRICULTOR, Perfil.TECNICO)
FORA_DA_PROVINCIA = HTTPException(status.HTTP_403_FORBIDDEN, "Esta conta não é da sua província")


def _na_provincia(provincia_codigo: str | None):
    if not provincia_codigo:
        return false()
    return or_(Utilizador.provincia_codigo == provincia_codigo,
               Utilizador.distrito_id.in_(select(Distrito.id).where(Distrito.provincia_codigo == provincia_codigo)))


def verificar_perfil_pedido(gestor: Utilizador, perfil: Perfil | None) -> None:
    """O coordenador só cria ou atribui os perfis de agricultor e de técnico."""
    if gestor.perfil == Perfil.COORDENADOR and perfil is not None and perfil not in PERFIS_DO_COORDENADOR:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "O coordenador só atribui os perfis de agricultor e técnico")


def verificar_zona_final(gestor: Utilizador, perfil: Perfil, provincia_codigo: str | None) -> None:
    """Depois de alterar: o coordenador precisa de província e o do gestor-coordenador fica na dele."""
    if perfil == Perfil.COORDENADOR and not provincia_codigo:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "O coordenador precisa de uma província")
    if gestor.perfil == Perfil.COORDENADOR and provincia_codigo != gestor.provincia_codigo:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Só pode colocar contas na sua província")


def _pode_gerir(gestor: Utilizador, alvo: Utilizador) -> bool:
    if gestor.perfil == Perfil.ADMINISTRADOR:
        return True
    return (gestor.perfil == Perfil.COORDENADOR and alvo.perfil in PERFIS_DO_COORDENADOR
            and bool(gestor.provincia_codigo) and alvo.provincia_codigo == gestor.provincia_codigo)


async def _alvo(sessao: AsyncSession, gestor: Utilizador, alvo_id: int) -> Utilizador:
    alvo = await sessao.get(Utilizador, alvo_id)
    if alvo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilizador não encontrado")
    if not _pode_gerir(gestor, alvo):
        raise FORA_DA_PROVINCIA
    return alvo


async def actualizar(sessao: AsyncSession, admin: Utilizador, alvo_id: int, dados: UtilizadorActualizar) -> Utilizador:
    """`admin` é quem gere: administrador ou coordenador provincial."""
    campos = dados.model_fields_set
    if admin.id == alvo_id and (("activo" in campos and dados.activo is False)
                                or ("perfil" in campos and dados.perfil != admin.perfil)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Não pode desactivar nem mudar o perfil da sua própria conta")
    alvo = admin if admin.id == alvo_id else await _alvo(sessao, admin, alvo_id)
    if "perfil" in campos:
        verificar_perfil_pedido(admin, dados.perfil)
    antes = instantaneo(alvo, CAMPOS_AUDITADOS)
    if "nome" in campos and dados.nome:
        alvo.nome = dados.nome.strip()
    if "perfil" in campos and dados.perfil:
        alvo.perfil = dados.perfil
    if "activo" in campos and dados.activo is not None:
        alvo.activo = dados.activo
    if "distrito_id" in campos or "provincia_codigo" in campos:
        distrito, provincia = await resolver_zona(
            sessao, dados.distrito_id, None, dados.provincia_codigo if "provincia_codigo" in campos else None)
        alvo.distrito_id = distrito.id if distrito else None
        alvo.provincia_codigo = provincia
        if distrito:
            alvo.area = distrito.nome
    verificar_zona_final(admin, alvo.perfil, alvo.provincia_codigo)
    auditar(sessao, admin, "utilizador.actualizar", "utilizador", alvo.id, antes=antes,
            depois=instantaneo(alvo, CAMPOS_AUDITADOS))
    await sessao.commit()
    return alvo


async def repor_palavra_passe(sessao: AsyncSession, admin: Utilizador, alvo_id: int, nova: str) -> None:
    alvo = await _alvo(sessao, admin, alvo_id)
    alvo.hash_palavra_passe = gerar_hash(nova)
    auditar(sessao, admin, "utilizador.repor_palavra_passe", "utilizador", alvo.id)
    await sessao.commit()
