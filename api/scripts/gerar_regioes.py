"""Gera as regiões de Moçambique (províncias e distritos) e o mapa do painel de administração.

Fonte: geoBoundaries (gbOpen, MOZ), descarregar os ficheiros *_simplified.geojson de
    https://www.geoboundaries.org/api/current/gbOpen/MOZ/ADM1/   (províncias, OpenStreetMap, ODbL)
    https://www.geoboundaries.org/api/current/gbOpen/MOZ/ADM2/   (distritos, INE/OCHA 2019, CC BY 3.0 IGO)

O ADM1 junta a Cidade de Maputo à província de Maputo; aqui a «Cidade De Maputo» do ADM2 passa a
ser a 11.ª província. A província de cada distrito obtém-se pelo ponto central do distrito.

Uso (a partir da pasta api/):
    python -m scripts.gerar_regioes ADM1.geojson ADM2.geojson
Escreve app/regioes_mocambique.json e ../admin/public/mapa_mocambique.json.
"""

import json
import sys
from pathlib import Path

PASTA_API = Path(__file__).resolve().parent.parent

# Códigos ISO 3166-2:MZ
PROVINCIAS = {
    "Niassa": "MZ-A", "Cabo Delgado": "MZ-P", "Nampula": "MZ-N", "Zambézia": "MZ-Q",
    "Tete": "MZ-T", "Manica": "MZ-B", "Sofala": "MZ-S", "Inhambane": "MZ-I", "Gaza": "MZ-G",
    "Maputo": "MZ-L", "Cidade de Maputo": "MZ-MPM",
}
# Unidades do ADM2 que não são distritos moçambicanos (ilhas Likoma e Chizumulu, do Malawi).
EXCLUIR = {"Ilha Licom", "Ilha Risunodo"}


def bonito(nome: str) -> str:
    for de, para in ((" De ", " de "), (" Da ", " da "), ("-A-", "-a-")):
        nome = nome.replace(de, para)
    return nome


def poligonos(geometria):
    if geometria["type"] == "Polygon":
        return [geometria["coordinates"]]
    return geometria["coordinates"]


def area_e_centro(anel):
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(anel, anel[1:]):
        f = x0 * y1 - x1 * y0
        a += f
        cx += (x0 + x1) * f
        cy += (y0 + y1) * f
    if abs(a) < 1e-12:
        xs, ys = zip(*anel)
        return 0.0, (sum(xs) / len(xs), sum(ys) / len(ys))
    return abs(a) / 2, (cx / (3 * a), cy / (3 * a))


def dentro(ponto, anel):
    x, y = ponto
    resultado = False
    for (x0, y0), (x1, y1) in zip(anel, anel[1:]):
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            resultado = not resultado
    return resultado


def horario(anel):
    """O d3-geo (geometria esférica) quer o anel exterior no sentido horário; senão desenha o
    complemento (o mundo menos o distrito). Área com sinal > 0 = anti-horário -> inverter."""
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(anel, anel[1:]))
    return anel[::-1] if area > 0 else anel


def simplificar(anel, tolerancia):
    """Douglas-Peucker; mantém pelo menos 4 pontos para o anel continuar fechado."""
    if len(anel) < 5:
        return anel

    def dp(pontos):
        (x0, y0), (x1, y1) = pontos[0], pontos[-1]
        dx, dy = x1 - x0, y1 - y0
        norma = (dx * dx + dy * dy) ** 0.5 or 1e-12
        idx, dmax = 0, 0.0
        for i in range(1, len(pontos) - 1):
            px, py = pontos[i]
            d = abs(dy * px - dx * py + x1 * y0 - y1 * x0) / norma
            if d > dmax:
                idx, dmax = i, d
        if dmax <= tolerancia:
            return [pontos[0], pontos[-1]]
        return dp(pontos[: idx + 1])[:-1] + dp(pontos[idx:])

    meio = len(anel) // 2
    resultado = dp(anel[: meio + 1])[:-1] + dp(anel[meio:])
    return resultado if len(resultado) >= 4 else anel


def main(adm1: Path, adm2: Path) -> None:
    g1 = json.loads(adm1.read_text(encoding="utf-8"))
    g2 = json.loads(adm2.read_text(encoding="utf-8"))
    provincias_geo = [(f["properties"]["shapeName"], poligonos(f["geometry"])) for f in g1["features"]]

    distritos, mapa = [], []
    for f in g2["features"]:
        nome = f["properties"]["shapeName"]
        if nome in EXCLUIR:
            continue
        partes = poligonos(f["geometry"])
        _, centro = max((area_e_centro(p[0]) for p in partes), key=lambda t: t[0])
        if nome == "Cidade De Maputo":
            provincia = "Cidade de Maputo"
        else:
            provincia = next((n for n, polis in provincias_geo if any(dentro(centro, p[0]) for p in polis)), None)
            if provincia is None:  # ponto central fora (distrito costeiro): província mais próxima
                provincia = min(provincias_geo, key=lambda t: min(
                    (x - centro[0]) ** 2 + (y - centro[1]) ** 2 for p in t[1] for x, y in p[0]))[0]
        assert provincia in PROVINCIAS, (nome, provincia)
        distritos.append({"nome": bonito(nome), "provincia": PROVINCIAS[provincia]})

        coords = [[horario([[round(x, 3), round(y, 3)] for x, y in simplificar(anel, 0.008)]) for anel in p[:1]]
                  for p in partes]
        coords = [p for p in coords if len(p[0]) >= 4]
        mapa.append({"type": "Feature",
                     "properties": {"distrito": bonito(nome), "provincia": PROVINCIAS[provincia]},
                     "geometry": {"type": "MultiPolygon", "coordinates": coords}})

    distritos.sort(key=lambda d: (d["provincia"], d["nome"]))
    regioes = {
        "fonte": "geoBoundaries gbOpen MOZ: ADM2 (INE/OCHA ROSEA, 2019, CC BY 3.0 IGO); "
                 "ADM1 (OpenStreetMap, ODbL) para atribuir a província.",
        "provincias": [{"codigo": c, "nome": n} for n, c in PROVINCIAS.items()],
        "distritos": distritos,
    }
    (PASTA_API / "app" / "regioes_mocambique.json").write_text(
        json.dumps(regioes, ensure_ascii=False, indent=1), encoding="utf-8")
    destino = PASTA_API.parent / "admin" / "public" / "mapa_mocambique.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps({"type": "FeatureCollection", "features": mapa},
                                  ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    por_prov = {}
    for d in distritos:
        por_prov[d["provincia"]] = por_prov.get(d["provincia"], 0) + 1
    print(len(distritos), "distritos:", por_prov)
    print("mapa:", round(destino.stat().st_size / 1024), "KB")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
