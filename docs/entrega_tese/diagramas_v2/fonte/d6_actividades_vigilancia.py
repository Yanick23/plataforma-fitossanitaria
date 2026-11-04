"""D6 — Actividades do ciclo de vigilância: diagnóstico → validação → sinal → alerta → visita → seguimento → boletim."""

import sys

from drawio import ORTOGONAL, SETA, Diagrama

d = Diagrama("Actividades: ciclo de vigilância", 1860, 2000)
L0, L1, L2 = 300, 920, 1540           # centros das raias
d.raia("Agricultor<br>(aplicação móvel)", 20, 20, 600, 1960)
d.raia("Plataforma<br>(API e base de dados)", 620, 20, 600, 1960)
d.raia("Técnico ou coordenador<br>(painel web)", 1220, 20, 620, 1960)

SETA_O = SETA + ORTOGONAL


def ligar(a, b, rotulo="", **kw):
    return d.aresta(a, b, SETA_O, rotulo, **kw)


ini = d.inicio(L0 - 15, 145)
a1 = d.actividade("Diagnosticar a planta no telemóvel (sem Internet)", L0, 200)
a2 = d.actividade("Sincronizar quando houver Internet", L0, 350)
p1 = d.actividade("Registar o diagnóstico no distrito do agricultor", L1, 350)
t1 = d.actividade("Validar o diagnóstico (confirmar ou corrigir)", L2, 350)
q1 = d.losango("Praga de declaração<br>obrigatória?", L2 - 150, 500, 300, 130, tamanho=19)
p2 = d.actividade("Avisar o coordenador da província e o administrador", L1, 515)
m1 = d.losango("", L2 - 30, 690, 60, 60)
p3 = d.actividade("Detectar sinais de surto e calcular o risco meteorológico", L1, 810)
q2 = d.losango("Surto, risco ou<br>caso confirmado?", L2 - 150, 793, 300, 130, tamanho=19)
t2 = d.actividade("Enviar alerta à zona", L2, 980)
p4 = d.actividade("Entregar o alerta na sincronização seguinte", L1, 980)
a3 = d.actividade("Receber e ler o alerta", L0, 980)
m2 = d.losango("", L0 - 30, 1140, 60, 60)
q3 = d.losango("Precisa de<br>ajuda técnica?", L0 - 150, 1240, 300, 130, tamanho=19)
a4 = d.actividade("Pedir visita a partir do diagnóstico", L0, 1440)
t3 = d.actividade("Agendar e resolver a visita", L2, 1440)
m3 = d.losango("", L0 - 30, 1600, 60, 60)
a5 = d.actividade("Responder ao seguimento (7 dias depois)", L0, 1700)
p5 = d.actividade("Actualizar o boletim, a exactidão em campo e a eficácia das recomendações", L1, 1693, h=110)
fim = d.fim(L1 - 17, 1880)

ligar(ini, a1)
ligar(a1, a2)
ligar(a2, p1)
ligar(p1, t1)
ligar(t1, q1)
ligar(q1, p2, "[sim]", saida=(0, 0.5), entrada=(1, 0.5))
ligar(q1, m1, "[não]", saida=(0.5, 1), entrada=(0.5, 0))
ligar(p2, m1, entrada=(0, 0.5), pontos=[(920, 720)])
ligar(m1, p3, saida=(0.5, 1), entrada=(0.5, 0), pontos=[(1540, 770), (920, 770)])
ligar(p3, q2, entrada=(0, 0.5))
ligar(q2, t2, "[sim]", saida=(0.5, 1), entrada=(0.5, 0))
ligar(t2, p4)
ligar(p4, a3)
ligar(a3, m2)
ligar(q2, m2, "[não]", saida=(1, 0.5), entrada=(1, 0.5), pontos=[(1800, 858), (1800, 1170)])
ligar(m2, q3)
ligar(q3, a4, "[sim]", saida=(0.5, 1), entrada=(0.5, 0))
ligar(a4, t3)
ligar(q3, m3, "[não]", saida=(0, 0.5), entrada=(0, 0.5), pontos=[(60, 1305), (60, 1630)])
ligar(t3, m3, saida=(0.5, 1), entrada=(1, 0.5), pontos=[(1540, 1630)])
ligar(m3, a5)
ligar(a5, p5)
ligar(p5, fim)

d.gravar(sys.argv[1])
