"""D4 — Sequência do diagnóstico offline e da sincronização (junta as Figuras 5.3 e 5.6 da v1)."""

import sys

from drawio import Diagrama

d = Diagrama("Sequência: diagnóstico e sincronização", 1900, 2360)
U, APP, MOD, LOC, API = 160, 520, 880, 1240, 1640
ALT = 2300
d.lifeline("Agricultor", U, 20, ALT, cinza=False)
d.lifeline("Aplicação<br>(Flutter)", APP, 20, ALT)
d.lifeline("Modelo<br>(TFLite)", MOD, 20, ALT)
d.lifeline("Dados locais<br>(SQLite, JSON)", LOC, 20, ALT)
d.lifeline("API<br>(FastAPI)", API, 20, ALT, w=300)

d.fragmento("opt", "primeiro início de sessão ou token expirado", U - 140, 130, 1790, 360)
d.mensagem(U, APP, 220, "1: introduzir telefone e palavra-passe")
d.mensagem(APP, API, 290, "2: POST /auth/login")
d.mensagem(API, APP, 360, "3: token JWT (válido 30 dias)", resposta=True)
d.auto_mensagem(APP, 400, "4: guardar o token no armazenamento seguro")

d.mensagem(U, APP, 550, "5: escolher a cultura")
d.mensagem(U, APP, 620, "6: tirar 1 a 3 fotografias da planta")
d.auto_mensagem(APP, 660, "7: verificar nitidez e luz de cada fotografia")
d.fragmento("opt", "fotografia desfocada ou escura", U - 140, 740, 780, 130)
d.mensagem(APP, U, 830, "8: aviso e pedido de nova fotografia", resposta=True)

d.mensagem(APP, MOD, 930, "9: inferir(imagens 224 × 224)")
d.mensagem(MOD, APP, 1000, "10: probabilidades por classe", resposta=True)
d.auto_mensagem(APP, 1040, "11: média das probabilidades das fotografias")

d.fragmento("alt", "confiança < 60%", U - 140, 1120, 780, 230, separadores=[(1235, "confiança ≥ 60%")])
d.mensagem(APP, U, 1205, "12a: aviso de incerteza e nova captura", resposta=True)
d.mensagem(APP, U, 1315, "12b: classe, nomes e recomendação", resposta=True)

d.mensagem(APP, LOC, 1420, "13: guardar o diagnóstico com UUID (pendente)")
d.mensagem(LOC, APP, 1490, "14: diagnóstico guardado", resposta=True)

d.fragmento("opt", "ligação ao servidor disponível", APP - 190, 1550, 1520, 710)
d.mensagem(APP, API, 1640, "15: POST /diagnosticos (pendentes, em lote)")
d.mensagem(API, APP, 1710, "16: registados (UUID repetidos ignorados)", resposta=True)
d.mensagem(APP, API, 1790, "17: POST /diagnosticos/{id}/imagem")
d.mensagem(APP, LOC, 1870, "18: marcar como sincronizado")
d.mensagem(APP, API, 1950, "19: pedir catálogo, alertas, validações, visitas e versão do modelo")
d.mensagem(API, APP, 2020, "20: dados actualizados (e ficheiro do modelo, se houver versão nova)", resposta=True)
d.auto_mensagem(APP, 2060, "21: verificar o SHA-256 e activar o modelo novo")
d.mensagem(APP, LOC, 2200, "22: guardar alertas, validações e catálogo")

d.gravar(sys.argv[1])
