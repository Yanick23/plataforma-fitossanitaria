"""Autenticação: palavra-passe com bcrypt, token JWT e controlo por perfil."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .config import definicoes
from .database import obter_sessao
from .tabelas import Perfil, Utilizador

esquema_bearer = HTTPBearer(auto_error=False, description="Token JWT obtido em POST /auth/login")


def gerar_hash(palavra_passe: str) -> str:
    return bcrypt.hashpw(palavra_passe.encode(), bcrypt.gensalt()).decode()


def verificar_palavra_passe(palavra_passe: str, hash_guardado: str) -> bool:
    return bcrypt.checkpw(palavra_passe.encode(), hash_guardado.encode())


def criar_token(utilizador: Utilizador) -> str:
    expira = datetime.now(timezone.utc) + timedelta(days=definicoes.jwt_validade_dias)
    dados = {"sub": str(utilizador.id), "perfil": utilizador.perfil.value, "exp": expira}
    return jwt.encode(dados, definicoes.jwt_segredo, algorithm=definicoes.jwt_algoritmo)


NAO_AUTENTICADO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token inválido ou em falta",
    headers={"WWW-Authenticate": "Bearer"},
)


async def utilizador_actual(
    credenciais: Annotated[HTTPAuthorizationCredentials | None, Depends(esquema_bearer)],
    sessao: Annotated[AsyncSession, Depends(obter_sessao)],
) -> Utilizador:
    if credenciais is None:
        raise NAO_AUTENTICADO
    try:
        dados = jwt.decode(credenciais.credentials, definicoes.jwt_segredo,
                           algorithms=[definicoes.jwt_algoritmo])
        utilizador_id = int(dados["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise NAO_AUTENTICADO from None
    utilizador = await sessao.get(Utilizador, utilizador_id)
    if utilizador is None:
        raise NAO_AUTENTICADO
    if not utilizador.activo:
        raise CONTA_DESACTIVADA
    return utilizador


CONTA_DESACTIVADA = HTTPException(status.HTTP_403_FORBIDDEN, "Conta desactivada. Contacte o administrador.")

UtilizadorActual = Annotated[Utilizador, Depends(utilizador_actual)]


async def exigir_administrador(utilizador: UtilizadorActual) -> Utilizador:
    if utilizador.perfil != Perfil.ADMINISTRADOR:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Operação reservada ao administrador")
    return utilizador


Administrador = Annotated[Utilizador, Depends(exigir_administrador)]


async def exigir_pessoal(utilizador: UtilizadorActual) -> Utilizador:
    """Técnico ou administrador (quem acompanha os agricultores de uma zona)."""
    if utilizador.perfil not in (Perfil.TECNICO, Perfil.ADMINISTRADOR):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Operação reservada a técnicos e administradores")
    return utilizador


Pessoal = Annotated[Utilizador, Depends(exigir_pessoal)]
