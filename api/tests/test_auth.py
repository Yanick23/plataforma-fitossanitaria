from conftest import entrar, registar


def test_registo_e_login(cliente):
    cabecalhos = registar(cliente, "841111111")
    eu = cliente.get("/auth/eu", headers=cabecalhos).json()
    assert eu["telefone"] == "841111111"
    assert eu["perfil"] == "AGRICULTOR"  # o registo público cria sempre agricultores

    assert entrar(cliente, "841111111", "segredo123")


def test_palavra_passe_errada(cliente):
    registar(cliente, "841111112")
    r = cliente.post("/auth/login", json={"telefone": "841111112", "palavra_passe": "errada"})
    assert r.status_code == 401


def test_telefone_repetido(cliente):
    registar(cliente, "841111113")
    r = cliente.post("/auth/registar", json={
        "nome": "Outro", "telefone": "841111113", "palavra_passe": "segredo123"})
    assert r.status_code == 409


def test_palavra_passe_guardada_com_hash(cliente):
    import asyncio

    from sqlalchemy import select

    from app.database import SessaoLocal
    from app.tabelas import Utilizador

    registar(cliente, "841111114")

    async def ler():
        async with SessaoLocal() as s:
            return await s.scalar(select(Utilizador).where(Utilizador.telefone == "841111114"))

    u = asyncio.run(ler())
    assert u.hash_palavra_passe.startswith("$2b$")  # bcrypt
    assert "segredo123" not in u.hash_palavra_passe


def test_sem_token(cliente):
    assert cliente.get("/diagnosticos").status_code == 401
    assert cliente.get("/diagnosticos", headers={"Authorization": "Bearer invalido"}).status_code == 401


def test_renovar_token(cliente):
    cab = registar(cliente, "841111115")
    r = cliente.post("/auth/renovar", headers=cab)
    assert r.status_code == 200
    novo = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert cliente.get("/auth/eu", headers=novo).json()["telefone"] == "841111115"
