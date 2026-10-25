"""Registo e login por telefone + palavra-passe (RF10)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import obter_sessao
from ..esquemas import Login, Registo, Token, UtilizadorCriar, UtilizadorLer
from ..regioes import resolver_zona
from ..servicos.auditoria import auditar, instantaneo
from ..seguranca import (CONTA_DESACTIVADA, Administrador, UtilizadorActual, criar_token, gerar_hash,
                         verificar_palavra_passe)
from ..tabelas import Perfil, Utilizador

router = APIRouter(tags=["Autenticação"])
Sessao = Annotated[AsyncSession, Depends(obter_sessao)]


async def _criar(sessao: AsyncSession, dados: Registo, perfil: Perfil,
                 provincia_codigo: str | None = None) -> Utilizador:
    if await sessao.scalar(select(Utilizador).where(Utilizador.telefone == dados.telefone)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma conta com este telefone")
    distrito, provincia = await resolver_zona(sessao, dados.distrito_id, dados.area, provincia_codigo)
    utilizador = Utilizador(
        nome=dados.nome, telefone=dados.telefone, perfil=perfil,
        area=distrito.nome if distrito else dados.area,
        distrito_id=distrito.id if distrito else None, provincia_codigo=provincia,
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
    if not utilizador.activo:
        raise CONTA_DESACTIVADA
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
async def criar_utilizador(dados: UtilizadorCriar, admin: Administrador, sessao: Sessao) -> Utilizador:
    """Só o administrador cria contas de técnico (ou de outro administrador)."""
    novo = await _criar(sessao, dados, dados.perfil, dados.provincia_codigo)
    auditar(sessao, admin, "utilizador.criar", "utilizador", novo.id, depois=instantaneo(
        novo, ("nome", "telefone", "perfil", "distrito_id", "provincia_codigo")))
    await sessao.commit()
    return novo
