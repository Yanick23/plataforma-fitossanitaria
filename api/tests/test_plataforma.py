"""Plataforma (fase 1): regiões, zonas, alertas, validação, visitas, vigilância, gestão e auditoria."""

import io
import uuid
import zipfile
from datetime import datetime, timedelta, timezone

from conftest import entrar, novo_diagnostico, registar
from test_sincronizacao import jpeg

ADMIN = ("840000000", "admin-123")


def distrito(cliente, nome: str) -> dict:
    return next(d for d in cliente.get("/distritos").json() if d["nome"] == nome)


def criar_tecnico(cliente, telefone: str, **zona) -> dict:
    admin = entrar(cliente, *ADMIN)
    r = cliente.post("/utilizadores", headers=admin, json={
        "nome": f"Técnico {telefone}", "telefone": telefone, "palavra_passe": "tecnico123",
        "perfil": "TECNICO", **zona})
    assert r.status_code == 201, r.text
    return entrar(cliente, telefone, "tecnico123")


def diagnostico_em(dias_atras: float, classe: str = "lagarta_do_cartucho", cultura: str = "milho") -> dict:
    d = novo_diagnostico(cultura, classe)
    d["data"] = (datetime.now(timezone.utc) - timedelta(days=dias_atras)).isoformat()
    return d


# --- Regiões e zona das contas --------------------------------------------------

def test_regioes_de_mocambique(cliente):
    provincias = cliente.get("/provincias").json()
    assert len(provincias) == 11
    assert {"codigo": "MZ-MPM", "nome": "Cidade de Maputo"} in provincias
    assert len(cliente.get("/distritos").json()) == 157
    maputo = {d["nome"] for d in cliente.get("/distritos", params={"provincia": "MZ-L"}).json()}
    assert {"Boane", "Manhiça", "Namaacha", "Cidade da Matola"} <= maputo


def test_registo_liga_a_area_ao_distrito(cliente):
    r = cliente.post("/auth/registar", json={"nome": "Agricultora", "telefone": "850000001",
                                             "palavra_passe": "segredo123", "area": "chokwe"})
    u = r.json()["utilizador"]
    assert u["distrito_id"] == distrito(cliente, "Chokwe")["id"] and u["provincia_codigo"] == "MZ-G"

    d = distrito(cliente, "Moamba")
    r = cliente.post("/auth/registar", json={"nome": "Agricultor", "telefone": "850000002",
                                             "palavra_passe": "segredo123", "distrito_id": d["id"]})
    assert r.json()["utilizador"]["area"] == "Moamba"
    r = cliente.post("/auth/registar", json={"nome": "X", "telefone": "850000003",
                                             "palavra_passe": "segredo123", "distrito_id": 99999})
    assert r.status_code == 422


def test_conta_desactivada_nao_entra(cliente):
    cab = registar(cliente, "850000010")
    eu = cliente.get("/auth/eu", headers=cab).json()
    admin = entrar(cliente, *ADMIN)
    r = cliente.patch(f"/gestao/utilizadores/{eu['id']}", headers=admin, json={"activo": False})
    assert r.status_code == 200 and r.json()["activo"] is False
    assert cliente.get("/auth/eu", headers=cab).status_code == 403
    r = cliente.post("/auth/login", json={"telefone": "850000010", "palavra_passe": "segredo123"})
    assert r.status_code == 403
    # O administrador não se pode desactivar a si próprio
    eu_admin = cliente.get("/auth/eu", headers=admin).json()
    assert cliente.patch(f"/gestao/utilizadores/{eu_admin['id']}", headers=admin,
                         json={"activo": False}).status_code == 409


def test_administrador_promove_e_repoe_palavra_passe(cliente):
    cab = registar(cliente, "850000020", area="Boane")
    uid = cliente.get("/auth/eu", headers=cab).json()["id"]
    admin = entrar(cliente, *ADMIN)
    r = cliente.patch(f"/gestao/utilizadores/{uid}", headers=admin,
                      json={"perfil": "TECNICO", "distrito_id": distrito(cliente, "Namaacha")["id"]})
    assert r.json()["perfil"] == "TECNICO" and r.json()["distrito_nome"] == "Namaacha"
    assert cliente.post(f"/gestao/utilizadores/{uid}/palavra-passe", headers=admin,
                        json={"palavra_passe": "nova-senha"}).status_code == 204
    entrar(cliente, "850000020", "nova-senha")
    accoes = {a["accao"] for a in cliente.get("/gestao/auditoria", headers=admin).json()["itens"]}
    assert {"utilizador.actualizar", "utilizador.repor_palavra_passe"} <= accoes
    assert cliente.get("/gestao/auditoria", headers=cab).status_code == 403


def test_tecnico_so_ve_agricultores_da_sua_zona(cliente):
    tecnico = criar_tecnico(cliente, "850000030", area="Magude")
    registar(cliente, "850000031", area="Magude")
    registar(cliente, "850000032", area="Matutuine")
    telefones = {u["telefone"] for u in cliente.get("/gestao/utilizadores", headers=tecnico).json()["itens"]}
    assert "850000031" in telefones and "850000032" not in telefones
    assert cliente.patch("/gestao/utilizadores/1", headers=tecnico, json={"activo": False}).status_code == 403


# --- Alertas -------------------------------------------------------------------

def test_alertas_por_zona(cliente):
    d_marracuene = distrito(cliente, "Marracuene")
    d_manhica = distrito(cliente, "Manhiça")
    tecnico = criar_tecnico(cliente, "850000040", distrito_id=d_marracuene["id"])
    no_distrito = registar(cliente, "850000041", area="Marracuene")
    na_provincia = registar(cliente, "850000042", area="Manhiça")
    noutra_provincia = registar(cliente, "850000043", area="Chibuto")

    # Alcance e permissões do técnico
    r = cliente.get("/alertas/alcance", headers=tecnico, params={"distrito_id": d_marracuene["id"]})
    assert r.json() == {"zona": "Distrito de Marracuene", "destinatarios": 1}
    assert cliente.get("/alertas/alcance", headers=tecnico,
                       params={"distrito_id": d_manhica["id"]}).status_code == 403
    assert cliente.post("/alertas", headers=tecnico,
                        json={"titulo": "Nacional", "mensagem": "Para todo o país"}).status_code == 403

    lagarta = next(p for p in cliente.get("/patologias", params={"cultura": "milho"}).json()
                   if p["codigo"] == "lagarta_do_cartucho")
    r = cliente.post("/alertas", headers=tecnico, json={
        "titulo": "Lagarta-do-funil em Marracuene", "mensagem": "Inspeccione o funil das plantas novas.",
        "nivel": "URGENTE", "patologia_id": lagarta["id"], "distrito_id": d_marracuene["id"]})
    assert r.status_code == 201, r.text
    distrital = r.json()
    assert distrital["cultura_id"] == "milho" and distrital["destinatarios"] == 1 and distrital["lidos"] == 0

    admin = entrar(cliente, *ADMIN)
    provincial = cliente.post("/alertas", headers=admin, json={
        "titulo": "Província de Maputo", "mensagem": "Época de sementeira.", "provincia_codigo": "MZ-L"}).json()
    nacional = cliente.post("/alertas", headers=admin, json={
        "titulo": "Aviso nacional", "mensagem": "Actualize a app.", "nivel": "INFORMACAO"}).json()
    assert nacional["zona"] == "Todo o país"

    def ids(cab):
        return {a["id"] for a in cliente.get("/alertas/meus", headers=cab).json()}

    assert {distrital["id"], provincial["id"], nacional["id"]} <= ids(no_distrito)
    assert distrital["id"] not in ids(na_provincia) and provincial["id"] in ids(na_provincia)
    assert ids(noutra_provincia) & {distrital["id"], provincial["id"]} == set()
    assert nacional["id"] in ids(noutra_provincia)

    # Leitura e arquivo
    assert cliente.post(f"/alertas/{distrital['id']}/lido", headers=no_distrito).status_code == 204
    assert cliente.post(f"/alertas/{distrital['id']}/lido", headers=noutra_provincia).status_code == 404
    lista = {a["id"]: a for a in cliente.get("/alertas", headers=tecnico).json()}
    assert lista[distrital["id"]]["lidos"] == 1
    meu = next(a for a in cliente.get("/alertas/meus", headers=no_distrito).json() if a["id"] == distrital["id"])
    assert meu["lido"] is True
    assert cliente.post(f"/alertas/{distrital['id']}/arquivar", headers=tecnico).status_code == 204
    assert distrital["id"] not in ids(no_distrito)


def test_alerta_expirado_nao_chega(cliente):
    admin = entrar(cliente, *ADMIN)
    passado = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    r = cliente.post("/alertas", headers=admin, json={
        "titulo": "Velho", "mensagem": "Já expirou", "expira_em": passado})
    assert r.status_code == 422 and "validade" in r.json()["detail"]


# --- Validação e exactidão em campo ---------------------------------------------

def test_validacao_pelo_tecnico(cliente):
    tecnico = criar_tecnico(cliente, "850000050", area="Cidade de Xai-Xai")
    fora = criar_tecnico(cliente, "850000051", area="Mabalane")
    cab = registar(cliente, "850000052", area="Xai-Xai")
    certo, errado = novo_diagnostico(), novo_diagnostico(classe="gafanhoto")
    cliente.post("/diagnosticos", json=[certo, errado], headers=cab)
    cliente.post(f"/diagnosticos/{certo['id']}/imagem", headers=cab,
                 files={"ficheiro": ("f.jpg", jpeg(), "image/jpeg")})

    assert cliente.put(f"/diagnosticos/{certo['id']}/validacao", headers=fora,
                       json={"classe_confirmada": "lagarta_do_cartucho"}).status_code == 403
    assert cliente.put(f"/diagnosticos/{certo['id']}/validacao", headers=tecnico,
                       json={"classe_confirmada": "mosaico"}).status_code == 422
    r = cliente.put(f"/diagnosticos/{certo['id']}/validacao", headers=tecnico,
                    json={"classe_confirmada": "lagarta_do_cartucho"})
    assert r.status_code == 200 and r.json()["validacao"] == "CONFIRMADO"
    r = cliente.put(f"/diagnosticos/{errado['id']}/validacao", headers=tecnico,
                    json={"classe_confirmada": "besouro_da_folha", "nota": "Furos típicos do besouro."})
    assert r.json()["validacao"] == "CORRIGIDO" and r.json()["tecnico_nome"] == "Técnico 850000050"

    # O agricultor vê a correcção na sincronização
    meus = {d["id"]: d for d in cliente.get("/diagnosticos", headers=cab).json()}
    assert meus[errado["id"]]["classe_confirmada"] == "besouro_da_folha"
    assert meus[errado["id"]]["nota_tecnico"] == "Furos típicos do besouro."

    ex = cliente.get("/validacoes/exactidao", headers=tecnico).json()
    assert ex["validados"] == 2 and ex["correctos"] == 1 and ex["exactidao"] == 0.5
    assert {"cultura_id": "milho", "prevista": "gafanhoto", "confirmada": "besouro_da_folha",
            "total": 1} in ex["confusoes"]

    # Fila de validação: só os pendentes
    pendentes = cliente.get("/gestao/diagnosticos", headers=tecnico, params={"validacao": "PENDENTE"}).json()
    assert {certo["id"], errado["id"]} & {d["id"] for d in pendentes["itens"]} == set()

    # Exportação para retreino (só administrador)
    assert cliente.get("/validacoes/exportar", headers=tecnico).status_code == 403
    r = cliente.get("/validacoes/exportar", headers=entrar(cliente, *ADMIN))
    z = zipfile.ZipFile(io.BytesIO(r.content))
    assert "rotulos.csv" in z.namelist()
    assert f"milho/lagarta_do_cartucho/{certo['id']}.jpg" in z.namelist()


# --- Pedidos de visita ------------------------------------------------------------

def test_pedido_de_visita(cliente):
    tecnico = criar_tecnico(cliente, "850000060", area="Massingir")
    cab = registar(cliente, "850000061", area="Massingir")
    d = novo_diagnostico()
    assert cliente.post("/visitas", headers=cab, json={"diagnostico_id": d["id"]}).status_code == 404
    cliente.post("/diagnosticos", json=[d], headers=cab)
    r = cliente.post("/visitas", headers=cab, json={"diagnostico_id": d["id"], "mensagem": "Muitas lagartas."})
    assert r.status_code == 201 and r.json()["estado"] == "PENDENTE" and r.json()["distrito_nome"] == "Massingir"
    vid = r.json()["id"]
    assert cliente.post("/visitas", headers=cab, json={"diagnostico_id": d["id"]}).status_code == 409

    assert vid in {v["id"] for v in cliente.get("/visitas", headers=tecnico).json()}
    assert cliente.patch(f"/visitas/{vid}", headers=tecnico, json={"estado": "AGENDADA"}).status_code == 422
    quando = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    r = cliente.patch(f"/visitas/{vid}", headers=tecnico, json={"estado": "AGENDADA", "data_agendada": quando})
    assert r.json()["estado"] == "AGENDADA" and r.json()["tecnico_nome"] == "Técnico 850000060"
    r = cliente.patch(f"/visitas/{vid}", headers=tecnico, json={"estado": "RESOLVIDA", "notas_tecnico": "Tratado."})
    assert r.json()["estado"] == "RESOLVIDA"
    assert cliente.patch(f"/visitas/{vid}", headers=tecnico, json={"estado": "PENDENTE"}).status_code == 409
    assert cliente.get("/visitas/minhas", headers=cab).json()[0]["notas_tecnico"] == "Tratado."

    fora = criar_tecnico(cliente, "850000062", area="Guija")
    assert cliente.patch(f"/visitas/{vid}", headers=fora, json={"notas_tecnico": "x"}).status_code == 404


# --- Vigilância e painel -----------------------------------------------------------

def test_deteccao_de_surto(cliente):
    tecnico = criar_tecnico(cliente, "850000070", area="Govuro")
    cab = registar(cliente, "850000071", area="Govuro")
    # Base: 1 caso por semana nas 4 semanas anteriores; agora: 6 casos nos últimos 7 dias
    lote = [diagnostico_em(d) for d in (10, 17, 24, 31)] + [diagnostico_em(d / 2) for d in range(1, 7)]
    lote.append(diagnostico_em(1, classe="saudavel"))  # folhas saudáveis não contam
    assert len(cliente.post("/diagnosticos", json=lote, headers=cab).json()["confirmados"]) == len(lote)

    surtos = cliente.get("/vigilancia/surtos", headers=tecnico).json()
    assert len(surtos) == 1
    s = surtos[0]
    assert (s["distrito"], s["classe"], s["casos_recentes"], s["media_anterior"]) == \
        ("Govuro", "lagarta_do_cartucho", 6, 1.0)
    assert s["nivel"] == "URGENTE" and s["razao"] == 6.0

    mapa = cliente.get("/vigilancia/ocorrencias", headers=tecnico, params={"classe": "lagarta_do_cartucho"}).json()
    assert mapa == [{"distrito_id": s["distrito_id"], "distrito": "Govuro", "provincia_codigo": "MZ-I", "total": 10}]


def test_resumo_e_diagnosticos_da_gestao(cliente):
    tecnico = criar_tecnico(cliente, "850000080", area="Funhalouro")
    cab = registar(cliente, "850000081", area="Funhalouro")
    baixo = novo_diagnostico()
    baixo["confianca"] = 0.41
    cliente.post("/diagnosticos", json=[novo_diagnostico(), baixo], headers=cab)

    r = cliente.get("/gestao/resumo", headers=tecnico).json()
    assert r["zona"] == "Funhalouro, Inhambane"
    assert r["agricultores"] == 1 and r["diagnosticos"] == 2 and r["confianca_baixa_30d"] == 1
    assert len(r["por_dia"]) == 31 and r["por_distrito"][0]["distrito"] == "Funhalouro"

    pagina = cliente.get("/gestao/diagnosticos", headers=tecnico, params={"ordem": "confianca", "limite": 1}).json()
    assert pagina["total"] == 2 and pagina["itens"][0]["id"] == baixo["id"]
    assert pagina["itens"][0]["patologia_nome"].startswith("Lagarta") and pagina["itens"][0]["tipo"] == "PRAGA"

    admin = entrar(cliente, *ADMIN)
    assert cliente.get("/gestao/resumo", headers=admin).json()["zona"] == "Moçambique"
    assert cliente.get("/gestao/resumo", headers=cab).status_code == 403


def test_imagem_do_diagnostico(cliente):
    cab = registar(cliente, "850000090", area="Inharrime")
    outro = registar(cliente, "850000091", area="Inharrime")
    d = novo_diagnostico()
    cliente.post("/diagnosticos", json=[d], headers=cab)
    assert cliente.get(f"/diagnosticos/{d['id']}/imagem", headers=cab).status_code == 404
    cliente.post(f"/diagnosticos/{d['id']}/imagem", headers=cab, files={"ficheiro": ("f.jpg", jpeg(), "image/jpeg")})
    r = cliente.get(f"/diagnosticos/{d['id']}/imagem", headers=cab)
    assert r.status_code == 200 and r.content[:2] == b"\xff\xd8"
    assert cliente.get(f"/diagnosticos/{d['id']}/imagem", headers=outro).status_code == 403


def test_auditoria_do_catalogo_e_modelos(cliente):
    admin = entrar(cliente, *ADMIN)
    p = cliente.get("/patologias", params={"cultura": "mandioca"}).json()[0]
    cliente.put(f"/patologias/{p['id']}", headers=admin, json={
        "nome_local": p["nome_local"], "nome_cientifico": p["nome_cientifico"], "tipo": p["tipo"],
        "recomendacao": "Recomendação auditada."})
    itens = cliente.get("/gestao/auditoria", headers=admin, params={"accao": "patologia"}).json()["itens"]
    assert itens[0]["accao"] == "patologia.actualizar" and "Recomendação auditada." in itens[0]["detalhes"]
    assert itens[0]["utilizador_nome"] == "Administrador"


# --- Migração de uma base criada antes do Alembic --------------------------------

def test_migracao_de_base_antiga(tmp_path):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect, text

    from app.config import PASTA_API
    from app.database import migrar

    motor = create_engine(f"sqlite:///{(tmp_path / 'antiga.db').as_posix()}")
    cfg = Config(str(PASTA_API / "alembic.ini"))
    cfg.set_main_option("script_location", str(PASTA_API / "migracoes"))
    with motor.begin() as ligacao:  # base "antiga": esquema 0001, sem tabela alembic_version
        cfg.attributes["connection"] = ligacao
        command.upgrade(cfg, "0001")
        ligacao.execute(text("DROP TABLE alembic_version"))
        ligacao.execute(text("INSERT INTO utilizadores (nome, telefone, hash_palavra_passe, perfil, area, criado_em) "
                             "VALUES ('Antigo', '849999999', 'x', 'AGRICULTOR', 'Boane', '2026-10-11')"))
    with motor.begin() as ligacao:
        migrar(ligacao)
    with motor.connect() as ligacao:
        colunas = {c["name"] for c in inspect(ligacao).get_columns("utilizadores")}
        assert {"distrito_id", "provincia_codigo", "activo"} <= colunas
        assert {"alertas", "validacoes", "pedidos_visita", "auditoria"} <= set(inspect(ligacao).get_table_names())
        assert ligacao.execute(text("SELECT nome, activo FROM utilizadores")).one() == ("Antigo", 1)
        assert ligacao.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0002"
    motor.dispose()


def test_uuid_aleatorio_nao_existe(cliente):
    cab = registar(cliente, "850000099")
    assert cliente.get(f"/diagnosticos/{uuid.uuid4()}/imagem", headers=cab).status_code == 404
