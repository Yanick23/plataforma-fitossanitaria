"""Funcionalidades completadas a 08/11: mapa com filtro de confiança e tendência (1), decisão sobre os
sinais de surto (1b), exactidão por distrito (2b), divisão do conjunto de retreino (2c) e boletim de
uma zona à escolha (5). Os distritos de Sofala só são usados aqui."""

import csv
import io
import zipfile
from collections import Counter
from datetime import date, datetime, timedelta, timezone

from conftest import entrar, novo_diagnostico, registar
from test_plataforma import ADMIN, criar_tecnico, diagnostico_em, distrito
from test_plataforma_perfis import criar_conta
from app.servicos.validacoes import subconjunto_de


def diag(dias_atras: float, confianca: float, classe="lagarta_do_cartucho"):
    d = diagnostico_em(dias_atras, classe)
    d["confianca"] = confianca
    return d


# --- 1. Mapa: confiança e tendência -------------------------------------------------------

def test_mapa_com_confianca_e_tendencia(cliente):
    tecnico = criar_tecnico(cliente, "891000001", area="Dondo")
    agr = registar(cliente, "891000002", area="Dondo")
    cliente.post("/diagnosticos", headers=agr, json=[diag(0.1, 0.9), diag(0.2, 0.5), diag(10, 0.8)])
    desde = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    def dondo(**params):
        lista = cliente.get("/vigilancia/ocorrencias", headers=tecnico,
                            params={"cultura": "milho", "desde": desde, **params}).json()
        return next(o for o in lista if o["distrito"] == "Dondo")

    o = dondo()
    assert (o["total"], o["ultimos_7d"], o["anteriores_7d"]) == (3, 2, 1)
    assert dondo(confianca="alta")["total"] == 2   # 90% e 80%
    assert dondo(confianca="baixa")["total"] == 1  # 50%
    assert cliente.get("/vigilancia/ocorrencias", headers=tecnico, params={"confianca": "media"}).status_code == 422

    semanas = cliente.get("/vigilancia/tendencia", headers=tecnico, params={"cultura": "milho", "semanas": 4}).json()
    assert len(semanas) == 4 and sum(s["total"] for s in semanas) == 3
    hoje = datetime.now(timezone.utc).date()
    assert semanas[-1]["semana"] == (hoje - timedelta(days=hoje.weekday())).isoformat()
    assert semanas[-1]["total"] >= 2 and all(s["pragas_doencas"] == s["total"] for s in semanas)
    assert sum(s["total"] for s in cliente.get("/vigilancia/tendencia", headers=tecnico,
                                               params={"cultura": "milho", "confianca": "baixa"}).json()) == 1


# --- 1b. Confirmar ou descartar um sinal de surto -----------------------------------------

def test_decisao_sobre_sinal_de_surto(cliente):
    tecnico = criar_tecnico(cliente, "891000011", area="Buzi")
    agr = registar(cliente, "891000012", area="Buzi")
    cliente.post("/diagnosticos", headers=agr, json=[diag(0.5, 0.9), diag(1, 0.9), diag(1.5, 0.9)])
    buzi = distrito(cliente, "Buzi")["id"]

    def sinal():
        return next(s for s in cliente.get("/vigilancia/surtos", headers=tecnico).json() if s["distrito"] == "Buzi")

    assert sinal()["decisao"] is None
    decisao = {"distrito_id": buzi, "cultura_id": "milho", "classe": "lagarta_do_cartucho"}
    r = cliente.post("/vigilancia/surtos/decisao", headers=tecnico,
                     json={**decisao, "decisao": "DESCARTADO", "nota": "Fotografias repetidas da mesma planta."})
    assert r.status_code == 204
    s = sinal()
    assert (s["decisao"], s["decisao_nota"], s["decidido_por"]) == (
        "DESCARTADO", "Fotografias repetidas da mesma planta.", "Técnico 891000011")
    # Mudar de ideias: vale a decisão mais recente
    cliente.post("/vigilancia/surtos/decisao", headers=tecnico, json={**decisao, "decisao": "CONFIRMADO"})
    assert sinal()["decisao"] == "CONFIRMADO"

    assert cliente.post("/vigilancia/surtos/decisao", headers=tecnico,
                        json={**decisao, "decisao": "TALVEZ"}).status_code == 422
    outro = criar_tecnico(cliente, "891000013", area="Caia")
    assert cliente.post("/vigilancia/surtos/decisao", headers=outro,
                        json={**decisao, "decisao": "DESCARTADO"}).status_code == 403
    investigador = criar_conta(cliente, "891000014", "INVESTIGADOR")
    assert cliente.post("/vigilancia/surtos/decisao", headers=investigador,
                        json={**decisao, "decisao": "DESCARTADO"}).status_code == 403
    reg = cliente.get("/gestao/auditoria", headers=entrar(cliente, *ADMIN), params={"accao": "surto.decidir"}).json()
    assert reg["total"] >= 2


# --- 2b. Exactidão em campo por distrito --------------------------------------------------

def test_exactidao_por_distrito(cliente):
    tecnico = criar_tecnico(cliente, "891000021", area="Chemba")
    agr = registar(cliente, "891000022", area="Chemba")
    certo, errado = diag(1, 0.9), diag(1, 0.7, "mancha_da_folha")
    cliente.post("/diagnosticos", headers=agr, json=[certo, errado])
    cliente.put(f"/diagnosticos/{certo['id']}/validacao", headers=tecnico, json={"classe_confirmada": "lagarta_do_cartucho"})
    cliente.put(f"/diagnosticos/{errado['id']}/validacao", headers=tecnico, json={"classe_confirmada": "queima_da_folha"})
    ex = cliente.get("/validacoes/exactidao", headers=tecnico).json()
    assert ex["por_distrito"] == [{"distrito_id": distrito(cliente, "Chemba")["id"], "distrito": "Chemba",
                                   "validados": 2, "correctos": 1, "exactidao": 0.5}]
    # O administrador vê vários distritos
    nacional = cliente.get("/validacoes/exactidao", headers=entrar(cliente, *ADMIN)).json()["por_distrito"]
    assert any(d["distrito"] == "Chemba" for d in nacional)


# --- 2c. Divisão do conjunto de retreino -------------------------------------------------

def test_divisao_do_retreino():
    contas = Counter(subconjunto_de(f"grupo-{i}") for i in range(3000))
    assert set(contas) == {"treino", "validacao", "teste"}
    assert 0.66 < contas["treino"] / 3000 < 0.74 and 0.12 < contas["teste"] / 3000 < 0.18
    assert subconjunto_de("grupo-7") == subconjunto_de("grupo-7")  # fixa entre exportações


def test_exportacao_com_subconjunto(cliente):
    tecnico = criar_tecnico(cliente, "891000031", area="Cheringoma")
    agr = registar(cliente, "891000032", area="Cheringoma")
    mesmo_dia = [diag(0.1, 0.9), diag(0.2, 0.8)]
    cliente.post("/diagnosticos", headers=agr, json=mesmo_dia)
    for d in mesmo_dia:
        cliente.put(f"/diagnosticos/{d['id']}/validacao", headers=tecnico, json={"classe_confirmada": "lagarta_do_cartucho"})
    z = zipfile.ZipFile(io.BytesIO(cliente.get("/validacoes/exportar", headers=entrar(cliente, *ADMIN)).content))
    assert {"rotulos.csv", "LEIA-ME.txt"} <= set(z.namelist())
    linhas = list(csv.DictReader(io.StringIO(z.read("rotulos.csv").decode())))
    assert {"grupo", "subconjunto"} <= set(linhas[0])
    deste = [l for l in linhas if l["diagnostico_id"] in {d["id"] for d in mesmo_dia}]
    assert len(deste) == 2 and deste[0]["grupo"] == deste[1]["grupo"] and deste[0]["subconjunto"] == deste[1]["subconjunto"]
    assert len(deste[0]["grupo"]) == 12 and "891000032" not in deste[0]["grupo"]  # sem identificar o agricultor
    assert all(l["subconjunto"] in {"treino", "validacao", "teste"} for l in linhas)


# --- 5. Boletim de uma zona à escolha ----------------------------------------------------

def test_boletim_de_uma_zona_escolhida(cliente):
    coord = criar_conta(cliente, "891000041", "COORDENADOR", provincia_codigo="MZ-S")
    tecnico = criar_tecnico(cliente, "891000042", area="Gorongosa")
    agr = registar(cliente, "891000043", area="Gorongosa")
    cliente.post("/diagnosticos", headers=agr, json=[diag(1, 0.9), diag(2, 0.9)])
    hoje = date.today().isoformat()
    periodo = {"inicio": (date.today() - timedelta(days=29)).isoformat(), "fim": hoje}

    sofala = cliente.get("/gestao/boletim", headers=coord, params=periodo).json()
    gorongosa_id = distrito(cliente, "Gorongosa")["id"]
    so_gorongosa = cliente.get("/gestao/boletim", headers=coord, params={**periodo, "distrito_id": gorongosa_id}).json()
    assert "Gorongosa" in so_gorongosa["zona"] and so_gorongosa["diagnosticos"] == 2
    assert sofala["diagnosticos"] > so_gorongosa["diagnosticos"]  # Dondo, Buzi, Chemba… também contam

    # Fora da zona de quem pede: não
    assert cliente.get("/gestao/boletim", headers=coord, params={**periodo, "provincia": "MZ-L"}).status_code == 403
    assert cliente.get("/gestao/boletim", headers=tecnico, params={**periodo, "provincia": "MZ-S"}).status_code == 403
    assert cliente.get("/gestao/boletim", headers=tecnico,
                       params={**periodo, "distrito_id": distrito(cliente, "Dondo")["id"]}).status_code == 403
    assert cliente.get("/gestao/boletim", headers=coord, params={**periodo, "provincia": "MZ-X"}).status_code == 422
    # O administrador escolhe qualquer zona; o CSV segue a mesma escolha
    admin = entrar(cliente, *ADMIN)
    r = cliente.get("/gestao/boletim", headers=admin, params={**periodo, "provincia": "MZ-S"}).json()
    assert r["zona"] == "Província de Sofala" and r["diagnosticos"] == sofala["diagnosticos"]
    linhas = cliente.get("/gestao/boletim.csv", headers=admin,
                         params={**periodo, "distrito_id": gorongosa_id}).content.decode("utf-8-sig").splitlines()
    assert all(l.startswith("MZ-S,Gorongosa") for l in linhas[1:]) and len(linhas) > 1
