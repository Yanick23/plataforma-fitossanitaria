"""Notificações para a equipa: casos confirmados de pragas/doenças de declaração obrigatória (3b).

Quando um técnico confirma (ou corrige para) uma classe de declaração obrigatória, avisa-se logo:
- todos os administradores activos;
- os coordenadores activos da província do diagnóstico.
Quem validou não recebe aviso do próprio caso. Uma validação repetida com a mesma classe não volta
a avisar. As notificações aparecem no painel (sino no topo) e ficam no registo de auditoria.
"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..esquemas import ListaNotificacoes, NotificacaoLer
from ..tabelas import Diagnostico, Notificacao, Patologia, Perfil, Utilizador
from .auditoria import auditar

DECLARACAO_OBRIGATORIA = "DECLARACAO_OBRIGATORIA"


async def destinatarios_declaracao(sessao: AsyncSession, provincia_codigo: str | None) -> list[Utilizador]:
    condicao = Utilizador.perfil == Perfil.ADMINISTRADOR
    if provincia_codigo:
        condicao = or_(condicao, (Utilizador.perfil == Perfil.COORDENADOR)
                       & (Utilizador.provincia_codigo == provincia_codigo))
    return list(await sessao.scalars(select(Utilizador).where(condicao, Utilizador.activo.is_(True))
                                     .order_by(Utilizador.id)))


async def avisar_declaracao(sessao: AsyncSession, tecnico: Utilizador, d: Diagnostico, patologia: Patologia) -> int:
    """Cria as notificações (sem commit: ficam no mesmo commit que a validação). Devolve quantas."""
    distrito = d.distrito
    provincia = distrito.provincia_codigo if distrito else None
    onde = f"distrito de {distrito.nome} ({provincia})" if distrito else "zona desconhecida"
    titulo = f"Caso confirmado: {patologia.nome_local}"
    mensagem = (f"{tecnico.nome} confirmou um caso de {patologia.nome_local} ({patologia.nome_cientifico}), "
                f"praga/doença de declaração obrigatória, no {onde}. Diagnóstico de "
                f"{d.data:%d/%m/%Y}, confiança do modelo {round(d.confianca * 100)}%.")
    pessoas = [u for u in await destinatarios_declaracao(sessao, provincia) if u.id != tecnico.id]
    for u in pessoas:
        sessao.add(Notificacao(utilizador_id=u.id, tipo=DECLARACAO_OBRIGATORIA, titulo=titulo,
                               mensagem=mensagem, diagnostico_id=d.id))
    auditar(sessao, tecnico, "declaracao.notificar", "diagnostico", d.id, depois={
        "classe": patologia.codigo, "provincia": provincia, "destinatarios": [u.id for u in pessoas]})
    return len(pessoas)


async def listar(sessao: AsyncSession, u: Utilizador, so_nao_lidas: bool, limite: int) -> ListaNotificacoes:
    consulta = select(Notificacao).where(Notificacao.utilizador_id == u.id)
    if so_nao_lidas:
        consulta = consulta.where(Notificacao.lida_em.is_(None))
    itens = await sessao.scalars(consulta.order_by(Notificacao.criado_em.desc(), Notificacao.id.desc()).limit(limite))
    nao_lidas = await sessao.scalar(select(func.count(Notificacao.id)).where(
        Notificacao.utilizador_id == u.id, Notificacao.lida_em.is_(None))) or 0
    return ListaNotificacoes(nao_lidas=nao_lidas, itens=[NotificacaoLer.model_validate(n) for n in itens])


async def marcar_lida(sessao: AsyncSession, u: Utilizador, notificacao_id: int) -> None:
    n = await sessao.get(Notificacao, notificacao_id)
    if n is None or n.utilizador_id != u.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notificação não encontrada")
    if n.lida_em is None:
        n.lida_em = datetime.now(timezone.utc)
        await sessao.commit()


async def marcar_todas_lidas(sessao: AsyncSession, u: Utilizador) -> None:
    await sessao.execute(update(Notificacao).where(Notificacao.utilizador_id == u.id, Notificacao.lida_em.is_(None))
                         .values(lida_em=datetime.now(timezone.utc)))
    await sessao.commit()
