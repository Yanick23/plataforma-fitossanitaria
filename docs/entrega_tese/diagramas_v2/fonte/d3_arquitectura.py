"""D3 — Arquitectura da plataforma (versão 2): app offline, painel web em MVVM e API em camadas."""

import sys

from drawio import ORTOGONAL, RESPOSTA, SETA, Diagrama

d = Diagrama("Arquitectura", 2440, 2000)


def numero(n, x, y):
    d._vertice(str(n), "ellipse;whiteSpace=wrap;html=1;fontFamily=Helvetica;fontSize=19;fontStyle=1;"
               "strokeColor=#000000;strokeWidth=2;fillColor=#FFFFFF;", x, y, 40, 40)


def bloco(titulo, texto, x, y, w, h):
    return d.caixa(f"<b>{titulo}</b><br>{texto}", x, y, w, h, tamanho=20)


# --- Telemóvel ---------------------------------------------------------------------
d.caixa("", 220, 40, 980, 700, tracejada=True)
d.texto("Telemóvel Android (funciona sem Internet)", 240, 50, 800, 36, tamanho=22, negrito=True, alinhar="left")
interface = bloco("Interface (Flutter / Dart)", "captura, resultado, historial,<br>alertas, visitas e seguimento",
                  260, 110, 420, 110)
verif = bloco("Verificação da fotografia", "nitidez e luz; várias fotos por caso", 260, 300, 420, 90)
tflite = bloco("Modelos TFLite INT8", "milho e mandioca (4,35 MB cada)", 260, 470, 420, 100)
locais = d.cilindro("<b>Dados locais</b><br>SQLite: historial, validações<br>e seguimento; JSON: catálogo,<br>"
                    "alertas, visitas e versão do modelo", 760, 100, 400, 170)
sinc = bloco("Sincronização", "UUID, token JWT, verificação SHA-256", 760, 470, 400, 100)

# --- Painel web ----------------------------------------------------------------------
d.caixa("", 1300, 40, 900, 700, tracejada=True)
d.texto("Navegador: painel web (React + TypeScript, MVVM)", 1320, 50, 860, 36, tamanho=22, negrito=True,
        alinhar="left")
view = bloco("View", "componentes React: painel, vigilância, validação, alertas,<br>visitas, boletim, catálogo, "
             "modelos, contas, auditoria", 1340, 110, 820, 110)
vm = bloco("ViewModel", "hooks: estado de cada ecrã e cache dos pedidos (TanStack Query)", 1340, 300, 820, 90)
model = bloco("Model", "repositórios: uma função por rota da API (HTTP, JSON, token JWT)", 1340, 470, 820, 100)

# --- Servidor ------------------------------------------------------------------------
d.caixa("", 220, 880, 1450, 980, tracejada=True)
d.texto("Servidor: API REST (FastAPI + Uvicorn)", 240, 890, 900, 36, tamanho=22, negrito=True, alinhar="left")
rotas = bloco("Rotas", "validação dos pedidos (Pydantic), autenticação JWT, permissões por perfil e por zona; "
              "61 endpoints", 260, 950, 1370, 100)
servicos = bloco("Serviços (regras de negócio)", "sincronização · validação e exactidão em campo · vigilância e "
                 "surtos · alertas · visitas · boletim · catálogo e modelos (piloto, porta de qualidade) · "
                 "risco meteorológico · notificações · auditoria", 260, 1120, 900, 150)
gradcam = bloco("Serviço Grad-CAM", "TensorFlow / Keras (.keras)", 1210, 1120, 420, 150)
repos = bloco("Repositórios", "SQLAlchemy 2 (assíncrono);<br>migrações Alembic", 260, 1340, 380, 110)
pg = d.cilindro("<b>PostgreSQL</b><br>17 tabelas", 260, 1560, 380, 170)
fotos = d.cilindro("<b>Fotografias</b><br>sincronizadas e de referência", 700, 1560, 420, 170)
modelos = d.cilindro("<b>Modelos publicados</b><br>.tflite + SHA-256; .keras", 1180, 1560, 450, 170)

meteo = d.caixa("<b>Open-Meteo</b><br>«sistema externo»<br>previsão horária de 7 dias", 1800, 1560, 400, 120)

# --- Actores -------------------------------------------------------------------------
agri = d.actor("Agricultor", 90, 120)
equipa = d.actor("Equipa", 2300, 120)
d.texto("técnico, coordenador,<br>investigador,<br>administrador", 2210, 250, 230, 90, tamanho=18)

# --- Ligações ------------------------------------------------------------------------
d.aresta(agri, interface, "endArrow=none;")
d.aresta(equipa, view, "endArrow=none;")
d.aresta(interface, verif, SETA)
d.aresta(verif, tflite, SETA)
d.aresta(tflite, interface, RESPOSTA + ORTOGONAL, saida=(1, 0.5), entrada=(1, 0.78), pontos=[(720, 520), (720, 196)])
d.aresta(interface, locais, SETA + ORTOGONAL, saida=(1, 0.2), entrada=(0, 0.35))
d.aresta(sinc, locais, RESPOSTA, "lê / marca")
d.aresta(view, vm, SETA)
d.aresta(vm, model, SETA)

d.aresta(sinc, rotas, SETA + ORTOGONAL, saida=(0.35, 1), entrada=(0.47, 0))
d.aresta(rotas, sinc, RESPOSTA + ORTOGONAL, saida=(0.58, 0), entrada=(0.72, 1))
d.aresta(model, rotas, SETA + ORTOGONAL, saida=(0.2, 1), entrada=(0.9, 0))
d.aresta(rotas, model, RESPOSTA + ORTOGONAL, saida=(0.97, 0), entrada=(0.32, 1))
d.aresta(interface, rotas, SETA + ORTOGONAL, saida=(0, 0.75), entrada=(0, 0.5), pontos=[(240, 192), (240, 1000)])

d.aresta(rotas, servicos, SETA, saida=(0.33, 1), entrada=(0.5, 0))
d.aresta(rotas, gradcam, SETA, saida=(0.9, 1), entrada=(0.5, 0))
d.aresta(servicos, repos, SETA, saida=(0.2, 1), entrada=(0.5, 0))
d.aresta(repos, pg, SETA)
d.aresta(servicos, fotos, SETA, saida=(0.69, 1), entrada=(0.5, 0))
d.aresta(servicos, modelos, SETA, saida=(0.95, 1), entrada=(0.2, 0))
d.aresta(gradcam, fotos, RESPOSTA, "lê", saida=(0.2, 1), entrada=(0.85, 0))
d.aresta(gradcam, modelos, RESPOSTA, saida=(0.75, 1), entrada=(0.75, 0))
d.aresta(servicos, meteo, SETA + ORTOGONAL, saida=(0.97, 0), entrada=(0.5, 0), pontos=[(1133, 1085), (2000, 1085)])

for n, x, y in ((1, 485, 240), (2, 485, 410), (3, 700, 337), (4, 700, 90), (5, 893, 790), (6, 1023, 790),
                (7, 1490, 790), (8, 223, 790), (9, 1983, 1300)):
    numero(n, x, y)

d.texto("1 fotografia · 2 imagem aprovada, 224 × 224 · 3 probabilidades · 4 guarda como pendente · "
        "5 envia pendentes e fotografias (lote) · 6 confirmação, catálogo, alertas, validações, visitas e nova "
        "versão do modelo<br>7 painel: pedidos e respostas em JSON · 8 pede o mapa Grad-CAM · 9 previsão do tempo "
        "(guardada 3 h) · 1–4 sem Internet; 5–9 só com Internet · tracejado: resposta ou leitura",
        160, 1880, 2120, 90, tamanho=18)

d.gravar(sys.argv[1])
