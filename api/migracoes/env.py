"""Ambiente do Alembic.

Dois modos:
- pela linha de comandos (`alembic upgrade head`): abre a ligação a DATABASE_URL;
- pela API no arranque (app.database.migrar): recebe a ligação já aberta em
  config.attributes["connection"].
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app import tabelas  # noqa: F401  (regista as tabelas no Base.metadata)
from app.config import definicoes
from app.database import Base

config = context.config
if config.config_file_name and not config.attributes.get("connection"):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _correr(ligacao) -> None:
    context.configure(
        connection=ligacao, target_metadata=target_metadata,
        render_as_batch=ligacao.dialect.name == "sqlite",  # o SQLite não altera tabelas sem "batch"
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def _linha_de_comandos() -> None:
    motor = create_async_engine(definicoes.database_url)
    async with motor.begin() as ligacao:
        await ligacao.run_sync(_correr)
    await motor.dispose()


if (ligacao := config.attributes.get("connection")) is not None:
    _correr(ligacao)
else:
    asyncio.run(_linha_de_comandos())
