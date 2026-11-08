"""SMS (13), notificações por consulta da app (13b), campanhas de vigilância activa (12) e
calendário agrícola (10). Os distritos da Zambézia só são usados aqui.

O fornecedor de SMS (API Ola) é simulado com um transporte HTTP falso: os testes não enviam SMS.
"""

import base64
import json
from datetime import date, datetime, timedelta, timezone

import httpx

from conftest import entrar, novo_diagnostico, registar
from test_plataforma import ADMIN, criar_tecnico, distrito
from app.config import definicoes
from app.servicos import sms


def eu(cliente, cab):
    return cliente.get("/auth/eu", headers=cab).json()


def alerta(cliente, cab, distrito_id, **extra):
    r = cliente.post("/alertas", headers=cab, json={
        "titulo": "Lagarta em Mocuba", "mensagem": "Veja o funil das plantas jovens.", "nivel": "AVISO",
        "distrito_id": distrito_id, **extra})
    assert r.status_code == 201, r.text
    return r.json()


def sms_do_alerta(cliente, cab, alerta_id):
    return next(a for a in cliente.get("/alertas", headers=cab).json() if a["id"] == alerta_id)["sms"]


# --- SMS ----------------------------------------------------------------------------------

def test_numero_internacional():
    for numero in ("841234567", "84 123 4567", "+258841234567", "258841234567", "00258841234567"):
        assert sms.numero_internacional(numero) == "258841234567", numero


def test_texto_sms_curto():
    t = sms.texto_sms("Alerta", "Lagarta", "x" * 1000)
    assert t.startswith("[Alerta] Lagarta. ") and len(t) == definicoes.sms_max_caracteres and t.endswith("…")


def test_alerta_com_sms_simulado(cliente):
    tecnico = criar_tecnico(cliente, "890000001", area="Mocuba")
    for t in ("890000002", "890000003"):
        registar(cliente, t, area="Mocuba")
    mocuba = distrito(cliente, "Mocuba")["id"]
    assert cliente.get("/alertas/alcance", headers=tecnico, params={"distrito_id": mocuba}).json()["sms_simulacao"]

    sem = alerta(cliente, tecnico, mocuba)
    assert sem["sms"] is None
    com = alerta(cliente, tecnico, mocuba, enviar_sms=True)
    r = sms_do_alerta(cliente, tecnico, com["id"])
    assert r["total"] == 2 and r["simulado"] == 2 and r["enviado"] == 0 and r["simulacao"] is True
    reg = cliente.get("/gestao/auditoria", headers=entrar(cliente, *ADMIN), params={"accao": "alerta.enviar"}).json()
    assert any(json.loads(x["detalhes"])["depois"].get("sms") == 2 for x in reg["itens"] if x["entidade_id"] == str(com["id"]))


def test_alerta_com_sms_pelo_fornecedor(cliente, monkeypatch):
    tecnico = criar_tecnico(cliente, "890000011", area="Gurue")
    registar(cliente, "890000012", area="Gurue")
    registar(cliente, "890000013", area="Gurue")
    gurue = distrito(cliente, "Gurue")["id"]
    pedidos = []

    def responder(pedido: httpx.Request) -> httpx.Response:
        pedidos.append(pedido)
        corpo = json.loads(pedido.content)
        # O fornecedor aceita o primeiro número e devolve um erro para o segundo
        primeiro = corpo["messages"][0]["recipient"]
        return httpx.Response(200, json={"messages": [{"id": "ola-1", "recipient": primeiro, "status": "QUEUED"}],
                                         "errors": [{"code": "X", "message": "Número inválido"}]})

    cliente_real = httpx.AsyncClient
    monkeypatch.setattr(sms.httpx, "AsyncClient",
                        lambda **kw: cliente_real(transport=httpx.MockTransport(responder), **kw))
    monkeypatch.setattr(definicoes, "sms_chave", "chave-de-teste")
    monkeypatch.setattr(definicoes, "sms_provider_id", "prov-1")
    monkeypatch.setattr(definicoes, "sms_remetente", "AGRO")

    a = alerta(cliente, tecnico, gurue, enviar_sms=True)
    assert len(pedidos) == 1
    p = pedidos[0]
    corpo = json.loads(p.content)
    assert str(p.url) == "https://api.ola.pavulla.com/v1/messages/bulk"
    assert p.headers["Authorization"] == "Basic " + base64.b64encode(b"chave-de-teste:").decode()
    assert corpo["provider_id"] == "prov-1" and corpo["sender"] == "AGRO"
    assert {m["recipient"] for m in corpo["messages"]} == {"258890000012", "258890000013"}
    assert all(m["content"].startswith("[Alerta] Lagarta em Mocuba.") for m in corpo["messages"])
    r = sms_do_alerta(cliente, tecnico, a["id"])
    assert r["total"] == 2 and r["enviado"] == 1 and r["falhou"] == 1 and r["simulacao"] is False


def test_fornecedor_em_baixo(cliente, monkeypatch):
    tecnico = criar_tecnico(cliente, "890000021", area="Milange")
    registar(cliente, "890000022", area="Milange")
    cliente_real = httpx.AsyncClient
    monkeypatch.setattr(sms.httpx, "AsyncClient", lambda **kw: cliente_real(
        transport=httpx.MockTransport(lambda p: httpx.Response(503)), **kw))
    monkeypatch.setattr(definicoes, "sms_chave", "chave-de-teste")
    a = alerta(cliente, tecnico, distrito(cliente, "Milange")["id"], enviar_sms=True)
    assert sms_do_alerta(cliente, tecnico, a["id"])["falhou"] == 1


# --- Campanhas ------------------------------------------------------------------------------

def campanha(cliente, cab, **campos):
    base = {"titulo": "Vigilância da lagarta", "mensagem": "Fotografe 3 plantas de milho esta semana.",
            "cultura_id": "milho", "inicio": date.today().isoformat(),
            "fim": (date.today() + timedelta(days=7)).isoformat()}
    return cliente.post("/campanhas", headers=cab, json={**base, **campos})


def test_campanha_e_respostas(cliente):
    tecnico = criar_tecnico(cliente, "890000031", area="Lugela")
    lugela = distrito(cliente, "Lugela")["id"]
    a1, a2 = registar(cliente, "890000032", area="Lugela"), registar(cliente, "890000033", area="Lugela")
    fora = registar(cliente, "890000034", area="Pebane")
    lagarta = next(p for p in cliente.get("/patologias", params={"cultura": "milho"}).json()
                   if p["codigo"] == "lagarta_do_cartucho")
    mosaico = next(p for p in cliente.get("/patologias", params={"cultura": "mandioca"}).json()
                   if p["codigo"] == "mosaico")

    # Validações e limites de zona
    assert campanha(cliente, tecnico, distrito_id=distrito(cliente, "Pebane")["id"]).status_code == 403
    assert campanha(cliente, tecnico, distrito_id=lugela, fim="2020-01-01").status_code == 422
    assert campanha(cliente, tecnico, distrito_id=lugela,
                    fim=(date.today() + timedelta(days=90)).isoformat()).status_code == 422
    assert campanha(cliente, tecnico, distrito_id=lugela, patologia_id=mosaico["id"]).status_code == 422

    r = campanha(cliente, tecnico, distrito_id=lugela, patologia_id=lagarta["id"], enviar_sms=True)
    assert r.status_code == 201, r.text
    c = r.json()
    assert c["estado"] == "ACTIVA" and c["agricultores"] == 2 and c["responderam"] == 0
    assert c["sms"] is None or c["sms"]["total"] == 2  # os SMS são registados e simulados depois da resposta

    # O agricultor vê a campanha; o de fora não
    assert [x["respondeu"] for x in cliente.get("/campanhas/minhas", headers=a1).json()] == [False]
    assert cliente.get("/campanhas/minhas", headers=fora).json() == []

    # Responder: um diagnóstico de milho conta; um de mandioca não
    cliente.post("/diagnosticos", headers=a1, json=[novo_diagnostico("milho", "lagarta_do_cartucho")])
    cliente.post("/diagnosticos", headers=a2, json=[novo_diagnostico("mandioca", "saudavel")])
    assert [x["respondeu"] for x in cliente.get("/campanhas/minhas", headers=a1).json()] == [True]
    c = next(x for x in cliente.get("/campanhas", headers=tecnico).json() if x["id"] == c["id"])
    assert (c["responderam"], c["taxa_resposta"], c["diagnosticos"], c["casos_praga_doenca"],
            c["casos_patologia"]) == (1, 0.5, 1, 1, 1)
    assert c["sms"]["total"] == 2 and c["sms"]["simulado"] == 2

    # Cancelar: outro técnico não pode; o autor pode
    outro = criar_tecnico(cliente, "890000035", area="Pebane")
    assert cliente.post(f"/campanhas/{c['id']}/cancelar", headers=outro).status_code == 403
    assert cliente.post(f"/campanhas/{c['id']}/cancelar", headers=tecnico).status_code == 204
    assert cliente.get("/campanhas/minhas", headers=a1).json() == []
    antigas = cliente.get("/campanhas", headers=tecnico, params={"antigas": True}).json()
    assert next(x for x in antigas if x["id"] == c["id"])["estado"] == "CANCELADA"
    # O investigador lê; o agricultor não gere campanhas
    assert cliente.get("/campanhas", headers=a1).status_code == 403
    assert campanha(cliente, a1, distrito_id=lugela).status_code == 403


def test_campanha_agendada(cliente):
    tecnico = criar_tecnico(cliente, "890000041", area="Namarroi")
    registar(cliente, "890000042", area="Namarroi")
    inicio = date.today() + timedelta(days=3)
    r = campanha(cliente, tecnico, distrito_id=distrito(cliente, "Namarroi")["id"], inicio=inicio.isoformat(),
                 fim=(inicio + timedelta(days=5)).isoformat())
    assert r.status_code == 201 and r.json()["estado"] == "AGENDADA"
    assert cliente.get("/campanhas/minhas", headers=registar(cliente, "890000043", area="Namarroi")).json() == []


# --- Novidades (notificações sem Firebase) ---------------------------------------------------

def test_novidades_para_o_agricultor(cliente):
    tecnico = criar_tecnico(cliente, "890000051", area="Morrumbala")
    agr = registar(cliente, "890000052", area="Morrumbala")
    morrumbala = distrito(cliente, "Morrumbala")["id"]

    primeira = cliente.get("/novidades", headers=agr).json()
    assert (primeira["alertas"], primeira["validacoes"], primeira["visitas"], primeira["campanhas"]) == ([], [], [], [])
    desde = primeira["agora"]

    d = novo_diagnostico("milho", "mancha_da_folha")
    cliente.post("/diagnosticos", headers=agr, json=[d])
    alerta(cliente, tecnico, morrumbala)
    assert cliente.put(f"/diagnosticos/{d['id']}/validacao", headers=tecnico,
                       json={"classe_confirmada": "queima_da_folha"}).status_code == 200
    v = cliente.post("/visitas", headers=agr, json={"diagnostico_id": d["id"]}).json()
    agendada = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    assert cliente.patch(f"/visitas/{v['id']}", headers=tecnico,
                         json={"estado": "AGENDADA", "data_agendada": agendada}).status_code == 200
    assert campanha(cliente, tecnico, distrito_id=morrumbala).status_code == 201

    n = cliente.get("/novidades", headers=agr, params={"desde": desde}).json()
    assert [a["titulo"] for a in n["alertas"]] == ["Lagarta em Mocuba"]
    assert n["validacoes"] == [{"diagnostico_id": d["id"], "classe_confirmada": "queima_da_folha", "correcto": False}]
    assert [x["estado"] for x in n["visitas"]] == ["AGENDADA"]
    assert [x["titulo"] for x in n["campanhas"]] == ["Vigilância da lagarta"]

    # A consulta seguinte, a partir de `agora`, já não repete nada
    m = cliente.get("/novidades", headers=agr, params={"desde": n["agora"]}).json()
    assert (m["alertas"], m["validacoes"], m["visitas"], m["campanhas"]) == ([], [], [], [])
    # Outro agricultor, de outra zona, não recebe estas novidades
    outro = registar(cliente, "890000053", area="Pebane")
    o = cliente.get("/novidades", headers=outro, params={"desde": desde}).json()
    assert o["alertas"] == [] and o["validacoes"] == [] and o["campanhas"] == []


# --- Calendário agrícola ----------------------------------------------------------------------

def test_calendario_da_provincia(cliente):
    agr = registar(cliente, "890000061", area="Mocuba")  # Zambézia: Centro e Sul
    cal = cliente.get("/calendario", headers=agr).json()
    assert cal["provincia_codigo"] == "MZ-Q" and cal["regiao"] == "Centro e Sul" and len(cal["meses"]) == 12
    assert "Quelimane" in cal["sementeira"]
    novembro = cal["meses"][10]
    assert "Sementeira principal" in novembro["actividades"]
    lagarta = [a for a in novembro["avisos"] if a["classe"] == "lagarta_do_cartucho"]
    assert lagarta and lagarta[0]["confianca"] == "alta" and lagarta[0]["fontes"] == ["MASA2018"]
    assert lagarta[0]["patologia_nome"]
    fontes = {f["id"] for f in cal["fontes"]}
    assert {"FEWS2013", "MASA2018"} <= fontes and all(f["referencia"] for f in cal["fontes"])
    # Todos os avisos citam fontes que vêm na resposta
    assert {x for m in cal["meses"] for a in m["avisos"] for x in a["fontes"]} <= fontes

    norte = cliente.get("/calendario", headers=agr, params={"provincia": "MZ-P"}).json()
    assert norte["regiao"] == "Norte" and "Dezembro" in norte["sementeira"]
    assert "Sementeira" in norte["meses"][0]["actividades"][0]  # Janeiro: fim da sementeira no Norte
    # Administrador sem província tem de a indicar; província inexistente
    admin = entrar(cliente, *ADMIN)
    assert cliente.get("/calendario", headers=admin).status_code == 422
    assert cliente.get("/calendario", headers=admin, params={"provincia": "MZ-X"}).status_code == 404
    assert cliente.get("/calendario").status_code == 401
