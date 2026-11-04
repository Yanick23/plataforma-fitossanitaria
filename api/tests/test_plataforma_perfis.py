"""Perfis finos (6b) e aviso imediato das pragas de declaração obrigatória (3b).

Coordenador provincial: o que o técnico faz, na província inteira, mais gerir as contas de técnicos e
agricultores dessa província. Investigador: só leitura, país todo, sem nomes nem telefones.
Nampula (MZ-N) e Cabo Delgado (MZ-P) só são usadas nestes testes.
"""

from conftest import entrar, registar
from test_plataforma import ADMIN, criar_tecnico, distrito
from test_plataforma_fase2 import diag, patologia, preparar_cultura


def criar_conta(cliente, telefone: str, perfil: str, **zona) -> dict:
    admin = entrar(cliente, *ADMIN)
    r = cliente.post("/utilizadores", headers=admin, json={
        "nome": f"{perfil.capitalize()} {telefone}", "telefone": telefone, "palavra_passe": "segredo123",
        "perfil": perfil, **zona})
    assert r.status_code == 201, r.text
    return entrar(cliente, telefone, "segredo123")


def eu(cliente, cab: dict) -> dict:
    return cliente.get("/auth/eu", headers=cab).json()


def declaracao_obrigatoria(cliente) -> dict:
    """A ferrugem do feijão passa a ser de declaração obrigatória."""
    admin = preparar_cultura(cliente)
    p = patologia(cliente, "ferrugem")
    r = cliente.put(f"/patologias/{p['id']}", headers=admin, json={
        **{k: p[k] for k in ("nome_local", "nome_cientifico", "tipo", "recomendacao")}, "declaracao_obrigatoria": True})
    assert r.status_code == 200
    return p


# --- Coordenador provincial ---------------------------------------------------------

def test_coordenador_precisa_de_provincia(cliente):
    admin = entrar(cliente, *ADMIN)
    r = cliente.post("/utilizadores", headers=admin, json={
        "nome": "Sem província", "telefone": "870000001", "palavra_passe": "segredo123", "perfil": "COORDENADOR"})
    assert r.status_code == 422
    cab = criar_conta(cliente, "870000002", "COORDENADOR", provincia_codigo="MZ-N")
    assert eu(cliente, cab)["perfil"] == "COORDENADOR" and eu(cliente, cab)["provincia_codigo"] == "MZ-N"


def test_coordenador_ve_e_valida_a_provincia_toda(cliente):
    preparar_cultura(cliente)
    coord = criar_conta(cliente, "870000010", "COORDENADOR", provincia_codigo="MZ-N")
    em_angoche, em_erati, em_pemba = (registar(cliente, t, area=a) for t, a in
                                      (("870000011", "Angoche"), ("870000012", "Erati"), ("870000013", "Ancuabe")))
    d1, d2, d3 = diag("saudavel"), diag("saudavel"), diag("saudavel")
    for cab, d in ((em_angoche, d1), (em_erati, d2), (em_pemba, d3)):
        assert cliente.post("/diagnosticos", json=[d], headers=cab).status_code == 200

    ids = {d["id"] for d in cliente.get("/gestao/diagnosticos", headers=coord, params={"cultura": "feijao"}).json()["itens"]}
    assert {d1["id"], d2["id"]} <= ids and d3["id"] not in ids
    assert "Nampula" in cliente.get("/gestao/resumo", headers=coord).json()["zona"]

    assert cliente.put(f"/diagnosticos/{d2['id']}/validacao", headers=coord,
                       json={"classe_confirmada": "saudavel"}).status_code == 200
    assert cliente.put(f"/diagnosticos/{d3['id']}/validacao", headers=coord,
                       json={"classe_confirmada": "saudavel"}).status_code == 403
    # Alerta para um distrito da província: sim; para outra província: não
    alerta = {"titulo": "Aviso", "mensagem": "Vigie as folhas.", "nivel": "INFORMACAO"}
    assert cliente.post("/alertas", headers=coord, json={**alerta, "distrito_id": distrito(cliente, "Erati")["id"]}
                        ).status_code == 201
    assert cliente.post("/alertas", headers=coord, json={**alerta, "provincia_codigo": "MZ-P"}).status_code == 403


def test_coordenador_gere_contas_so_na_provincia(cliente):
    coord = criar_conta(cliente, "870000020", "COORDENADOR", provincia_codigo="MZ-N")
    novo = {"palavra_passe": "segredo123", "perfil": "TECNICO"}

    # Cria técnicos na província (sem zona indicada fica na província dele), não noutras
    r = cliente.post("/utilizadores", headers=coord, json={**novo, "nome": "Técnico A", "telefone": "870000021",
                                                           "distrito_id": distrito(cliente, "Angoche")["id"]})
    assert r.status_code == 201 and r.json()["provincia_codigo"] == "MZ-N"
    tecnico_a = r.json()["id"]
    r = cliente.post("/utilizadores", headers=coord, json={**novo, "nome": "Técnico B", "telefone": "870000022"})
    assert r.status_code == 201 and r.json()["provincia_codigo"] == "MZ-N" and r.json()["distrito_id"] is None
    assert cliente.post("/utilizadores", headers=coord, json={**novo, "nome": "Fora", "telefone": "870000023",
                                                              "provincia_codigo": "MZ-P"}).status_code == 403
    for perfil in ("ADMINISTRADOR", "COORDENADOR", "INVESTIGADOR"):
        assert cliente.post("/utilizadores", headers=coord, json={
            **novo, "perfil": perfil, "nome": "Conta X", "telefone": "870000024"}).status_code == 403

    # Lista: agricultores e técnicos da província (incluindo o técnico provincial, sem distrito)
    registar(cliente, "870000025", area="Erati")
    fora = registar(cliente, "870000026", area="Balama")
    contas = cliente.get("/gestao/utilizadores", headers=coord, params={"limite": 200}).json()["itens"]
    telefones = {c["telefone"] for c in contas}
    assert {"870000021", "870000022", "870000025"} <= telefones and "870000026" not in telefones
    assert {c["perfil"] for c in contas} <= {"AGRICULTOR", "TECNICO"}

    # Altera e desactiva contas da província; não de outra, nem as promove a perfis acima
    assert cliente.patch(f"/gestao/utilizadores/{tecnico_a}", headers=coord, json={"activo": False}).json()["activo"] is False
    assert cliente.patch(f"/gestao/utilizadores/{tecnico_a}", headers=coord,
                         json={"perfil": "ADMINISTRADOR"}).status_code == 403
    assert cliente.patch(f"/gestao/utilizadores/{tecnico_a}", headers=coord,
                         json={"distrito_id": distrito(cliente, "Balama")["id"]}).status_code == 403
    id_fora = eu(cliente, fora)["id"]
    assert cliente.patch(f"/gestao/utilizadores/{id_fora}", headers=coord, json={"activo": False}).status_code == 403
    assert cliente.post(f"/gestao/utilizadores/{tecnico_a}/palavra-passe", headers=coord,
                        json={"palavra_passe": "nova-123"}).status_code == 204
    assert cliente.post(f"/gestao/utilizadores/{id_fora}/palavra-passe", headers=coord,
                        json={"palavra_passe": "nova-123"}).status_code == 403
    # Não muda o próprio perfil nem a auditoria (só do administrador)
    assert cliente.patch(f"/gestao/utilizadores/{eu(cliente, coord)['id']}", headers=coord,
                         json={"perfil": "AGRICULTOR"}).status_code == 409
    assert cliente.get("/gestao/auditoria", headers=coord).status_code == 403


def test_tecnico_continua_sem_gerir_contas(cliente):
    tecnico = criar_tecnico(cliente, "870000030", area="Erati")
    alvo = eu(cliente, registar(cliente, "870000031", area="Erati"))["id"]
    assert cliente.patch(f"/gestao/utilizadores/{alvo}", headers=tecnico, json={"activo": False}).status_code == 403
    assert cliente.post("/utilizadores", headers=tecnico, json={
        "nome": "Conta X", "telefone": "870000032", "palavra_passe": "segredo123", "perfil": "AGRICULTOR"}).status_code == 403


# --- Investigador ---------------------------------------------------------------------

def test_investigador_le_tudo_anonimizado(cliente):
    p = declaracao_obrigatoria(cliente)
    inv = criar_conta(cliente, "870000040", "INVESTIGADOR")
    agricultor = registar(cliente, "870000041", area="Angoche")
    d = diag()
    cliente.post("/diagnosticos", json=[d], headers=agricultor)

    itens = cliente.get("/gestao/diagnosticos", headers=inv, params={"cultura": "feijao", "limite": 200}).json()["itens"]
    meu = next(x for x in itens if x["id"] == d["id"])
    assert meu["utilizador_telefone"] == "" and meu["utilizador_id"] == 0
    assert meu["utilizador_nome"].startswith("Agricultor ") and "870000041" not in meu["utilizador_nome"]
    # O pseudónimo é estável (permite contar casos por agricultor sem saber quem é)
    outra = cliente.get("/gestao/diagnosticos", headers=inv, params={"cultura": "feijao", "limite": 200}).json()["itens"]
    assert next(x for x in outra if x["id"] == d["id"])["utilizador_nome"] == meu["utilizador_nome"]

    declaracoes = cliente.get("/vigilancia/declaracoes", headers=inv).json()
    assert declaracoes and all(x["agricultor_telefone"] == "" for x in declaracoes)
    assert all(x["agricultor_telefone"] == "" for x in cliente.get("/gestao/boletim", headers=inv).json()["declaracoes"])
    assert cliente.get("/diagnosticos", headers=inv).json()[0]["utilizador_id"] == 0

    for caminho in ("/gestao/resumo", "/vigilancia/ocorrencias", "/vigilancia/surtos", "/gestao/eficacia",
                    "/validacoes/exactidao", "/validacoes/exportar", "/gestao/boletim.csv", "/modelos/milho"):
        assert cliente.get(caminho, headers=inv).status_code == 200, caminho
    assert cliente.get("/gestao/resumo", headers=inv).json()["zona"] == "Moçambique"


def test_investigador_nao_escreve_nem_ve_contactos(cliente):
    preparar_cultura(cliente)
    inv = criar_conta(cliente, "870000050", "INVESTIGADOR")
    d = diag()
    cliente.post("/diagnosticos", json=[d], headers=registar(cliente, "870000051", area="Angoche"))
    assert cliente.put(f"/diagnosticos/{d['id']}/validacao", headers=inv,
                       json={"classe_confirmada": "ferrugem"}).status_code == 403
    assert cliente.post("/alertas", headers=inv, json={
        "titulo": "Aviso X", "mensagem": "Mensagem Y", "nivel": "AVISO"}).status_code == 403
    for caminho in ("/visitas", "/alertas", "/gestao/utilizadores", "/gestao/auditoria", "/gestao/notificacoes"):
        assert cliente.get(caminho, headers=inv).status_code == 403, caminho
    pid = patologia(cliente, "ferrugem")["id"]
    assert cliente.post(f"/patologias/{pid}/validar", headers=inv).status_code == 403


# --- Declaração obrigatória: aviso imediato -------------------------------------------

def test_caso_confirmado_avisa_coordenador_e_administrador(cliente):
    declaracao_obrigatoria(cliente)
    admin = entrar(cliente, *ADMIN)
    coord_nampula = criar_conta(cliente, "870000060", "COORDENADOR", provincia_codigo="MZ-N")
    coord_pemba = criar_conta(cliente, "870000061", "COORDENADOR", provincia_codigo="MZ-P")
    tecnico = criar_tecnico(cliente, "870000062", area="Ilha de Moçambique")
    cab = registar(cliente, "870000063", area="Ilha de Moçambique")
    caso, saudavel = diag(), diag("saudavel")
    cliente.post("/diagnosticos", json=[caso, saudavel], headers=cab)

    def nao_lidas(c):
        return cliente.get("/gestao/notificacoes", headers=c).json()["nao_lidas"]

    antes = {"admin": nao_lidas(admin), "pemba": nao_lidas(coord_pemba)}
    assert nao_lidas(coord_nampula) == 0

    # Folha saudável confirmada: ninguém é avisado
    cliente.put(f"/diagnosticos/{saudavel['id']}/validacao", headers=tecnico, json={"classe_confirmada": "saudavel"})
    assert nao_lidas(coord_nampula) == 0

    # Ferrugem confirmada: avisa o coordenador de Nampula e o administrador; não o de Cabo Delgado
    assert cliente.put(f"/diagnosticos/{caso['id']}/validacao", headers=tecnico,
                       json={"classe_confirmada": "ferrugem"}).status_code == 200
    lista = cliente.get("/gestao/notificacoes", headers=coord_nampula).json()
    assert lista["nao_lidas"] == 1
    n = lista["itens"][0]
    assert n["tipo"] == "DECLARACAO_OBRIGATORIA" and n["diagnostico_id"] == caso["id"] and n["lida_em"] is None
    assert "Ferrugem" in n["titulo"] and "Ilha de Moçambique" in n["mensagem"]
    assert nao_lidas(admin) == antes["admin"] + 1
    assert nao_lidas(coord_pemba) == antes["pemba"]
    assert nao_lidas(tecnico) == 0  # quem validou não é avisado do próprio caso

    # Validar outra vez com a mesma classe não repete o aviso
    cliente.put(f"/diagnosticos/{caso['id']}/validacao", headers=tecnico,
                json={"classe_confirmada": "ferrugem", "nota": "Confirmado no terreno."})
    assert nao_lidas(coord_nampula) == 1

    # Ler: uma, ou todas; ninguém lê as notificações de outra pessoa
    assert cliente.post(f"/gestao/notificacoes/{n['id']}/lida", headers=coord_pemba).status_code == 404
    assert cliente.post(f"/gestao/notificacoes/{n['id']}/lida", headers=coord_nampula).status_code == 204
    assert nao_lidas(coord_nampula) == 0
    assert cliente.get("/gestao/notificacoes", headers=coord_nampula, params={"so_nao_lidas": True}).json()["itens"] == []
    assert cliente.post("/gestao/notificacoes/lidas", headers=admin).status_code == 204
    assert nao_lidas(admin) == 0

    # Fica no registo de auditoria
    reg = cliente.get("/gestao/auditoria", headers=admin, params={"accao": "declaracao.notificar"}).json()["itens"]
    assert any(r["entidade_id"] == caso["id"] for r in reg)


def test_agricultor_nao_tem_notificacoes_da_equipa(cliente):
    assert cliente.get("/gestao/notificacoes", headers=registar(cliente, "870000070")).status_code == 403
