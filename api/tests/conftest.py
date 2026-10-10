"""Configuração dos testes: base de dados SQLite temporária e pastas temporárias.

As variáveis de ambiente são definidas ANTES de importar a app, porque a
configuração é lida na importação.
"""

import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

PASTA_TESTES = Path(tempfile.mkdtemp(prefix="agrodiagnostico_testes_"))
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{(PASTA_TESTES / 'teste.db').as_posix()}"
os.environ["PASTA_MODELOS"] = str(PASTA_TESTES / "modelos")
os.environ["PASTA_IMAGENS"] = str(PASTA_TESTES / "imagens")
os.environ["JWT_SEGREDO"] = "segredo-de-teste"
os.environ["ADMIN_TELEFONE"] = "840000000"
os.environ["ADMIN_PALAVRA_PASSE"] = "admin-123"
(PASTA_TESTES / "modelos").mkdir()

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def cliente():
    with TestClient(app) as c:  # executa o arranque (tabelas + dados iniciais)
        yield c
    shutil.rmtree(PASTA_TESTES, ignore_errors=True)


def registar(cliente, telefone: str, area: str | None = "Boane") -> dict:
    """Cria um agricultor e devolve os cabeçalhos com o token."""
    r = cliente.post("/auth/registar", json={
        "nome": f"Agricultor {telefone}", "telefone": telefone, "palavra_passe": "segredo123", "area": area})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def entrar(cliente, telefone: str, palavra_passe: str) -> dict:
    r = cliente.post("/auth/login", json={"telefone": telefone, "palavra_passe": palavra_passe})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def novo_diagnostico(cultura: str = "milho", classe: str = "lagarta_do_cartucho") -> dict:
    return {
        "id": str(uuid.uuid4()), "cultura_id": cultura, "classe_prevista": classe,
        "confianca": 0.91, "data": datetime.now(timezone.utc).isoformat(),
        "versao_modelo": 1, "tempo_inferencia_ms": 180,
    }
