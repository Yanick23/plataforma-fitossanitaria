"""D1 — Diagrama de casos de uso da plataforma (versão 2)."""

import sys

from drawio import ASSOC, GENERALIZA, INCLUDE, Diagrama

d = Diagrama("Casos de uso", 2000, 1560)

# Fronteira do sistema
d.caixa("", 300, 20, 1340, 1520)
d.texto("Plataforma de diagnóstico e vigilância fitossanitária", 300, 32, 1330, 40, tamanho=24, negrito=True)

W, H = 370, 92
# Coluna da esquerda: agricultor (aplicação móvel)
XE = 340
diag = d.elipse("Efectuar diagnóstico no dispositivo<br>(RF01–RF07, RF26, RF27)", XE, 100, W, 96)
hist = d.elipse("Consultar historial e validações (RF08)", XE, 250, W, H)
sinc = d.elipse("Sincronizar diagnósticos (RF09)", XE, 390, W, H)
alert_ver = d.elipse("Receber alertas da zona (RF17)", XE, 530, W, H)
pedir = d.elipse("Pedir visita técnica (RF18)", XE, 670, W, H)
segue = d.elipse("Responder ao seguimento do tratamento (RF19)", XE, 810, W, H)
auth = d.elipse("Autenticar-se (RF10)", 780, 1420, 380, 86)

# Coluna da direita: equipa (painel web)
XD = 1240
W2 = 400
cat = d.elipse("Gerir catálogo de culturas e pragas (RF11)", XD - 20, 90, W2, H)
mod = d.elipse("Publicar modelo em piloto ou para todos (RF12)", XD - 20, 200, W2, H)
aud = d.elipse("Consultar auditoria (RF24)", XD - 20, 310, W2, H)
contas = d.elipse("Gerir contas e zonas (RF23)", XD - 20, 450, W2, H)
validar = d.elipse("Validar diagnóstico (RF13)", XD - 20, 600, W2, H)
alertar = d.elipse("Enviar alerta por zona (RF17)", XD - 20, 720, W2, H)
visita = d.elipse("Agendar e resolver visita (RF18)", XD - 20, 840, W2, H)
vig = d.elipse("Consultar vigilância: mapa e surtos (RF15, RF16)", XD - 20, 990, W2, H)
bol = d.elipse("Gerar boletim fitossanitário (RF22)", XD - 20, 1100, W2, H)
exac = d.elipse("Consultar exactidão em campo e exportar conjunto de retreino (RF14, RF25)", XD - 20, 1210, W2, 96)

# Coluna do meio: casos incluídos e extensões
avisar = d.elipse("Avisar caso de declaração obrigatória (RF20)", 760, 560, 330, 100)
risco = d.elipse("Calcular risco meteorológico (RF21)", 790, 1080, 330, H)
sincmeio = None

# Actores
agri = d.actor("Agricultor", 120, 420)
admin = d.actor("Administrador", 1700, 200)
coord = d.actor("Coordenador<br>provincial", 1850, 470)
tec = d.actor("Técnico", 1700, 740)
equipa = d.actor("Equipa", 1850, 1060, abstracto=True)
inv = d.actor("Investigador", 1700, 1330)
meteo = d.actor("Open-Meteo<br>(serviço externo)", 120, 1080)

for uc in (diag, hist, sinc, alert_ver, pedir, segue):
    d.aresta(agri, uc, ASSOC, entrada=(0, 0.5))
d.aresta(agri, auth, ASSOC + "edgeStyle=orthogonalEdgeStyle;rounded=0;", saida=(0, 0.5), entrada=(0, 0.5), pontos=[(50, 466), (50, 1460)])
for uc in (cat, mod, aud):
    d.aresta(admin, uc, ASSOC, saida=(0, 0.35), entrada=(1, 0.5))
d.aresta(coord, contas, ASSOC, entrada=(1, 0.5))
for uc in (validar, alertar, visita):
    d.aresta(tec, uc, ASSOC, entrada=(1, 0.5))
for uc in (vig, bol, exac):
    d.aresta(equipa, uc, ASSOC, entrada=(1, 0.5))
d.aresta(equipa, auth, ASSOC + "edgeStyle=orthogonalEdgeStyle;rounded=0;", saida=(1, 0.5), entrada=(1, 0.5), pontos=[(1950, 1106), (1950, 1460)])

# Generalizações entre actores (seta de triângulo vazio para o actor mais geral)
d.aresta(admin, coord, GENERALIZA, saida=(1, 0.5), entrada=(0.5, 0))
d.aresta(coord, tec, GENERALIZA, saida=(0, 0.5), entrada=(0.5, 0))
d.aresta(tec, equipa, GENERALIZA, saida=(1, 0.5), entrada=(0.5, 0))
d.aresta(inv, equipa, GENERALIZA, saida=(1, 0.3), entrada=(0, 0.75))

# Relações entre casos de uso
d.aresta(avisar, validar, INCLUDE, saida=(0.5, 1), entrada=(0, 0.5), pontos=[(925, 702)])
d.texto("«extend»<br><i>[praga de declaração obrigatória]</i>", 900, 708, 320, 56, tamanho=17)
d.aresta(vig, risco, INCLUDE, "«include»", saida=(0, 0.5), entrada=(1, 0.5))
d.aresta(meteo, risco, ASSOC, entrada=(0, 0.5))

d.gravar(sys.argv[1])
