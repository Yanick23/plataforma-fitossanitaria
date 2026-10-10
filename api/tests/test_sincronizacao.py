"""RF09 / RNF07: nenhum diagnóstico se perde nem se duplica."""

import io

from PIL import Image

from conftest import novo_diagnostico, registar


def jpeg() -> bytes:
    saida = io.BytesIO()
    Image.new("RGB", (300, 200), (40, 160, 60)).save(saida, format="JPEG")
    return saida.getvalue()


def test_reenvio_nao_duplica(cliente):
    cab = registar(cliente, "842222221")
    lote = [novo_diagnostico(), novo_diagnostico("mandioca", "mosaico")]

    r1 = cliente.post("/diagnosticos", json=lote, headers=cab).json()
    assert len(r1["confirmados"]) == 2 and r1["rejeitados"] == []

    # A rede caiu antes de a app receber a resposta: a app reenvia o mesmo lote.
    r2 = cliente.post("/diagnosticos", json=lote, headers=cab).json()
    assert sorted(r2["confirmados"]) == sorted(r1["confirmados"])

    meus = cliente.get("/diagnosticos", headers=cab).json()
    assert len(meus) == 2


def test_id_repetido_no_mesmo_lote(cliente):
    cab = registar(cliente, "842222222")
    d = novo_diagnostico()
    r = cliente.post("/diagnosticos", json=[d, d], headers=cab).json()
    assert r["confirmados"] == [d["id"]]
    assert len(cliente.get("/diagnosticos", headers=cab).json()) == 1


def test_classe_invalida_rejeitada(cliente):
    cab = registar(cliente, "842222223")
    bom, mau = novo_diagnostico(), novo_diagnostico("milho", "classe_inexistente")
    r = cliente.post("/diagnosticos", json=[bom, mau], headers=cab).json()
    assert r["confirmados"] == [bom["id"]]
    assert r["rejeitados"] == [mau["id"]]


def test_uuid_de_outro_utilizador_nao_e_tomado(cliente):
    cab_a = registar(cliente, "842222224")
    cab_b = registar(cliente, "842222225")
    d = novo_diagnostico()
    cliente.post("/diagnosticos", json=[d], headers=cab_a)
    r = cliente.post("/diagnosticos", json=[d], headers=cab_b).json()
    assert r["rejeitados"] == [d["id"]]


def test_envio_de_imagem(cliente):
    cab = registar(cliente, "842222226")
    d = novo_diagnostico()
    cliente.post("/diagnosticos", json=[d], headers=cab)
    for _ in range(2):  # reenviar a imagem também não duplica
        r = cliente.post(f"/diagnosticos/{d['id']}/imagem", headers=cab,
                         files={"ficheiro": ("folha.jpg", jpeg(), "image/jpeg")})
        assert r.status_code == 201, r.text
    lista = cliente.get("/diagnosticos", headers=cab).json()
    assert lista[0]["tem_imagem"] is True


def test_imagem_de_outro_utilizador_proibida(cliente):
    cab_a = registar(cliente, "842222227")
    cab_b = registar(cliente, "842222228")
    d = novo_diagnostico()
    cliente.post("/diagnosticos", json=[d], headers=cab_a)
    r = cliente.post(f"/diagnosticos/{d['id']}/imagem", headers=cab_b,
                     files={"ficheiro": ("folha.jpg", jpeg(), "image/jpeg")})
    assert r.status_code == 403
