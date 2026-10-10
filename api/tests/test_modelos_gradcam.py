"""RF12 (versões do modelo) e Grad-CAM."""

import io
import json

from PIL import Image

from conftest import entrar, novo_diagnostico, registar
from test_sincronizacao import jpeg

ADMIN = ("840000000", "admin-123")
CLASSES_MILHO = ["besouro_da_folha", "gafanhoto", "lagarta_do_cartucho", "listrado_do_milho",
                 "mancha_da_folha", "queima_da_folha", "saudavel"]


def test_publicar_e_descarregar_modelo(cliente):
    admin = entrar(cliente, *ADMIN)
    cab = registar(cliente, "844444441")
    assert cliente.get("/modelos/milho/ultima-versao", headers=cab).status_code == 404

    for versao in (1, 2):
        r = cliente.post("/modelos/milho", headers=admin,
                         data={"classes": json.dumps(CLASSES_MILHO), "acuracia_teste": "0.91"},
                         files={"ficheiro": ("m.tflite", f"conteudo-{versao}".encode(), "application/octet-stream")})
        assert r.status_code == 201, r.text
        assert r.json()["versao"] == versao

    ultima = cliente.get("/modelos/milho/ultima-versao", headers=cab).json()
    assert ultima["versao"] == 2 and ultima["classes"] == CLASSES_MILHO
    ficheiro = cliente.get(ultima["url_ficheiro"], headers=cab)
    assert ficheiro.status_code == 200 and ficheiro.content == b"conteudo-2"


def test_agricultor_nao_publica_modelos(cliente):
    cab = registar(cliente, "844444442")
    r = cliente.post("/modelos/milho", headers=cab, data={"classes": "[\"a\"]"},
                     files={"ficheiro": ("m.tflite", b"x", "application/octet-stream")})
    assert r.status_code == 403


def test_gradcam(cliente):
    """Gera um Grad-CAM com um modelo de teste com a mesma arquitectura do treino."""
    import keras
    from keras import layers

    from app.config import definicoes

    base = keras.applications.EfficientNetB0(include_top=False, weights=None, input_shape=(224, 224, 3))
    entradas = keras.Input((224, 224, 3))
    x = layers.GlobalAveragePooling2D(name="pooling")(base(entradas, training=False))
    x = layers.Dropout(0.3, name="dropout")(x)
    saidas = layers.Dense(len(CLASSES_MILHO), activation="softmax", name="classificacao")(x)
    keras.Model(entradas, saidas).save(definicoes.pasta_modelos / "modelo_milho.keras")

    cab = registar(cliente, "844444443")
    d = novo_diagnostico("milho", "mancha_da_folha")
    cliente.post("/diagnosticos", json=[d], headers=cab)

    # Sem imagem ainda: o Grad-CAM não é possível.
    assert cliente.get(f"/diagnosticos/{d['id']}/gradcam", headers=cab).status_code == 409

    cliente.post(f"/diagnosticos/{d['id']}/imagem", headers=cab,
                 files={"ficheiro": ("folha.jpg", jpeg(), "image/jpeg")})
    r = cliente.get(f"/diagnosticos/{d['id']}/gradcam", headers=cab)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "image/png"
    assert Image.open(io.BytesIO(r.content)).size == (300, 200)  # mesmo tamanho da foto

    # Outro agricultor não vê o Grad-CAM de um diagnóstico alheio.
    outro = registar(cliente, "844444444", area="Namaacha")
    assert cliente.get(f"/diagnosticos/{d['id']}/gradcam", headers=outro).status_code == 403
