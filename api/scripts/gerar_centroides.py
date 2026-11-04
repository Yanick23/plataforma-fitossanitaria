"""Ponto central de cada distrito (para pedir a previsão do tempo à Open-Meteo).

Lê o mapa do painel (../admin/public/mapa_mocambique.json, gerado por gerar_regioes.py) e
escreve app/centroides_distritos.json. O centro é a média dos centróides dos polígonos do
distrito, pesada pela área; chega para a previsão, que tem uma grelha de cerca de 10 km.

Uso (a partir da pasta api/):
    python -m scripts.gerar_centroides
"""

import json

from scripts.gerar_regioes import PASTA_API, area_e_centro, poligonos

MAPA = PASTA_API.parent / "admin" / "public" / "mapa_mocambique.json"
SAIDA = PASTA_API / "app" / "centroides_distritos.json"


def centro(geometria) -> tuple[float, float]:
    total = sx = sy = 0.0
    for poligono in poligonos(geometria):
        area, (x, y) = area_e_centro(poligono[0])  # anel exterior
        total += area
        sx += x * area
        sy += y * area
    return sx / total, sy / total


def main() -> None:
    mapa = json.loads(MAPA.read_text(encoding="utf-8"))
    linhas = []
    for f in mapa["features"]:
        lon, lat = centro(f["geometry"])
        linhas.append({"nome": f["properties"]["distrito"], "provincia": f["properties"]["provincia"],
                       "latitude": round(lat, 4), "longitude": round(lon, 4)})
    linhas.sort(key=lambda d: (d["provincia"], d["nome"]))
    SAIDA.write_text(json.dumps({"fonte": "Centro de cada distrito calculado a partir de " + MAPA.name,
                                 "distritos": linhas}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(linhas)} distritos -> {SAIDA}")


if __name__ == "__main__":
    main()
