"""Permissões por perfil: agricultor, técnico e administrador."""

from conftest import entrar, novo_diagnostico, registar

ADMIN = ("840000000", "admin-123")


def test_seed_culturas_e_patologias(cliente):
    culturas = {c["id"] for c in cliente.get("/culturas").json()}
    assert culturas == {"milho", "mandioca"}
    patologias = cliente.get("/patologias").json()
    assert len(patologias) == 12
    assert len(cliente.get("/patologias", params={"cultura": "milho"}).json()) == 7


def test_agricultor_nao_escreve_no_catalogo(cliente):
    cab = registar(cliente, "843333331")
    r = cliente.post("/culturas", headers=cab, json={"id": "feijao", "nome": "Feijão", "nome_cientifico": "Phaseolus"})
    assert r.status_code == 403
    pid = cliente.get("/patologias").json()[0]["id"]
    r = cliente.put(f"/patologias/{pid}", headers=cab, json={
        "nome_local": "x", "nome_cientifico": "y", "tipo": "PRAGA", "recomendacao": "z"})
    assert r.status_code == 403


def test_administrador_gere_catalogo(cliente):
    cab = entrar(cliente, *ADMIN)
    r = cliente.post("/culturas", headers=cab, json={"id": "feijao", "nome": "Feijão", "nome_cientifico": "Phaseolus vulgaris"})
    assert r.status_code == 201
    mosaico = next(p for p in cliente.get("/patologias", params={"cultura": "mandioca"}).json() if p["codigo"] == "mosaico")
    r = cliente.put(f"/patologias/{mosaico['id']}", headers=cab, json={
        "nome_local": mosaico["nome_local"], "nome_cientifico": mosaico["nome_cientifico"],
        "tipo": "DOENCA", "recomendacao": "Recomendação revista pelo técnico."})
    assert r.status_code == 200
    assert r.json()["recomendacao"] == "Recomendação revista pelo técnico."


def test_agricultor_ve_so_os_seus(cliente):
    cab_a = registar(cliente, "843333332")
    cab_b = registar(cliente, "843333333")
    da, db = novo_diagnostico(), novo_diagnostico()
    cliente.post("/diagnosticos", json=[da], headers=cab_a)
    cliente.post("/diagnosticos", json=[db], headers=cab_b)
    ids_a = {d["id"] for d in cliente.get("/diagnosticos", headers=cab_a).json()}
    assert da["id"] in ids_a and db["id"] not in ids_a


def test_tecnico_ve_os_da_sua_area(cliente):
    admin = entrar(cliente, *ADMIN)
    r = cliente.post("/utilizadores", headers=admin, json={
        "nome": "Técnica de Boane", "telefone": "843333334", "palavra_passe": "tecnico123",
        "perfil": "TECNICO", "area": "Manhiça"})
    assert r.status_code == 201
    tecnico = entrar(cliente, "843333334", "tecnico123")

    cab_mesma_area = registar(cliente, "843333335", area="Manhiça")
    cab_outra_area = registar(cliente, "843333336", area="Namaacha")
    d1, d2 = novo_diagnostico(), novo_diagnostico()
    cliente.post("/diagnosticos", json=[d1], headers=cab_mesma_area)
    cliente.post("/diagnosticos", json=[d2], headers=cab_outra_area)

    vistos = {d["id"] for d in cliente.get("/diagnosticos", headers=tecnico).json()}
    assert d1["id"] in vistos and d2["id"] not in vistos


def test_registo_publico_nao_cria_tecnicos(cliente):
    r = cliente.post("/auth/registar", json={
        "nome": "Falso", "telefone": "843333337", "palavra_passe": "segredo123", "perfil": "ADMINISTRADOR"})
    assert r.status_code == 201
    assert r.json()["utilizador"]["perfil"] == "AGRICULTOR"


def test_so_administrador_cria_utilizadores(cliente):
    cab = registar(cliente, "843333338")
    r = cliente.post("/utilizadores", headers=cab, json={
        "nome": "X", "telefone": "843333339", "palavra_passe": "segredo123", "perfil": "TECNICO"})
    assert r.status_code == 403


def test_apagar_patologia_so_administrador(cliente):
    admin = entrar(cliente, *ADMIN)
    r = cliente.post("/patologias", headers=admin, json={
        "cultura_id": "feijao", "codigo": "ferrugem", "nome_local": "Ferrugem",
        "nome_cientifico": "Uromyces appendiculatus", "tipo": "DOENCA", "recomendacao": "-"})
    assert r.status_code == 201, r.text
    cab = registar(cliente, "843333340")
    assert cliente.delete(f"/patologias/{r.json()['id']}", headers=cab).status_code == 403
    assert cliente.delete(f"/patologias/{r.json()['id']}", headers=admin).status_code == 204
