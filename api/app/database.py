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


def migrar(ligacao) -> None:
    """Aplica as migrações do Alembic (uso: await ligacao.run_sync(migrar)).

    Uma base criada antes do Alembic (sem a tabela alembic_version) é marcada como estando na
    revisão 0001 (o esquema testado no PFC) e sobe a partir daí; uma base vazia é criada do zero.
    """
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect

    from .config import PASTA_API

    cfg = Config(str(PASTA_API / "alembic.ini"))
    cfg.set_main_option("script_location", str(PASTA_API / "migracoes"))
    cfg.attributes["connection"] = ligacao
    tabelas = set(inspect(ligacao).get_table_names())
    if "utilizadores" in tabelas and "alembic_version" not in tabelas:
        command.stamp(cfg, "0001")
    command.upgrade(cfg, "head")
