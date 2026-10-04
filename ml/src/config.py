"""Configuração partilhada pelos scripts do módulo ml.

Concentra num único sítio os caminhos, a semente aleatória, as proporções
da divisão e o mapeamento entre as pastas do CCMT e os nomes das classes.
"""

from pathlib import Path

# --- Caminhos (relativos à pasta ml/, para funcionarem em qualquer máquina) ---
PASTA_ML = Path(__file__).resolve().parent.parent
PASTA_DADOS = PASTA_ML / "data"
PASTA_RAW = PASTA_DADOS / "raw"
PASTA_DIVISOES = PASTA_DADOS / "divisoes"
FICHEIRO_METADADOS = PASTA_DADOS / "metadados.csv"

# --- Reprodutibilidade ---
RANDOM_STATE = 42

# --- Proporções da divisão treino/validação/teste ---
PROPORCAO_TREINO = 0.70
PROPORCAO_VALIDACAO = 0.15
PROPORCAO_TESTE = 0.15

# --- Extensões de imagem aceites ---
EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png"}

# --- Culturas: nome da pasta no CCMT -> nome usado no projecto ---
CULTURAS = {
    "maize": "milho",
    "cassava": "mandioca",
}

# --- Classes: nome da pasta no CCMT (normalizado) -> nome usado no projecto ---
# Os nomes das pastas são comparados em minúsculas, sem dígitos finais e com
# espaços simples (ver normalizar_nome em gerar_metadados.py).
CLASSES = {
    "milho": {
        "grasshoper": "gafanhoto",  # grafia original do CCMT
        "grasshopper": "gafanhoto",
        "fall armyworm": "lagarta_do_cartucho",
        "leaf beetle": "besouro_da_folha",
        "leaf blight": "queima_da_folha",
        "leaf spot": "mancha_da_folha",
        "streak virus": "listrado_do_milho",
        "healthy": "saudavel",
    },
    "mandioca": {
        "mosaic": "mosaico",
        "brown spot": "mancha_castanha",
        "bacterial blight": "mancha_bacteriana",
        "green mite": "acaro_verde",
        "healthy": "saudavel",
    },
}
