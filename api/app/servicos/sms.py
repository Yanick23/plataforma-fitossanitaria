"""SMS para os agricultores (funcionalidade 13), pela API Ola da Pavulla.

Fluxo: quem envia um alerta ou uma campanha pode pedir também SMS. A API regista um EnvioSMS
PENDENTE por agricultor, no mesmo commit do alerta, e envia-os depois da resposta (tarefa em
segundo plano), em lotes, para POST {SMS_URL}/v1/messages/bulk. Sem SMS_CHAVE configurada, os
envios ficam SIMULADO: nada sai, mas o resto (alcance, registo, painel) funciona.

Documentação do fornecedor: https://ola.pavulla.com/docsspage/message/overview
O endereço, a autenticação (HTTP Basic, token como utilizador e palavra-passe vazia) e o formato
do número (só dígitos) seguem a integração da Pavulla já em uso noutro sistema (AquaSystem), porque
a documentação não os diz.
"""

import logging
from collections import Counter

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import definicoes
from ..esquemas import ResumoSMS
from ..tabelas import EnvioSMS, EstadoSMS, Utilizador

log = logging.getLogger(__name__)


def configurado() -> bool:
    return bool(definicoes.sms_chave)


def numero_internacional(telefone: str) -> str:
    """Só dígitos, com indicativo: '84 123 4567' -> '258841234567'; '+258…' e '00258…' -> '258…'."""
    t = "".join(c for c in telefone if c.isdigit())
    if t.startswith("00"):
        t = t[2:]
    indicativo = definicoes.sms_indicativo
    if indicativo and len(t) == 9:  # número local moçambicano
        t = indicativo + t
    return t


def texto_sms(prefixo: str, titulo: str, mensagem: str) -> str:
    """Texto curto: «[Alerta] Título. Mensagem…», cortado ao limite configurado."""
    texto = f"[{prefixo}] {titulo.strip().rstrip('.')}. {mensagem.strip()}"
    limite = definicoes.sms_max_caracteres
    return texto if len(texto) <= limite else texto[: limite - 1].rstrip() + "…"


def registar(sessao: AsyncSession, destinatarios: list[Utilizador], conteudo: str, *,
             alerta_id: int | None = None, campanha_id: int | None = None) -> int:
    """Cria um EnvioSMS PENDENTE por destinatário (sem commit). Devolve quantos."""
    for u in destinatarios:
        sessao.add(EnvioSMS(alerta_id=alerta_id, campanha_id=campanha_id, utilizador_id=u.id,
                            telefone=u.telefone, conteudo=conteudo, estado=EstadoSMS.PENDENTE))
    return len(destinatarios)


async def _enviar_lote(cliente: httpx.AsyncClient, envios: list[EnvioSMS]) -> None:
    corpo = {"messages": [{"recipient": numero_internacional(e.telefone), "content": e.conteudo,
                           "tags": ["agrodiagnostico"]} for e in envios]}
    if definicoes.sms_provider_id:
        corpo["provider_id"] = definicoes.sms_provider_id
    if definicoes.sms_remetente:
        corpo["sender"] = definicoes.sms_remetente
    try:
        r = await cliente.post(f"{definicoes.sms_url.rstrip('/')}/v1/messages/bulk", json=corpo,
                               auth=(definicoes.sms_chave, ""))  # HTTP Basic, como na AquaSystem
        r.raise_for_status()
        resposta = r.json()
    except (httpx.HTTPError, ValueError) as e:
        log.warning("Envio de SMS falhou: %s", e)
        for env in envios:
            env.estado, env.erro = EstadoSMS.FALHOU, str(e)[:500]
        return
    # A documentação mostra {"messages": [...], "errors": [...]}, sem dizer como se casam com o pedido:
    # usa-se o destinatário para ligar cada mensagem devolvida ao envio.
    devolvidas = {m.get("recipient"): m for m in resposta.get("messages") or [] if isinstance(m, dict)}
    erros = resposta.get("errors") or []
    for env in envios:
        m = devolvidas.get(numero_internacional(env.telefone))
        if m is not None:
            env.estado, env.id_externo = EstadoSMS.ENVIADO, str(m.get("id") or "")[:80] or None
        else:
            env.estado = EstadoSMS.FALHOU
            env.erro = (str(erros[0].get("message")) if erros and isinstance(erros[0], dict)
                        else "O fornecedor não devolveu esta mensagem")[:500]


async def enviar_pendentes(sessao: AsyncSession, *, alerta_id: int | None = None,
                           campanha_id: int | None = None) -> Counter:
    """Envia (ou simula) os SMS pendentes de um alerta ou campanha. Devolve a contagem por estado."""
    consulta = select(EnvioSMS).where(EnvioSMS.estado == EstadoSMS.PENDENTE)
    if alerta_id is not None:
        consulta = consulta.where(EnvioSMS.alerta_id == alerta_id)
    if campanha_id is not None:
        consulta = consulta.where(EnvioSMS.campanha_id == campanha_id)
    pendentes = list(await sessao.scalars(consulta.order_by(EnvioSMS.id)))
    if not configurado():
        for env in pendentes:
            env.estado = EstadoSMS.SIMULADO
    else:
        async with httpx.AsyncClient(timeout=30) as cliente:
            for i in range(0, len(pendentes), definicoes.sms_lote):
                await _enviar_lote(cliente, pendentes[i:i + definicoes.sms_lote])
    await sessao.commit()
    return Counter(e.estado.value for e in pendentes)


async def enviar_em_segundo_plano(alerta_id: int | None = None, campanha_id: int | None = None) -> None:
    """Corre depois da resposta HTTP, com a sua própria sessão."""
    from ..database import SessaoLocal

    async with SessaoLocal() as sessao:
        await enviar_pendentes(sessao, alerta_id=alerta_id, campanha_id=campanha_id)


async def resumo(sessao: AsyncSession, *, alerta_id: int | None = None, campanha_id: int | None = None) -> ResumoSMS:
    consulta = select(EnvioSMS.estado)
    if alerta_id is not None:
        consulta = consulta.where(EnvioSMS.alerta_id == alerta_id)
    if campanha_id is not None:
        consulta = consulta.where(EnvioSMS.campanha_id == campanha_id)
    contas = Counter(e.value for e in await sessao.scalars(consulta))
    return ResumoSMS(total=sum(contas.values()), **{k.lower(): contas.get(k, 0) for k in
                                                     ("PENDENTE", "ENVIADO", "FALHOU", "SIMULADO")},
                     simulacao=not configurado())
