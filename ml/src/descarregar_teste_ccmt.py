"""Descarrega do Mendeley Data só as imagens do conjunto de teste do CCMT.

Usa as divisões fixas (ml/data/divisoes/divisao_<cultura>.csv, semente 42) e grava
as imagens com o nome que o «Teste com fotografias» da app espera:
    <cultura>_<nnnn>_<classe>.jpg      (ex.: milho_0007_lagarta_do_cartucho.jpg)
Também escreve um mapa.csv (nome novo -> caminho original no CCMT).

Uso (a partir da pasta ml/):
    python -m src.descarregar_teste_ccmt                 # todas as imagens de teste
    python -m src.descarregar_teste_ccmt --por-classe 3  # amostra: 3 por classe
"""

import argparse
import csv
import json
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .config import PASTA_DIVISOES, PASTA_RAW

API = "https://data.mendeley.com/public-api/datasets/bwh3zbpkpv"  # CCMT, DOI 10.17632/bwh3zbpkpv.1
VERSAO = 1

# O Mendeley recusa (403) o User-Agent por omissão do urllib.
_opener = urllib.request.build_opener()
_opener.addheaders = [("User-Agent", "Mozilla/5.0 (PFC ISUTC; descarregar_teste_ccmt)")]
urllib.request.install_opener(_opener)


def _json(url: str):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def _pastas() -> dict[str, str]:
    """Caminho da pasta no CCMT (ex.: 'Raw Data/CCMT Dataset/Maize/healthy') -> id no Mendeley."""
    pastas = _json(f"{API}/folders/{VERSAO}")
    por_id = {p["id"]: p for p in pastas}

    def caminho(p):
        partes = [p["name"]]
        while p.get("parent_id") in por_id:
            p = por_id[p["parent_id"]]
            partes.insert(0, p["name"])
        return "/".join(partes)

    return {caminho(p): p["id"] for p in pastas}


def main() -> None:
    args = argparse.ArgumentParser()
    args.add_argument("--por-classe", type=int, default=0, help="0 = todas as imagens de teste")
    args.add_argument("--destino", type=Path, default=PASTA_RAW / "ccmt_teste")
    a = args.parse_args()

    pastas = _pastas()
    a.destino.mkdir(parents=True, exist_ok=True)
    tarefas, mapa = [], []
    for cultura in ("milho", "mandioca"):
        with open(PASTA_DIVISOES / f"divisao_{cultura}.csv", encoding="utf-8") as f:
            teste = [l for l in csv.DictReader(f) if l["subconjunto"] == "teste"]
        por_classe = defaultdict(list)
        for l in teste:
            por_classe[l["classe"]].append(l)

        n = 0
        for classe in sorted(por_classe):
            # A API só lista os primeiros 1000 ficheiros de cada pasta (sem paginação),
            # por isso nas pastas grandes parte das imagens de teste não está acessível.
            urls = {}
            for pasta in sorted({l["caminho"].rsplit("/", 1)[0] for l in por_classe[classe]}):
                for x in _json(f"{API}/files?folder_id={pastas[pasta]}&version={VERSAO}"):
                    urls[f"{pasta}/{x['filename']}"] = x["content_details"]["download_url"]
            acessiveis = [l for l in por_classe[classe] if l["caminho"] in urls]
            if len(acessiveis) < len(por_classe[classe]):
                print(f"{cultura}/{classe}: {len(por_classe[classe]) - len(acessiveis)} de "
                      f"{len(por_classe[classe])} imagens de teste fora do alcance da API")
            for l in acessiveis[: a.por_classe or None]:
                n += 1
                nome = f"{cultura}_{n:04d}_{classe}.jpg"
                tarefas.append((urls[l["caminho"]], a.destino / nome))
                mapa.append({"ficheiro": nome, "cultura": cultura, "classe": classe, "caminho_ccmt": l["caminho"]})

    def descarregar(t):
        url, destino = t
        if not destino.exists():
            urllib.request.urlretrieve(url, destino)

    with ThreadPoolExecutor(8) as ex:
        for i, _ in enumerate(ex.map(descarregar, tarefas), 1):
            if i % 100 == 0 or i == len(tarefas):
                print(f"{i}/{len(tarefas)}")

    with open(a.destino / "mapa.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ficheiro", "cultura", "classe", "caminho_ccmt"])
        w.writeheader()
        w.writerows(mapa)
    print(f"{len(tarefas)} imagens em {a.destino}")


if __name__ == "__main__":
    main()
