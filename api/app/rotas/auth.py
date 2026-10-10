"""Registo e login por telefone + palavra-passe (RF10)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import obter_sessao
from ..esquemas import Login, Registo, Token, UtilizadorCriar, UtilizadorLer
from ..seguranca import Administrador, UtilizadorActual, criar_token, gerar_hash, verificar_palavra_passe
from ..tabelas import Perfil, Utilizador

router = APIRouter(tags=["Autenticação"])
Sessao = Annotated[AsyncSession, Depends(obter_sessao)]


async def _criar(sessao: AsyncSession, dados: Registo, perfil: Perfil) -> Utilizador:
    if await sessao.scalar(select(Utilizador).where(Utilizador.telefone == dados.telefone)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma conta com este telefone")
    utilizador = Utilizador(
        nome=dados.nome, telefone=dados.telefone, area=dados.area, perfil=perfil,
        hash_palavra_passe=gerar_hash(dados.palavra_passe),
    )
    sessao.add(utilizador)
    await sessao.commit()
    await sessao.refresh(utilizador)
    return utilizador


@router.post("/auth/registar", response_model=Token, status_code=status.HTTP_201_CREATED)
async def registar(dados: Registo, sessao: Sessao) -> Token:
    """Cria uma conta de agricultor e devolve logo o token (entra sem novo login)."""
    utilizador = await _criar(sessao, dados, Perfil.AGRICULTOR)
    return Token(access_token=criar_token(utilizador), utilizador=UtilizadorLer.model_validate(utilizador))


@router.post("/auth/login", response_model=Token)
async def login(dados: Login, sessao: Sessao) -> Token:
    utilizador = await sessao.scalar(select(Utilizador).where(Utilizador.telefone == dados.telefone))
    if utilizador is None or not verificar_palavra_passe(dados.palavra_passe, utilizador.hash_palavra_passe):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Telefone ou palavra-passe incorrectos")
    return Token(access_token=criar_token(utilizador), utilizador=UtilizadorLer.model_validate(utilizador))


@router.post("/auth/renovar", response_model=Token)
async def renovar(utilizador: UtilizadorActual) -> Token:
    """Emite um token novo; a app chama-o em cada sincronização (secção 4.4.5)."""
    return Token(access_token=criar_token(utilizador), utilizador=UtilizadorLer.model_validate(utilizador))


@router.get("/auth/eu", response_model=UtilizadorLer)
async def eu(utilizador: UtilizadorActual) -> Utilizador:
    return utilizador


@router.post("/utilizadores", response_model=UtilizadorLer, status_code=status.HTTP_201_CREATED,
             tags=["Utilizadores"])
async def criar_utilizador(dados: UtilizadorCriar, _: Administrador, sessao: Sessao) -> Utilizador:
    """Só o administrador cria contas de técnico (ou de outro administrador)."""
    return await _criar(sessao, dados, dados.perfil)
