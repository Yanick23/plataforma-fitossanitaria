"""Línguas locais e áudio (funcionalidade 14): a equipa grava, outra pessoa valida, o agricultor ouve.
Só se usam distritos de Tete (Moatize, Changara, Mutarara, Chiuta)."""

from conftest import entrar, registar
from test_plataforma import ADMIN, criar_tecnico, distrito
from test_plataforma_perfis import criar_conta

WEBM = b"\x1a\x45\xdf\xa3" + b"voz de teste " * 50  # cabeçalho EBML + conteúdo qualquer


def gravar(cliente, cab, caminho, lingua="vmw", conteudo=WEBM, tipo="audio/webm;codecs=opus", duracao="12.5"):
    return cliente.post(caminho, headers=cab, data={"lingua": lingua, "duracao_s": duracao},
                        files={"ficheiro": ("gravacao.webm", conteudo, tipo)})


def mosaico(cliente) -> dict:
    return next(p for p in cliente.get("/patologias", params={"cultura": "mandioca"}).json() if p["codigo"] == "mosaico")


def test_linguas_e_lingua_do_agricultor(cliente):
    linguas = cliente.get("/linguas").json()
    codigos = [l["codigo"] for l in linguas]
    assert codigos[0] == "por" and {"vmw", "tso", "seh", "ngl"} <= set(codigos)
    assert "MZ-N" in next(l for l in linguas if l["codigo"] == "vmw")["provincias"]

    r = cliente.post("/auth/registar", json={"nome": "Agricultora", "telefone": "880000001", "palavra_passe": "segredo123",
                                             "area": "Moatize", "lingua": "seh"})
    assert r.status_code == 201 and r.json()["utilizador"]["lingua"] == "seh"
    cab = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert cliente.put("/auth/eu/lingua", headers=cab, json={"lingua": "nya"}).json()["lingua"] == "nya"
    assert cliente.put("/auth/eu/lingua", headers=cab, json={"lingua": "xyz"}).status_code == 422
    assert cliente.put("/auth/eu/lingua", headers=cab, json={"lingua": None}).json()["lingua"] is None
    assert cliente.post("/auth/registar", json={"nome": "Outro", "telefone": "880000002", "palavra_passe": "segredo123",
                                                "lingua": "abc"}).status_code == 422


def test_gravar_validar_e_ouvir_no_catalogo(cliente):
    rui = criar_tecnico(cliente, "880000011", area="Moatize")
    ana = criar_tecnico(cliente, "880000012", area="Changara")
    pid = mosaico(cliente)["id"]
    caminho = f"/patologias/{pid}/audios"

    r = gravar(cliente, rui, caminho)
    assert r.status_code == 201, r.text
    audio = r.json()
    assert (audio["lingua"], audio["lingua_nome"], audio["tipo_mime"], audio["validado_em"]) == (
        "vmw", "Emakhuwa", "audio/webm", None)
    assert audio["duracao_s"] == 12.5 and audio["tamanho_bytes"] == len(WEBM)
    # Por validar: o painel vê-a, a app (catálogo) ainda não
    assert [a["id"] for a in cliente.get("/audios", headers=rui, params={"patologia_id": pid}).json()] == [audio["id"]]
    assert mosaico(cliente)["audios"] == []

    # Quem gravou não valida a sua própria gravação
    assert cliente.post(f"/audios/{audio['id']}/validar", headers=rui).status_code == 403
    r = cliente.post(f"/audios/{audio['id']}/validar", headers=ana)
    assert r.status_code == 200 and r.json()["validado_por_nome"] == "Técnico 880000012"
    assert [a["lingua"] for a in mosaico(cliente)["audios"]] == ["vmw"]

    f = cliente.get(audio["url"])  # pública, como as fotos de referência
    assert f.status_code == 200 and f.content == WEBM and f.headers["content-type"] == "audio/webm"

    # Gravar de novo na mesma língua substitui (e volta a precisar de validação)
    nova = gravar(cliente, rui, caminho, conteudo=WEBM + b"!").json()
    assert cliente.get(audio["url"]).status_code == 404
    assert mosaico(cliente)["audios"] == []
    assert len(cliente.get("/audios", headers=rui, params={"patologia_id": pid}).json()) == 1
    cliente.post(f"/audios/{nova['id']}/validar", headers=ana)

    # O que não se aceita
    assert gravar(cliente, rui, caminho, tipo="text/plain").status_code == 415
    assert gravar(cliente, rui, caminho, conteudo=b"").status_code == 422
    assert gravar(cliente, rui, caminho, conteudo=b"0" * (4 * 1024 * 1024 + 1)).status_code == 413
    assert gravar(cliente, rui, caminho, duracao="200").status_code == 422
    assert gravar(cliente, rui, caminho, lingua="xyz").status_code == 422
    assert gravar(cliente, rui, "/patologias/99999/audios").status_code == 404
    assert gravar(cliente, registar(cliente, "880000013", area="Moatize"), caminho).status_code == 403
    assert gravar(cliente, criar_conta(cliente, "880000014", "INVESTIGADOR"), caminho).status_code == 403

    auditoria = cliente.get("/gestao/auditoria", headers=entrar(cliente, *ADMIN), params={"accao": "audio.gravar"}).json()
    assert auditoria["total"] >= 2


def test_audio_de_um_alerta(cliente):
    tecnico = criar_tecnico(cliente, "880000021", area="Mutarara")
    agr = registar(cliente, "880000022", area="Mutarara")
    alerta = cliente.post("/alertas", headers=tecnico, json={
        "titulo": "Lagarta em Mutarara", "mensagem": "Veja o funil das plantas.", "nivel": "AVISO",
        "distrito_id": distrito(cliente, "Mutarara")["id"]}).json()
    caminho = f"/alertas/{alerta['id']}/audios"

    r = gravar(cliente, tecnico, caminho, lingua="seh")
    assert r.status_code == 201 and r.json()["validado_em"] is not None  # vai logo com o alerta
    gravar(cliente, tecnico, caminho, lingua="por", tipo="audio/mp4")
    assert cliente.post(f"/audios/{r.json()['id']}/validar", headers=tecnico).status_code == 409

    meus = next(a for a in cliente.get("/alertas/meus", headers=agr).json() if a["id"] == alerta["id"])
    assert [a["lingua"] for a in meus["audios"]] == ["por", "seh"]
    painel = next(a for a in cliente.get("/alertas", headers=tecnico).json() if a["id"] == alerta["id"])
    assert len(painel["audios"]) == 2

    outro = criar_tecnico(cliente, "880000023", area="Chiuta")
    assert gravar(cliente, outro, caminho).status_code == 403
    assert cliente.delete(f"/audios/{r.json()['id']}", headers=outro).status_code == 403
    assert cliente.delete(f"/audios/{r.json()['id']}", headers=tecnico).status_code == 204
    assert cliente.get(r.json()["url"]).status_code == 404


def test_cobertura_e_reproducoes(cliente):
    coord = criar_conta(cliente, "880000031", "COORDENADOR", provincia_codigo="MZ-T")
    tecnico = criar_tecnico(cliente, "880000032", area="Changara")
    for i, lingua in enumerate(["nya", "nya", "seh", None]):
        cab = registar(cliente, f"88000004{i}", area="Changara")
        if lingua:
            cliente.put("/auth/eu/lingua", headers=cab, json={"lingua": lingua})
    pid = mosaico(cliente)["id"]
    a = gravar(cliente, tecnico, f"/patologias/{pid}/audios", lingua="nya").json()

    c = cliente.get("/audios/cobertura", headers=coord).json()
    linha = next(p for p in c["patologias"] if p["patologia_id"] == pid)
    assert linha["audios"]["nya"] == {"id": a["id"], "validado": False}
    assert c["agricultores_por_lingua"]["nya"] >= 2 and c["agricultores_por_lingua"]["seh"] >= 1
    assert c["agricultores_sem_lingua"] >= 1 and c["por_validar"] >= 1
    # A coordenadora de Tete não conta agricultores de outras províncias
    assert "vmw" not in c["agricultores_por_lingua"]
    assert cliente.get("/audios/cobertura", headers=registar(cliente, "880000049")).status_code == 403

    agr = registar(cliente, "880000050", area="Changara")
    assert cliente.post("/audios/reproducoes", headers=agr, json=[{"audio_id": a["id"], "vezes": 3},
                                                                   {"audio_id": 999999, "vezes": 1}]).status_code == 204
    lista = cliente.get("/audios", headers=coord, params={"patologia_id": pid}).json()
    assert next(x for x in lista if x["id"] == a["id"])["reproducoes"] == 3
