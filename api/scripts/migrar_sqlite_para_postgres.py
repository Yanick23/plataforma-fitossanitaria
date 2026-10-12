"""Copia os dados de uma base SQLite de desenvolvimento para o PostgreSQL.

Mantém os ids (incluindo os UUID dos diagnósticos), para que os registos já
marcados como SINCRONIZADO nos telemóveis continuem a existir no servidor.

Utilização (a partir da pasta api/, com a API parada):
    python -m scripts.migrar_sqlite_para_postgres sqlite+aiosqlite:///./dados/agrodiagnostico.db \
        postgresql+asyncpg://utilizador:senha@localhost:5432/agrodiagnostico
"""

import asyncio
import sys

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.database import Base
from app import tabelas  # noqa: F401  (regista as tabelas no Base.metadata)

# Ordem que respeita as chaves estrangeiras.
ORDEM = ["utilizadores", "culturas", "patologias", "modelos_ml", "diagnosticos", "imagens"]


async def migrar(origem_url: str, destino_url: str) -> None:
    origem = create_async_engine(origem_url)
    destino = create_async_engine(destino_url)
    async with destino.begin() as d:
        await d.run_sync(Base.metadata.create_all)

    async with origem.connect() as o, destino.begin() as d:
        for nome in ORDEM:
            tabela = Base.metadata.tables[nome]
            linhas = [dict(r._mapping) for r in await o.execute(select(tabela))]
            ja_existem = await d.scalar(select(func.count()).select_from(tabela))
            if ja_existem:
                print(f"{nome}: o destino já tem {ja_existem} linhas; tabela ignorada")
                continue
            if linhas:
                await d.execute(tabela.insert(), linhas)
            # Acerta o contador dos ids inteiros para os próximos registos.
            if "id" in tabela.c and tabela.c.id.type.python_type is int:
                await d.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{nome}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {nome}), 0) + 1, false)"))
            print(f"{nome}: {len(linhas)} linhas copiadas")

    await origem.dispose()
    await destino.dispose()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    asyncio.run(migrar(sys.argv[1], sys.argv[2]))
