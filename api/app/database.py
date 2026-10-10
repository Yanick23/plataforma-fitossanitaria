"""Ligação assíncrona à base de dados com SQLAlchemy 2."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import definicoes


class Base(DeclarativeBase):
    pass


motor = create_async_engine(definicoes.database_url, pool_pre_ping=True)
SessaoLocal = async_sessionmaker(motor, expire_on_commit=False)


async def obter_sessao() -> AsyncIterator[AsyncSession]:
    """Dependência do FastAPI: uma sessão por pedido."""
    async with SessaoLocal() as sessao:
        yield sessao
