"""Plataforma (fase 2): catálogo enriquecido, versões piloto do modelo, seguimento, declaração obrigatória e boletim."""

import json
from datetime import date

from conftest import entrar, novo_diagnostico, registar
from test_plataforma import ADMIN, criar_tecnico, diagnostico_em, distrito
from test_sincronizacao import jpeg

CULTURA = "feijao"


def preparar_cultura(cliente) -> dict:
    """Uma cultura só destes testes (os modelos do milho são usados noutros testes)."""
    admin = entrar(cliente, *ADMIN)
    if cliente.get("/patologias", params={"cultura": CULTURA}).json():
        return admin
    cliente.post("/culturas", headers=admin, json={"id": CULTURA, "nome": "Feijão", "nome_cientifico": "Phaseolus vulgaris"})
    for codigo, tipo in (("ferrugem", "DOENCA"), ("saudavel", "SAUDAVEL")):
        r = cliente.post("/patologias", headers=admin, json={
            "cultura_id": CULTURA, "codigo": codigo, "nome_local": codigo.capitalize(), "nome_cientifico": "-",
            "tipo": tipo, "recomendacao": "Recomendação inicial.", "sintomas": "Pústulas castanhas."})
        assert r.status_code == 201, r.text
    return admin


def patologia(cliente, codigo: str) -> dict:
    return next(p for p in cliente.get("/patologias", params={"cultura": CULTURA}).json() if p["codigo"] == codigo)


def diag(classe: str = "ferrugem", versao: int = 1, confianca: float = 0.9) -> dict:
    d = novo_diagnostico(CULTURA, classe)
    d["versao_modelo"], d["confianca"] = versao, confianca
    return d


# --- Catálogo enriquecido ---------------------------------------------------------

def test_conteudo_versionado_e_validado(cliente):
    admin = preparar_cultura(cliente)
    tecnico = criar_tecnico(cliente, "860000101", area="Boane")
    agricultor = registar(cliente, "860000102")
    p = patologia(cliente, "ferrugem")
    assert p["versao_conteudo"] == 1 and p["validado_por_nome"] is None and p["sintomas"] == "Pústulas castanhas."

    assert cliente.post(f"/patologias/{p['id']}/validar", headers=agricultor).status_code == 403
    r = cliente.post(f"/patologias/{p['id']}/validar", headers=tecnico)
    assert r.status_code == 200 and r.json()["validado_por_nome"] == "Técnico 860000101"

    base = {k: p[k] for k in ("nome_local", "nome_cientifico", "tipo", "recomendacao")}
    # Só muda a declaração obrigatória: o texto é o mesmo, a validação mantém-se e os sintomas não se perdem
    r = cliente.put(f"/patologias/{p['id']}", headers=admin, json={**base, "declaracao_obrigatoria": True})
    assert r.json()["versao_conteudo"] == 1 and r.json()["validado_por_nome"] is not None
    assert r.json()["sintomas"] == "Pústulas castanhas." and r.json()["declaracao_obrigatoria"] is True

    # Mudar o texto sobe a versão e retira a validação
    r = cliente.put(f"/patologias/{p['id']}", headers=admin, json={**base, "prevencao": "Rodar culturas."})
    assert r.json()["versao_conteudo"] == 2 and r.json()["validado_por_nome"] is None
    assert r.json()["prevencao"] == "Rodar culturas." and r.json()["declaracao_obrigatoria"] is True


def test_fotos_de_referencia(cliente):
    admin = preparar_cultura(cliente)
    p = patologia(cliente, "ferrugem")
    agricultor = registar(cliente, "860000103")
    foto = {"ficheiro": ("f.jpg", jpeg(), "image/jpeg")}
    assert cliente.post(f"/patologias/{p['id']}/fotos", headers=agricultor, files=foto).status_code == 403
    assert cliente.post(f"/patologias/{p['id']}/fotos", headers=admin,
                        files={"ficheiro": ("f.gif", b"GIF89a", "image/gif")}).status_code == 415

    r = cliente.post(f"/patologias/{p['id']}/fotos", headers=admin, files=foto, data={"legenda": "Folha com pústulas"})
    assert r.status_code == 201
    f = r.json()["fotos"][-1]
    assert f["legenda"] == "Folha com pústulas"
    img = cliente.get(f["url"])  # pública: a app descarrega-a sem sessão
    assert img.status_code == 200 and img.content[:2] == b"\xff\xd8"

    assert cliente.delete(f["url"], headers=admin).status_code == 204
    assert cliente.get(f["url"]).status_code == 404
    assert f["id"] not in {x["id"] for x in patologia(cliente, "ferrugem")["fotos"]}


# --- Versões do modelo: piloto, porta de qualidade, monitorização ----------------

def publicar(cliente, admin, **campos) -> dict:
    r = cliente.post(f"/modelos/{CULTURA}", headers=admin, data={"classes": json.dumps(["ferrugem", "saudavel"]), **campos},
                     files={"ficheiro": ("m.tflite", b"modelo", "application/octet-stream")})
    assert r.status_code == 201, r.text
    return r.json()


def test_piloto_e_porta_de_qualidade(cliente):
    admin = preparar_cultura(cliente)
    boane, moamba = distrito(cliente, "Boane")["id"], distrito(cliente, "Moamba")["id"]
    v1 = publicar(cliente, admin)
    v2 = publicar(cliente, admin, distritos_piloto=json.dumps([boane]), notas="Retreino com fotos de campo")
    assert v1["estado"] == "PUBLICADO" and v2["estado"] == "PILOTO" and v2["distritos_piloto"] == [boane]
    assert cliente.post(f"/modelos/{CULTURA}", headers=admin, data={
        "classes": "[\"a\"]", "distritos_piloto": "[999999]"},
        files={"ficheiro": ("m.tflite", b"x", "application/octet-stream")}).status_code == 422

    em_boane, em_moamba = registar(cliente, "860000111", area="Boane"), registar(cliente, "860000112", area="Moamba")
    assert cliente.get(f"/modelos/{CULTURA}/ultima-versao", headers=em_boane).json()["versao"] == v2["versao"]
    assert cliente.get(f"/modelos/{CULTURA}/ultima-versao", headers=em_moamba).json()["versao"] == v1["versao"]

    # Sem validações suficientes a porta fecha; forçar fica na auditoria
    url = f"/modelos/{CULTURA}/{v2['versao']}"
    porta = cliente.get(f"{url}/porta-qualidade", headers=admin).json()
    assert porta["aprovado"] is False and porta["validados"] == 0
    assert cliente.patch(url, headers=admin, json={"estado": "PUBLICADO"}).status_code == 409

    # 10 validações em campo da v2 (9 correctas) e a porta abre
    tecnico = criar_tecnico(cliente, "860000113", area="Boane")
    lote = [diag(versao=v2["versao"]) for _ in range(10)]
    cliente.post("/diagnosticos", json=lote, headers=em_boane)
    for i, d in enumerate(lote):
        r = cliente.put(f"/diagnosticos/{d['id']}/validacao", headers=tecnico,
                        json={"classe_confirmada": "saudavel" if i == 0 else "ferrugem"})
        assert r.status_code == 200, r.text
    porta = cliente.get(f"{url}/porta-qualidade", headers=admin).json()
    assert porta["aprovado"] is True and porta["validados"] == 10 and porta["exactidao"] == 0.9

    r = cliente.patch(url, headers=admin, json={"estado": "PUBLICADO"})
    assert r.status_code == 200 and r.json()["estado"] == "PUBLICADO"
    assert cliente.get(f"/modelos/{CULTURA}/ultima-versao", headers=em_moamba).json()["versao"] == v2["versao"]

    # Retirar a v2: volta tudo à v1
    cliente.patch(url, headers=admin, json={"estado": "RETIRADO"})
    assert cliente.get(f"/modelos/{CULTURA}/ultima-versao", headers=em_boane).json()["versao"] == v1["versao"]
    auditoria = cliente.get("/gestao/auditoria", headers=admin, params={"accao": "modelo.actualizar"}).json()["itens"]
    assert auditoria[0]["entidade_id"] == f"{CULTURA} v{v2['versao']}"


def test_monitorizacao_detecta_deriva(cliente):
    preparar_cultura(cliente)
    admin = entrar(cliente, *ADMIN)
    cab = registar(cliente, "860000121", area="Boane")
    antigos = [diagnostico_em(40 - i % 10, "ferrugem", CULTURA) | {"versao_modelo": 7, "confianca": 0.9}
               for i in range(20)]
    recentes = [diagnostico_em(i % 10 / 2, "ferrugem", CULTURA) | {"versao_modelo": 7, "confianca": 0.4}
                for i in range(20)]
    cliente.post("/diagnosticos", json=antigos + recentes, headers=cab)

    m = cliente.get(f"/modelos/{CULTURA}/monitorizacao", headers=admin).json()
    sinal = next(s for s in m["sinais"] if s["versao"] == 7)
    assert sinal["deriva"] is True and sinal["taxa_baixa_inicial"] == 0 and sinal["taxa_baixa_recente"] == 1
    semanas = [s for s in m["semanas"] if s["versao"] == 7]
    assert sum(s["diagnosticos"] for s in semanas) == 40


# --- Seguimento do tratamento e eficácia -----------------------------------------

def test_seguimento_e_eficacia(cliente):
    preparar_cultura(cliente)
    tecnico = criar_tecnico(cliente, "860000131", area="Namaacha")
    cab, outro = registar(cliente, "860000132", area="Namaacha"), registar(cliente, "860000133", area="Namaacha")
    ds = [diag() for _ in range(3)]
    cliente.post("/diagnosticos", json=ds, headers=cab)

    resposta = {"seguiu": "SIM", "resultado": "MELHOROU"}
    assert cliente.post(f"/diagnosticos/{ds[0]['id']}/seguimento", headers=outro, json=resposta).status_code == 403
    cliente.post(f"/diagnosticos/{ds[0]['id']}/seguimento", headers=cab, json={"seguiu": "SIM", "resultado": "IGUAL"})
    cliente.post(f"/diagnosticos/{ds[0]['id']}/seguimento", headers=cab, json=resposta)  # substitui a anterior
    cliente.post(f"/diagnosticos/{ds[1]['id']}/seguimento", headers=cab, json={"seguiu": "PARCIAL", "resultado": "PIOROU"})
    cliente.post(f"/diagnosticos/{ds[2]['id']}/seguimento", headers=cab, json={"seguiu": "NAO", "resultado": "NAO_SEI"})

    meus = {d["id"]: d for d in cliente.get("/diagnosticos", headers=cab).json()}
    assert all(meus[d["id"]]["seguimento_respondido"] for d in ds)

    ef = next(e for e in cliente.get("/gestao/eficacia", headers=tecnico).json() if e["cultura_id"] == CULTURA)
    assert (ef["respostas"], ef["seguiram"], ef["melhoraram"], ef["eficacia"]) == (3, 2, 1, 0.5)


# --- Declaração obrigatória e boletim ---------------------------------------------

def test_declaracoes_e_boletim(cliente):
    admin = preparar_cultura(cliente)
    p = patologia(cliente, "ferrugem")
    cliente.put(f"/patologias/{p['id']}", headers=admin, json={
        **{k: p[k] for k in ("nome_local", "nome_cientifico", "tipo", "recomendacao")}, "declaracao_obrigatoria": True})
    tecnico = criar_tecnico(cliente, "860000141", area="Magude")
    cab = registar(cliente, "860000142", area="Magude")
    suspeita, confirmada, saudavel = diag(confianca=0.5), diag(), diag("saudavel")
    cliente.post("/diagnosticos", json=[suspeita, confirmada, saudavel], headers=cab)
    cliente.put(f"/diagnosticos/{confirmada['id']}/validacao", headers=tecnico, json={"classe_confirmada": "ferrugem"})

    estados = {d["diagnostico_id"]: d["estado"] for d in cliente.get("/vigilancia/declaracoes", headers=tecnico).json()}
    assert estados == {suspeita["id"]: "SUSPEITA", confirmada["id"]: "CONFIRMADO"}

    cliente.post("/alertas", headers=tecnico, json={
        "titulo": "Ferrugem em Magude", "mensagem": "Retire as folhas afectadas.", "nivel": "AVISO",
        "patologia_id": p["id"], "distrito_id": distrito(cliente, "Magude")["id"]})

    b = cliente.get("/gestao/boletim", headers=tecnico).json()
    assert [(a["titulo"], a["nivel"], a["zona"], a["patologia_nome"]) for a in b["alertas"]] == [
        ("Ferrugem em Magude", "AVISO", "Distrito de Magude", "Ferrugem")]
    assert "Magude" in b["zona"] and b["diagnosticos"] == 3 and b["diagnosticos_pragas_doencas"] == 2
    assert b["validados"] == 1 and b["exactidao_campo"] == 1 and b["taxa_confianca_baixa"] == round(1 / 3, 4)
    assert b["agricultores_novos"] >= 1 and b["distritos_mais_afectados"] == [{"nome": "Magude", "valor": 2, "detalhe": None}]
    assert len(b["declaracoes"]) == 2

    hoje = date.today().isoformat()
    assert cliente.get("/gestao/boletim", headers=tecnico, params={"inicio": hoje, "fim": "2020-01-01"}).status_code == 422
    csv = cliente.get("/gestao/boletim.csv", headers=tecnico)
    assert csv.headers["content-type"].startswith("text/csv") and "attachment" in csv.headers["content-disposition"]
    linhas = csv.content.decode("utf-8-sig").splitlines()
    assert linhas[0].startswith("provincia,distrito,cultura") and "MZ-L,Magude,feijao,ferrugem,Ferrugem,1,1" in linhas
    assert cliente.get("/gestao/boletim", headers=cab).status_code == 403
