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
from .tabelas import PERFIS_GESTAO, PERFIS_LEITURA, PERFIS_PESSOAL, Perfil, Utilizador

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
    """Técnico, coordenador ou administrador (quem acompanha os agricultores de uma zona)."""
    if utilizador.perfil not in PERFIS_PESSOAL:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Operação reservada a técnicos e administradores")
    return utilizador


Pessoal = Annotated[Utilizador, Depends(exigir_pessoal)]


async def exigir_leitura(utilizador: UtilizadorActual) -> Utilizador:
    """Pessoal ou investigador: indicadores, vigilância e relatórios (o investigador só lê, anonimizado)."""
    if utilizador.perfil not in PERFIS_LEITURA:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Operação reservada à equipa da plataforma")
    return utilizador


Leitor = Annotated[Utilizador, Depends(exigir_leitura)]


async def exigir_gestor(utilizador: UtilizadorActual) -> Utilizador:
    """Coordenador (na sua província) ou administrador: gestão de contas."""
    if utilizador.perfil not in PERFIS_GESTAO:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Operação reservada a coordenadores e administradores")
    return utilizador


Gestor = Annotated[Utilizador, Depends(exigir_gestor)]


async def exigir_admin_ou_investigador(utilizador: UtilizadorActual) -> Utilizador:
    if utilizador.perfil not in (Perfil.ADMINISTRADOR, Perfil.INVESTIGADOR):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Operação reservada ao administrador e ao investigador")
    return utilizador


AdminOuInvestigador = Annotated[Utilizador, Depends(exigir_admin_ou_investigador)]


def anonimizado(utilizador: Utilizador) -> bool:
    """O investigador nunca vê nomes nem telefones de agricultores."""
    return utilizador.perfil == Perfil.INVESTIGADOR


def pseudonimo(utilizador_id: int) -> str:
    """Nome estável e não reversível para um agricultor ('Agricultor 3F9A1C'), sem expor o id."""
    import hashlib
    import hmac

    codigo = hmac.new(definicoes.jwt_segredo.encode(), str(utilizador_id).encode(), hashlib.sha256).hexdigest()
    return f"Agricultor {codigo[:6].upper()}"
