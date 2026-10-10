"""Grad-CAM (secção 4.6.6): mostra em que zona da folha o modelo se baseou.

Usa os modelos Keras originais (api/modelos/modelo_<cultura>.keras), com a
estrutura do notebook de treino: entrada → EfficientNetB0 ("efficientnetb0")
→ GlobalAveragePooling ("pooling") → Dropout → Dense softmax ("classificacao").
O mapa é calculado na camada "top_activation", a última convolucional da base.

O TensorFlow só é importado no primeiro pedido, para a API arrancar depressa.
"""

import io
import threading
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

from .config import definicoes

TAMANHO = 224
CAMADA_CONV = "top_activation"
_lock = threading.Lock()  # o TensorFlow não precisa de correr dois Grad-CAM ao mesmo tempo


class ModeloIndisponivel(Exception):
    pass


def caminho_modelo(cultura_id: str) -> Path:
    return definicoes.pasta_modelos / f"modelo_{cultura_id}.keras"


@lru_cache(maxsize=2)
def _carregar(cultura_id: str):
    import keras  # importação tardia (pesada)

    caminho = caminho_modelo(cultura_id)
    if not caminho.exists():
        raise ModeloIndisponivel(f"Falta o ficheiro {caminho.name} em api/modelos/")
    modelo = keras.models.load_model(caminho, compile=False)
    base = modelo.get_layer("efficientnetb0")
    # Da imagem até aos mapas de activação da última camada convolucional.
    extractor = keras.Model(base.inputs, base.get_layer(CAMADA_CONV).output)
    cabeca = [modelo.get_layer("pooling"), modelo.get_layer("classificacao")]  # sem dropout (inferência)
    return extractor, cabeca


def _ler_imagem(caminho: Path) -> tuple[np.ndarray, Image.Image]:
    from PIL import ImageOps

    original = ImageOps.exif_transpose(Image.open(caminho)).convert("RGB")
    # Igual ao treino e à app: esticar para 224×224 (bilinear) e manter 0–255, sem dividir por 255.
    redimensionada = original.resize((TAMANHO, TAMANHO), Image.BILINEAR)
    entrada = np.asarray(redimensionada, dtype=np.float32)[np.newaxis]
    return entrada, original


def gerar_gradcam(cultura_id: str, caminho_imagem: Path, indice_classe: int) -> bytes:
    """Devolve um PNG com o mapa de calor Grad-CAM sobreposto à fotografia."""
    import tensorflow as tf
    from matplotlib import colormaps

    extractor, (pooling, classificacao) = _carregar(cultura_id)
    entrada, original = _ler_imagem(caminho_imagem)

    with _lock:
        with tf.GradientTape() as fita:
            mapas = extractor(entrada, training=False)        # (1, 7, 7, 1280)
            fita.watch(mapas)
            probabilidades = classificacao(pooling(mapas))     # (1, n_classes)
            pontuacao = probabilidades[:, indice_classe]
        gradientes = fita.gradient(pontuacao, mapas)

    # Peso de cada mapa = média do gradiente (α_k^c); combinação ponderada + ReLU.
    pesos = tf.reduce_mean(gradientes, axis=(1, 2))           # (1, 1280)
    cam = tf.nn.relu(tf.reduce_sum(mapas * pesos[:, tf.newaxis, tf.newaxis, :], axis=-1))[0]
    cam = cam.numpy()
    if cam.max() > 0:
        cam = cam / cam.max()

    # Redimensiona o mapa para o tamanho da foto e sobrepõe com a escala "jet".
    largura, altura = original.size
    mapa = Image.fromarray(np.uint8(cam * 255)).resize((largura, altura), Image.BILINEAR)
    cores = colormaps["jet"](np.asarray(mapa) / 255.0)[..., :3]
    calor = Image.fromarray(np.uint8(cores * 255))
    sobreposta = Image.blend(original, calor, alpha=0.4)

    saida = io.BytesIO()
    sobreposta.save(saida, format="PNG")
    return saida.getvalue()
