"""Configuração lida de variáveis de ambiente (ou do ficheiro api/.env)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PASTA_API = Path(__file__).resolve().parent.parent


class Definicoes(BaseSettings):
    model_config = SettingsConfigDict(env_file=PASTA_API / ".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://agrodiagnostico:agrodiagnostico@localhost:5433/agrodiagnostico"

    jwt_segredo: str = "mude-esta-chave"
    jwt_algoritmo: str = "HS256"
    jwt_validade_dias: int = 30

    admin_telefone: str | None = None
    admin_palavra_passe: str | None = None
    admin_nome: str = "Administrador"

    # Ficheiros guardados pela API (fora do Git).
    pasta_modelos: Path = PASTA_API / "modelos"
    pasta_imagens: Path = PASTA_API / "dados" / "imagens"


definicoes = Definicoes()
