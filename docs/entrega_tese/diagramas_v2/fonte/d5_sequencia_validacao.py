"""D5 — Sequência da validação pelo técnico e da resposta (aviso de declaração obrigatória e alerta)."""

import sys

from drawio import Diagrama

d = Diagrama("Sequência: validação e resposta", 2080, 2140)
TEC, PAINEL, API, BD, COORD, APP = 150, 470, 830, 1190, 1530, 1870
ALT = 2080
d.lifeline("Técnico", TEC, 20, ALT, w=220, cinza=False)
d.lifeline("Painel web<br>(React)", PAINEL, 20, ALT, w=240)
d.lifeline("API<br>(FastAPI)", API, 20, ALT, w=240)
d.lifeline("Base de dados<br>(PostgreSQL)", BD, 20, ALT, w=260)
d.lifeline("Coordenador /<br>administrador", COORD, 20, ALT, w=260, cinza=False)
d.lifeline("App do<br>agricultor", APP, 20, ALT, w=240)

d.mensagem(TEC, PAINEL, 180, "1: abrir a fila de validação")
d.mensagem(PAINEL, API, 250, "2: GET /gestao/diagnosticos?ordem=confianca")
d.mensagem(API, BD, 320, "3: diagnósticos da zona do técnico")
d.mensagem(API, PAINEL, 390, "4: menos certos primeiro", resposta=True)
d.mensagem(TEC, PAINEL, 470, "5: confirmar ou corrigir a classe (com nota)")
d.mensagem(PAINEL, API, 540, "6: PUT /diagnosticos/{id}/validacao")
d.auto_mensagem(API, 580, "7: verificar o perfil e a zona")
d.mensagem(API, BD, 690, "8: gravar a validação e a auditoria")

d.fragmento("opt", "praga de declaração obrigatória, classe nova", API - 160, 740, 740, 160)
d.mensagem(API, BD, 850, "9: criar notificações")

d.mensagem(API, PAINEL, 960, "10: diagnóstico «Confirmado» ou «Corrigido»", resposta=True)

d.mensagem(COORD, API, 1060, "11: GET /gestao/notificacoes (a cada minuto)")
d.mensagem(API, COORD, 1130, "12: aviso no sino: caso confirmado", resposta=True)

d.fragmento("opt", "o técnico decide avisar a zona", TEC - 120, 1190, 1440, 360)
d.mensagem(TEC, PAINEL, 1280, "13: compor o alerta (zona, nível, praga)")
d.mensagem(PAINEL, API, 1350, "14: POST /alertas")
d.auto_mensagem(API, 1385, "15: verificar se o destino está na zona")
d.mensagem(API, BD, 1490, "16: gravar o alerta e a auditoria")

d.fragmento("opt", "sincronização seguinte da app", API - 160, 1610, 1340, 380)
d.mensagem(APP, API, 1700, "17: GET /alertas/meus e GET /diagnosticos")
d.mensagem(API, APP, 1770, "18: alerta da zona e «Corrigido pelo técnico»", resposta=True)
d.mensagem(APP, API, 1850, "19: POST /alertas/{id}/lido")
d.mensagem(API, BD, 1920, "20: registar a leitura (taxa de leitura)")

d.gravar(sys.argv[1])
