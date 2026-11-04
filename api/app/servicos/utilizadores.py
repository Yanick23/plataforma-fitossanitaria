"""Gestão de contas pelo pessoal: listar, mudar perfil e zona, desactivar, repor palavra-passe."""

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
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


async def actualizar(sessao: AsyncSession, admin: Utilizador, alvo_id: int, dados: UtilizadorActualizar) -> Utilizador:
    alvo = await sessao.get(Utilizador, alvo_id)
    if alvo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilizador não encontrado")
    campos = dados.model_fields_set
    if alvo.id == admin.id and (("activo" in campos and dados.activo is False)
                                or ("perfil" in campos and dados.perfil != Perfil.ADMINISTRADOR)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Não pode desactivar nem despromover a sua própria conta")
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
    auditar(sessao, admin, "utilizador.actualizar", "utilizador", alvo.id, antes=antes,
            depois=instantaneo(alvo, CAMPOS_AUDITADOS))
    await sessao.commit()
    return alvo


async def repor_palavra_passe(sessao: AsyncSession, admin: Utilizador, alvo_id: int, nova: str) -> None:
    alvo = await sessao.get(Utilizador, alvo_id)
    if alvo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilizador não encontrado")
    alvo.hash_palavra_passe = gerar_hash(nova)
    auditar(sessao, admin, "utilizador.repor_palavra_passe", "utilizador", alvo.id)
    await sessao.commit()
