"""Lê a versão em bruto (raw) do conjunto CCMT e gera data/metadados.csv.

Estrutura esperada (versão raw do CCMT):
    ml/data/raw/<qualquer subpasta>/Maize/<classe>/<imagem>.jpg
    ml/data/raw/<qualquer subpasta>/Cassava/<classe>/<imagem>.jpg

Cada linha do CSV corresponde a uma imagem, com as colunas:
    caminho   - caminho relativo a ml/data/raw (separador "/")
    cultura   - milho ou mandioca
    classe    - nome da classe no projecto (ver config.CLASSES)
    id_folha  - identificador da folha; no CCMT cada imagem é uma folha
    fonte     - origem da imagem (aqui sempre "ccmt")

Utilização (a partir da raiz do repositório):
    python ml/src/gerar_metadados.py
"""

import re
import sys

import pandas as pd
from PIL import Image

import config

# Pastas que só existem na versão aumentada do CCMT. Se aparecerem, o
# utilizador descarregou a versão errada e há risco de fuga de dados.
# Já na forma normalizada ("train_set" -> "train set").
PASTAS_PROIBIDAS = {"train set", "test set"}


def normalizar_nome(nome):
    """Põe o nome em minúsculas, retira dígitos finais e espaços repetidos."""
    nome = nome.lower().replace("_", " ")
    nome = re.sub(r"\d+$", "", nome)
    return " ".join(nome.split())


def imagem_valida(caminho):
    """Devolve True se o ficheiro abrir correctamente como imagem."""
    try:
        with Image.open(caminho) as img:
            img.verify()
        return True
    except Exception:
        return False


def encontrar_cultura(partes):
    """Procura no caminho a pasta da cultura e devolve (índice, cultura)."""
    for i, parte in enumerate(partes):
        cultura = config.CULTURAS.get(normalizar_nome(parte))
        if cultura is not None:
            return i, cultura
    return None, None


def recolher_imagens():
    linhas = []
    pastas_desconhecidas = set()
    corrompidas = []

    for caminho in sorted(config.PASTA_RAW.rglob("*")):
        if caminho.suffix.lower() not in config.EXTENSOES_IMAGEM:
            continue

        relativo = caminho.relative_to(config.PASTA_RAW)
        partes = relativo.parts

        nomes = {normalizar_nome(p) for p in partes}
        if nomes & PASTAS_PROIBIDAS or any("augmented" in n for n in nomes):
            sys.exit(
                f"ERRO: encontrada pasta da versão aumentada do CCMT em '{relativo}'.\n"
                "Use apenas a versão em bruto (Raw Data) para evitar fuga de dados."
            )

        i_cultura, cultura = encontrar_cultura(partes)
        if cultura is None:
            continue  # culturas que não usamos (caju, tomate)

        # A classe é a pasta imediatamente abaixo da cultura; é preciso
        # existir pelo menos cultura/classe/ficheiro.
        if len(partes) < i_cultura + 3:
            continue
        pasta_classe = partes[i_cultura + 1]
        classe = config.CLASSES[cultura].get(normalizar_nome(pasta_classe))
        if classe is None:
            pastas_desconhecidas.add(f"{cultura}/{pasta_classe}")
            continue

        if not imagem_valida(caminho):
            corrompidas.append(str(relativo))
            continue

        linhas.append({
            "caminho": relativo.as_posix(),
            "cultura": cultura,
            "classe": classe,
            "fonte": "ccmt",
        })

    if pastas_desconhecidas:
        sys.exit(
            "ERRO: pastas de classe sem correspondência em config.CLASSES:\n  "
            + "\n  ".join(sorted(pastas_desconhecidas))
        )

    if corrompidas:
        print(f"AVISO: {len(corrompidas)} imagens corrompidas foram ignoradas:")
        for c in corrompidas:
            print(f"  {c}")

    return pd.DataFrame(linhas)


def main():
    if not config.PASTA_RAW.exists():
        sys.exit(f"ERRO: a pasta {config.PASTA_RAW} não existe.")

    df = recolher_imagens()
    if df.empty:
        sys.exit(f"ERRO: nenhuma imagem de milho ou mandioca encontrada em {config.PASTA_RAW}.")

    # No CCMT não há informação sobre a folha de origem: cada imagem é
    # tratada como uma folha distinta. O id é único e estável entre execuções
    # porque as imagens são percorridas por ordem alfabética.
    df["id_folha"] = [
        f"ccmt_{cultura}_{i:06d}"
        for i, cultura in enumerate(df["cultura"])
    ]
    df = df[["caminho", "cultura", "classe", "id_folha", "fonte"]]

    config.PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.FICHEIRO_METADADOS, index=False)

    print(f"Metadados guardados em {config.FICHEIRO_METADADOS} ({len(df)} imagens).\n")
    print(df.groupby(["cultura", "classe"]).size().to_string())

    # Verifica se todas as classes esperadas têm pelo menos uma imagem.
    for cultura, mapa in config.CLASSES.items():
        esperadas = set(mapa.values())
        encontradas = set(df.loc[df["cultura"] == cultura, "classe"])
        em_falta = esperadas - encontradas
        if em_falta:
            print(f"\nAVISO: {cultura} sem imagens para: {', '.join(sorted(em_falta))}")


if __name__ == "__main__":
    main()
