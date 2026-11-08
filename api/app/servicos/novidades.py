"""Novidades para o agricultor (funcionalidade 13b, notificações sem Firebase).

A app consulta GET /novidades?desde=... em segundo plano (de 15 em 15 minutos, no mínimo, por
limitação do Android) e mostra uma notificação local por cada novidade: alerta da zona, validação
do técnico, visita agendada ou resolvida, campanha nova. A resposta traz `agora`, que a app guarda
e envia como `desde` na consulta seguinte. Sem `desde` (primeira consulta), não devolve nada:
só marca o ponto de partida, para não notificar o que já é antigo.
"""

from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..esquemas import NovidadeAlerta, NovidadeCampanha, NovidadeValidacao, NovidadeVisita, Novidades
from ..tabelas import Alerta, Campanha, Diagnostico, EstadoVisita, PedidoVisita, Utilizador, Validacao
from .alertas import _activos_para
from .campanhas import _activas_para, hoje


async def novidades(sessao: AsyncSession, u: Utilizador, desde: datetime | None) -> Novidades:
    agora = datetime.now(timezone.utc)
    if desde is None:
        return Novidades(agora=agora, alertas=[], validacoes=[], visitas=[], campanhas=[])
    desde = desde if desde.tzinfo else desde.replace(tzinfo=timezone.utc)

    alertas = await sessao.scalars(select(Alerta).where(_activos_para(u), Alerta.criado_em > desde)
                                   .order_by(Alerta.criado_em))
    validacoes = await sessao.execute(
        select(Validacao.diagnostico_id, Validacao.classe_confirmada, Validacao.correcto)
        .join(Diagnostico, Diagnostico.id == Validacao.diagnostico_id)
        .where(Diagnostico.utilizador_id == u.id, Validacao.actualizado_em > desde))
    visitas = await sessao.scalars(select(PedidoVisita).where(
        PedidoVisita.agricultor_id == u.id, PedidoVisita.actualizado_em > desde,
        PedidoVisita.estado.in_((EstadoVisita.AGENDADA, EstadoVisita.RESOLVIDA))))
    dia = hoje()
    campanhas = await sessao.scalars(select(Campanha).where(
        _activas_para(u, dia),
        # nova desde a última consulta, ou agendada antes e que começou entretanto
        or_(Campanha.criado_em > desde, Campanha.inicio > desde.date())))
    return Novidades(
        agora=agora,
        alertas=[NovidadeAlerta(id=a.id, titulo=a.titulo, nivel=a.nivel) for a in alertas],
        validacoes=[NovidadeValidacao(diagnostico_id=d, classe_confirmada=k, correcto=c) for d, k, c in validacoes],
        visitas=[NovidadeVisita(id=v.id, estado=v.estado, data_agendada=v.data_agendada) for v in visitas],
        campanhas=[NovidadeCampanha(id=c.id, titulo=c.titulo, fim=c.fim) for c in campanhas],
    )
