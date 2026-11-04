"""Alertas por zona: quem pode enviar para onde, alcance e leituras."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..esquemas import AlertaAgricultorLer, AlertaCriar, AlertaLer
from ..regioes import Zona, zona_contem, zona_de
from ..tabelas import (Alerta, AlertaLeitura, Cultura, Distrito, Patologia, Perfil, Provincia, Utilizador)
from .auditoria import auditar, instantaneo


def _destinatarios(provincia_codigo: str | None, distrito_id: int | None):
    """Condição SQL: agricultores activos que recebem um alerta para esta zona."""
    base = and_(Utilizador.perfil == Perfil.AGRICULTOR, Utilizador.activo.is_(True))
    if distrito_id:
        return and_(base, Utilizador.distrito_id == distrito_id)
    if provincia_codigo:
        return and_(base, Utilizador.distrito_id.in_(
            select(Distrito.id).where(Distrito.provincia_codigo == provincia_codigo)))
    return base


async def nome_zona(sessao: AsyncSession, provincia_codigo: str | None, distrito_id: int | None) -> str:
    if distrito_id:
        d = await sessao.get(Distrito, distrito_id)
        return f"Distrito de {d.nome}" if d else f"Distrito {distrito_id}"
    if provincia_codigo:
        p = await sessao.get(Provincia, provincia_codigo)
        return f"Província de {p.nome}" if p else provincia_codigo
    return "Todo o país"


async def alcance(sessao: AsyncSession, provincia_codigo: str | None, distrito_id: int | None) -> tuple[str, int]:
    n = await sessao.scalar(select(func.count(Utilizador.id)).where(_destinatarios(provincia_codigo, distrito_id)))
    return await nome_zona(sessao, provincia_codigo, distrito_id), n or 0


async def validar_destino(sessao: AsyncSession, autor: Utilizador, provincia_codigo: str | None,
                          distrito_id: int | None) -> tuple[str | None, int | None]:
    """Normaliza o destino (distrito > província > país) e confirma que o autor o pode usar."""
    provincia_do_distrito = None
    if distrito_id is not None:
        distrito = await sessao.get(Distrito, distrito_id)
        if distrito is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Distrito inexistente")
        provincia_do_distrito = distrito.provincia_codigo
        provincia_codigo = None
    elif provincia_codigo is not None and await sessao.get(Provincia, provincia_codigo) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Província inexistente")
    zona = zona_de(autor)
    if not zona_contem(zona, provincia_codigo, distrito_id, provincia_do_distrito):
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Só pode enviar alertas para a sua zona de actuação" if not zona.vazia
                            else "Não tem zona de actuação atribuída: peça ao administrador")
    return provincia_codigo, distrito_id


async def criar(sessao: AsyncSession, autor: Utilizador, dados: AlertaCriar) -> Alerta:
    provincia_codigo, distrito_id = await validar_destino(sessao, autor, dados.provincia_codigo, dados.distrito_id)
    cultura_id = dados.cultura_id
    if dados.patologia_id is not None:
        patologia = await sessao.get(Patologia, dados.patologia_id)
        if patologia is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Praga/doença inexistente")
        cultura_id = patologia.cultura_id
    if cultura_id is not None and await sessao.get(Cultura, cultura_id) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Cultura inexistente")
    if dados.expira_em is not None and dados.expira_em <= datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A data de validade já passou")

    alerta = Alerta(titulo=dados.titulo.strip(), mensagem=dados.mensagem.strip(), nivel=dados.nivel,
                    cultura_id=cultura_id, patologia_id=dados.patologia_id, provincia_codigo=provincia_codigo,
                    distrito_id=distrito_id, autor_id=autor.id, expira_em=dados.expira_em)
    sessao.add(alerta)
    await sessao.flush()
    auditar(sessao, autor, "alerta.enviar", "alerta", alerta.id, depois=instantaneo(
        alerta, ("titulo", "nivel", "patologia_id", "provincia_codigo", "distrito_id", "expira_em")))
    await sessao.commit()
    return alerta


def _visiveis_pessoal(zona: Zona):
    """Alertas que o pessoal vê: os da sua zona (o administrador vê todos)."""
    if zona.nacional:
        return true()
    if zona.distrito_id:
        return Alerta.distrito_id == zona.distrito_id
    return or_(Alerta.provincia_codigo == zona.provincia_codigo,
               Alerta.distrito_id.in_(select(Distrito.id).where(Distrito.provincia_codigo == zona.provincia_codigo)))


async def para_ler(sessao: AsyncSession, alertas: list[Alerta]) -> list[AlertaLer]:
    if not alertas:
        return []
    lidos = dict((await sessao.execute(
        select(AlertaLeitura.alerta_id, func.count()).where(AlertaLeitura.alerta_id.in_([a.id for a in alertas]))
        .group_by(AlertaLeitura.alerta_id))).all())
    resultado = []
    for a in alertas:
        zona, destinatarios = await alcance(sessao, a.provincia_codigo, a.distrito_id)
        resultado.append(AlertaLer(
            id=a.id, titulo=a.titulo, mensagem=a.mensagem, nivel=a.nivel, cultura_id=a.cultura_id,
            patologia_id=a.patologia_id, patologia_nome=a.patologia.nome_local if a.patologia else None,
            provincia_codigo=a.provincia_codigo, distrito_id=a.distrito_id, zona=zona,
            autor_nome=a.autor.nome, criado_em=a.criado_em, expira_em=a.expira_em, arquivado=a.arquivado,
            destinatarios=destinatarios, lidos=lidos.get(a.id, 0)))
    return resultado


async def listar_pessoal(sessao: AsyncSession, utilizador: Utilizador, arquivados: bool) -> list[AlertaLer]:
    consulta = (select(Alerta).options(selectinload(Alerta.autor), selectinload(Alerta.patologia))
                .where(_visiveis_pessoal(zona_de(utilizador))).order_by(Alerta.criado_em.desc()))
    if not arquivados:
        consulta = consulta.where(Alerta.arquivado.is_(False))
    return await para_ler(sessao, list(await sessao.scalars(consulta)))


def _activos_para(u: Utilizador):
    """Alertas que chegam a um agricultor: do seu distrito, da sua província ou nacionais."""
    agora = datetime.now(timezone.utc)
    provincia = select(Distrito.provincia_codigo).where(Distrito.id == u.distrito_id).scalar_subquery()
    destino = or_(
        and_(Alerta.distrito_id.is_(None), Alerta.provincia_codigo.is_(None)),
        and_(Alerta.distrito_id.is_not(None), Alerta.distrito_id == u.distrito_id),
        and_(Alerta.distrito_id.is_(None), Alerta.provincia_codigo == provincia),
    )
    return and_(destino, Alerta.arquivado.is_(False), or_(Alerta.expira_em.is_(None), Alerta.expira_em > agora))


async def meus(sessao: AsyncSession, u: Utilizador) -> list[AlertaAgricultorLer]:
    alertas = list(await sessao.scalars(select(Alerta).where(_activos_para(u)).order_by(Alerta.criado_em.desc())
                                        .options(selectinload(Alerta.patologia))))
    lidos = set(await sessao.scalars(select(AlertaLeitura.alerta_id).where(
        AlertaLeitura.utilizador_id == u.id, AlertaLeitura.alerta_id.in_([a.id for a in alertas])))) if alertas else set()
    return [AlertaAgricultorLer(
        id=a.id, titulo=a.titulo, mensagem=a.mensagem, nivel=a.nivel, cultura_id=a.cultura_id,
        patologia_id=a.patologia_id, patologia_codigo=a.patologia.codigo if a.patologia else None,
        zona=await nome_zona(sessao, a.provincia_codigo, a.distrito_id),
        criado_em=a.criado_em, expira_em=a.expira_em, lido=a.id in lidos) for a in alertas]


async def marcar_lido(sessao: AsyncSession, u: Utilizador, alerta_id: int) -> None:
    if await sessao.scalar(select(Alerta.id).where(Alerta.id == alerta_id, _activos_para(u))) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alerta não encontrado")
    if await sessao.get(AlertaLeitura, (alerta_id, u.id)) is None:
        sessao.add(AlertaLeitura(alerta_id=alerta_id, utilizador_id=u.id))
        await sessao.commit()


async def arquivar(sessao: AsyncSession, utilizador: Utilizador, alerta_id: int) -> None:
    alerta = await sessao.get(Alerta, alerta_id)
    if alerta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alerta não encontrado")
    if utilizador.perfil != Perfil.ADMINISTRADOR and alerta.autor_id != utilizador.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Só o autor ou o administrador podem arquivar")
    alerta.arquivado = True
    auditar(sessao, utilizador, "alerta.arquivar", "alerta", alerta.id)
    await sessao.commit()

