"""Risco meteorológico (9): regras sobre a previsão, cache na base e funcionamento sem internet.

A Open-Meteo é substituída por uma previsão simulada (os testes não dependem da internet).
Os distritos de Niassa e Tete só são usados aqui.
"""

from datetime import date, timedelta

import httpx
import pytest

from conftest import entrar, registar
from test_plataforma import ADMIN, criar_tecnico, distrito
from test_plataforma_perfis import criar_conta
from app.config import definicoes
from app.servicos import meteorologia


def horaria(temp=24.0, hr=95.0, chuva=0.0, horas_humidas=24, dias=7) -> dict:
    """Previsão horária simulada: `horas_humidas` horas por dia com a humidade `hr`, o resto a 60%."""
    inicio = date(2026, 11, 4)
    t, temperatura, humidade, precipitacao = [], [], [], []
    for d in range(dias):
        for h in range(24):
            t.append(f"{inicio + timedelta(days=d)}T{h:02d}:00")
            temperatura.append(temp)
            humidade.append(hr if h < horas_humidas else 60.0)
            precipitacao.append(chuva)
    return {"time": t, "temperature_2m": temperatura, "relative_humidity_2m": humidade, "precipitation": precipitacao}


class OpenMeteoFalsa:
    def __init__(self, previsao: dict | None = None, falhar: bool = False):
        self.previsao, self.falhar, self.pedidos = previsao, falhar, 0

    async def __call__(self, coordenadas):
        self.pedidos += 1
        if self.falhar:
            raise httpx.ConnectError("sem rede")
        return [self.previsao for _ in coordenadas]


def risco(cliente, cab) -> dict:
    r = cliente.get("/vigilancia/risco-meteorologico", headers=cab)
    assert r.status_code == 200, r.text
    return r.json()


def classes(resposta) -> dict[str, str]:
    return {i["classe"]: i["nivel"] for i in resposta["itens"]}


def test_resumo_diario_ignora_dia_incompleto():
    h = horaria(dias=2)
    for k in h:
        h[k] = h[k][:30]  # 1 dia completo + 6 horas
    dias = meteorologia.resumir(h)
    assert len(dias) == 1 and dias[0].horas_hr90 == 24 and dias[0].temperatura_media == 24


def test_semana_humida_e_semana_seca(cliente, monkeypatch):
    tecnico = criar_tecnico(cliente, "880000001", area="Cuamba")
    registar(cliente, "880000002", area="Cuamba")
    monkeypatch.setattr(definicoes, "meteo_validade_horas", 0)  # pede sempre previsão nova

    # Semana húmida e amena: queima da folha e mancha cinzenta em risco alto; ácaro não
    monkeypatch.setattr(meteorologia, "descarregar", OpenMeteoFalsa(horaria(temp=24, hr=96, chuva=0.5)))
    r = risco(cliente, tecnico)
    assert r["distritos_com_agricultores"] == 1 and r["distritos_avaliados"] == 1 and r["erro"] is None
    c = classes(r)
    assert c["queima_da_folha"] == "ALTO" and c["mancha_da_folha"] == "ALTO" and c["mancha_castanha"] == "ALTO"
    assert "acaro_verde" not in c
    item = next(i for i in r["itens"] if i["classe"] == "queima_da_folha")
    assert item["distrito"] == "Cuamba" and item["dias_favoraveis"] == 7 and item["patologia_id"] > 0
    assert {g["classe"] for g in r["regras"]} == {"queima_da_folha", "mancha_da_folha", "mancha_castanha", "acaro_verde"}
    assert all(g["fontes"] for g in r["regras"])

    # Humidade só de noite (6 h): nenhuma doença de folha; semana seca: ácaro verde em risco alto
    monkeypatch.setattr(meteorologia, "descarregar", OpenMeteoFalsa(horaria(temp=27, hr=95, horas_humidas=6)))
    assert classes(risco(cliente, tecnico)) == {"acaro_verde": "ALTO"}

    # Frio demais para a mancha cinzenta (18 °C), mas não para a queima da folha
    monkeypatch.setattr(meteorologia, "descarregar", OpenMeteoFalsa(horaria(temp=18, hr=96, chuva=2)))
    c = classes(risco(cliente, tecnico))
    assert c.get("queima_da_folha") == "ALTO" and "mancha_da_folha" not in c and "mancha_castanha" not in c


def test_previsao_guardada_e_sem_internet(cliente, monkeypatch):
    tecnico = criar_tecnico(cliente, "880000011", distrito_id=distrito(cliente, "Angonia")["id"])
    registar(cliente, "880000012", area="Angonia")

    # Sem internet e sem previsão guardada: nada a mostrar, mas diz porquê
    monkeypatch.setattr(meteorologia, "descarregar", OpenMeteoFalsa(falhar=True))
    r = risco(cliente, tecnico)
    assert r["itens"] == [] and r["distritos_avaliados"] == 0 and "Open-Meteo" in r["erro"]

    # Com rede: pede uma vez e guarda; o pedido seguinte usa a previsão guardada
    open_meteo = OpenMeteoFalsa(horaria(temp=24, hr=96))
    monkeypatch.setattr(meteorologia, "descarregar", open_meteo)
    r1, r2 = risco(cliente, tecnico), risco(cliente, tecnico)
    assert open_meteo.pedidos == 1 and r1["itens"] == r2["itens"] and r2["previsao_mais_antiga"]

    # A previsão passou de validade e a rede caiu: mostra a guardada e avisa
    monkeypatch.setattr(definicoes, "meteo_validade_horas", 0)
    monkeypatch.setattr(meteorologia, "descarregar", OpenMeteoFalsa(falhar=True))
    r3 = risco(cliente, tecnico)
    assert r3["erro"] and classes(r3) == classes(r1)


def test_quem_ve_o_risco(cliente, monkeypatch):
    monkeypatch.setattr(meteorologia, "descarregar", OpenMeteoFalsa(horaria()))
    assert cliente.get("/vigilancia/risco-meteorologico", headers=registar(cliente, "880000021")).status_code == 403
    investigador = criar_conta(cliente, "880000022", "INVESTIGADOR")
    r = risco(cliente, investigador)
    assert r["distritos_com_agricultores"] >= 2  # o país todo
    # O técnico só vê os distritos da sua zona
    tecnico = criar_tecnico(cliente, "880000023", area="Cuamba")
    assert {i["distrito"] for i in risco(cliente, tecnico)["itens"]} <= {"Cuamba"}
    assert risco(cliente, entrar(cliente, *ADMIN))["distritos_com_agricultores"] >= 2


@pytest.mark.parametrize("chuva_hora, esperado", [(0.0, "ALTO"), (0.05, "MEDIO"), (0.1, None)])
def test_limiares_do_acaro_verde(chuva_hora, esperado):
    # 7 dias x 24 h: 0 mm -> alto (< 2 mm); 8,4 mm -> médio (< 10 mm); 16,8 mm -> sem risco
    a = meteorologia._acaro_verde(meteorologia.resumir(horaria(hr=50, chuva=chuva_hora)))
    assert (a.nivel if a else None) == esperado
