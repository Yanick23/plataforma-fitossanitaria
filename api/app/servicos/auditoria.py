"""Registo de auditoria: quem fez o quê e quando."""

import json
from datetime import date, datetime
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from ..tabelas import RegistoAuditoria, Utilizador


def _serializavel(valor):
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, Enum):
        return valor.value
    return valor


def instantaneo(objecto, campos: tuple[str, ...]) -> dict:
    """Os valores de alguns campos de um objecto, prontos para guardar em JSON."""
    return {c: _serializavel(getattr(objecto, c)) for c in campos}


def auditar(sessao: AsyncSession, autor: Utilizador | None, accao: str, entidade: str,
            entidade_id: object = None, antes: dict | None = None, depois: dict | None = None) -> None:
    """Acrescenta o registo à sessão; fica gravado no mesmo commit que a alteração."""
    detalhes = {k: v for k, v in (("antes", antes), ("depois", depois)) if v is not None}
    sessao.add(RegistoAuditoria(
        utilizador_id=autor.id if autor else None, accao=accao, entidade=entidade,
        entidade_id=None if entidade_id is None else str(entidade_id),
        detalhes=json.dumps(detalhes, ensure_ascii=False, default=_serializavel) if detalhes else None,
    ))
