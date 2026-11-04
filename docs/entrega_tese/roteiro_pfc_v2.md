# Roteiro da versão 2 do PFC

**Para:** o projecto do Claude na web que reescreve o texto do PFC, e o Yanick.
**Base:** `PFC_YANICK_RIBEIRO_MUSSAGY_PROD_LAST_VERSION.docx` (versão de Outubro) e o estado do
código a 04/11/2026. **Entrega:** 10/11/2026.

---

## 1. O que muda e porquê

O trabalho deixou de ser «um modelo de ML com uma app». Passou a ser uma **plataforma de
diagnóstico e vigilância fitossanitária**, com uma componente forte de engenharia de software:

- **App Android** (Flutter): diagnóstico sem internet, historial e sincronização; recebe alertas,
  visitas e validações; tem verificação da qualidade da foto, várias fotos por caso e seguimento
  do tratamento.
- **API REST** (FastAPI e PostgreSQL), em camadas (rotas, serviços, repositórios), com 61
  endpoints, 17 tabelas e migrações Alembic de 0001 a 0005.
- **Painel web** (React, Vite e TypeScript, em MVVM), para técnicos, coordenadores, investigadores
  e administradores.

**Nova abordagem do texto:** a plataforma passa a estar no centro e o modelo de ML é um dos seus
componentes. Corta-se a matemática e a estatística de ML e dá-se espaço à engenharia de software
(requisitos, arquitectura, diagramas, implementação, testes).

**Ponto de apoio:** o problema (1.3) já fala em «detecção **e resposta** fitossanitária». A
versão 1 só respondia à detecção (o modelo). A versão 2 responde também à resposta: validação,
vigilância, alertas, visitas e boletim. Por isso o problema **não muda**.

---

## 2. Limites (guia do ISUTC e decisão do Yanick)

| Limite | Regra | Estado actual |
|---|---|---|
| Parte textual (caps. I a VI) | ≤ 12 000 palavras; **não contam** as tabelas, as figuras, os gráficos, o resumo, as referências nem os anexos | **10 637** palavras de prosa (mais 5 409 em tabelas, que não contam) |
| Páginas no total | ≤ 110 (decisão do Yanick) | **111** no Word; **116** no PDF do LibreOffice. **Já está no limite** |
| Resumo | ~250 palavras e palavras-chave | 270 |

**Objectivo:** prosa ≤ 11 500 palavras (margem de 500) e ≤ 105 páginas no Word (margem para os
diagramas novos).

Regras do guia a respeitar:
- Times New Roman: texto a 12, títulos a 14 em negrito, subtítulos a 13 e 12 em negrito.
- Espaçamento 1,5; margens de 3 cm (superior e esquerda) e 2 cm (inferior e direita).
- Palavras estrangeiras em itálico; citações autor-data.
- Equações numeradas à direita.
- Legendas auto-explicativas.
- Paginação em romano na parte pré-textual e em árabe a partir da Introdução.

### Onde estão hoje as páginas (PDF de 116 páginas)

| Parte | Páginas | Meta | Nota |
|---|---|---|---|
| Pré-textual (capa, índices, abreviaturas, resumo) | 18 | 16 | os índices encolhem com menos figuras; tirar as abreviaturas que deixam de ser usadas (ECE, NLL, MCC…) |
| Cap. I | 4 | 4 | |
| Cap. II | 24 | **14** | o maior corte |
| Cap. III | 3 | 3 | |
| Cap. IV | 7 | 6 | |
| Cap. V | 41 | **44** | cresce pouco: entra a plataforma e sai o pormenor de ML |
| Cap. VI | 3 | 3 | |
| Referências | 8 | 8 | saem as de ML que deixem de ser citadas; entram as de vigilância |
| Anexos | 8 | 6 | |
| **Total** | **116** | **~104** | |

---

## 3. Decisões (1 e 2 confirmadas pelo Yanick a 04/11/2026; 3 segue a decisão de não fazer essas funcionalidades; 4 pendente)

1. **Título: mantém-se** como está («Desenvolvimento de uma plataforma para diagnóstico
   automatizado de doenças e pragas em culturas agrícolas com recurso à aprendizagem de máquina»).
   A palavra «plataforma» já cobre a parte de vigilância e resposta.
2. **Hipótese H1: mantém-se, em versão curta.** Enunciado e resultado em poucas linhas (mandioca
   confirma: 93,1%, F1 mínimo 0,885; milho não: 87,0%, três classes abaixo de 0,85). A
   formulação estatística detalhada (binomial, z, *bootstrap*) sai do texto principal; quando
   muito, uma linha a remeter para o Anexo 3.
3. **Funcionalidades que não se fazem** (severidade, FAMEWS, armadilhas, dados abertos,
   segurança de produção, privacidade): não se mencionam como funcionalidades. A segurança (HTTPS,
   cópias de segurança) e a privacidade ficam só nas Recomendações, como já estão.
4. **Línguas locais em áudio (14):** só entra no texto se ficar implementada a tempo. Depende
   da API de áudio do Yanick.

---

## 4. O que fazer em cada capítulo

### Resumo (~250 palavras)
Reescrever:
- três componentes (app, API, painel) e o ciclo diagnóstico → validação → vigilância → alerta →
  visita → boletim;
- os resultados do modelo numa frase (93,1% mandioca, 87,0% milho, 26,2% no teste externo);
- os números de engenharia: 59 testes automáticos da API, 5 perfis, risco meteorológico.

### Cap. I — Introdução (~1 000 palavras)
- **1.2 Problemática:** acrescentar a falha da *resposta*. A extensão chega só a 12% das
  explorações (MADER 2024, já citado no cap. III) e não há registo agregado de onde surgem
  os casos.
- **1.3 Problema:** mantém-se.
- **1.5 Objectivos:** reescrever o 4.º objectivo, por exemplo «Desenvolver uma plataforma que
  integre o modelo treinado numa aplicação móvel offline e em ferramentas web de validação,
  vigilância e resposta para os técnicos». O 3.º (treinar o modelo) mantém-se, mais curto.
- **1.6 Hipótese:** versão curta (ver decisão 2).
- **1.9 Delimitação:** no plano tecnológico, «aplicação Android, API REST e painel web».
- Encurtar o 1.8 (Importância).

### Cap. II — Revisão da literatura (24 → ~14 páginas; prosa 2 950 → ~2 200)
**Cortar ou condensar:**
- 2.1 Agricultura: definições gerais de agricultura e segurança alimentar e a botânica do milho
  e da mandioca. Manter a Tabela 2.1 e versões curtas das Tabelas 2.2 e 2.3.
- 2.2 e 2.3: juntar num só «Visão computacional e aprendizagem profunda».
  - Sair: os três paradigmas de ML, a rede neuronal genérica (Fig. 2.7), a hierarquia IA/ML/DL
    (Fig. 2.6), a arquitectura CNN genérica (Fig. 2.8) e as fórmulas e a lista de métricas
    (kappa, MCC, Wilson, McNemar, bootstrap, Fig. 2.12).
  - Ficar: CNN em duas frases, *transfer learning*, EfficientNetB0, *data augmentation*,
    exactidão, precisão, sensibilidade e F1.
- 2.4.1 e 2.4.2: encurtar o ciclo de vida e a comparação de modelos de desenvolvimento; manter a
  prototipagem como escolha.

**Acrescentar:**
- **2.x Vigilância fitossanitária e alerta precoce** (~350 palavras): vigilância passiva (os
  casos que chegam) e activa; pragas de declaração obrigatória; alertas por zona; modelos de risco
  baseados no tempo (ver as fontes na secção 7). Ligar a Moçambique: o Departamento de Sanidade
  Vegetal e o Decreto n.º 5/2009, já citados no cap. III.
- **2.4.x Arquitectura** (~300 palavras): arquitectura em camadas no servidor (rotas, serviços,
  repositórios); aplicação web de página única; MVVM (Model = repositórios, ViewModel = *hooks*,
  View = componentes); controlo de acesso por perfil (RBAC); migrações da base de dados.
- Tabela 2.5 (tecnologias): juntar React, Vite, TypeScript e Alembic.
- **2.5 Soluções similares:** juntar 1 ou 2 sistemas de vigilância, por exemplo a app FAMEWS da
  FAO para a lagarta-do-cartucho, e uma coluna «vigilância e resposta» na Tabela 2.7.

### Cap. III — Contextualização (~800 palavras)
- Manter o 3.1.1 a 3.1.4.
- No 3.1.5 e 3.1.6, juntar a falha da **resposta**: o técnico não sabe onde estão os casos, não
  há forma de avisar os agricultores de uma zona e não se sabe se o tratamento resultou.
- Ajustar a Figura 3.1, ou acrescentar o fluxo proposto (ver o diagrama D6).

### Cap. IV — Metodologia (7 → ~6 páginas; prosa 1 390 → ~1 200)
- **Sair:** a formulação matemática do 4.5 (equações 1 a 3, normalização com μ e σ, o teste
  binomial). Fica uma frase: «o conjunto de teste usou-se uma só vez; exactidão e F1 por classe,
  com intervalos de confiança a 95%».
- **4.6 Variáveis:** reduzir a Tabela 4.3 às variáveis do modelo e às da plataforma (tempo de
  diagnóstico, testes aprovados).
- **4.8 reescrito:** desenvolvimento por **iterações de prototipagem**, cada uma testada antes da
  seguinte:

  | Iteração | Conteúdo |
  |---|---|
  | 0 | Modelo, app offline e API base (versão 1 do PFC) |
  | 1a–1d | Núcleo de vigilância: regiões, validação, alertas, visitas, auditoria, painel web; a app recebe-os |
  | 2a–2c | Gestão e qualidade: boletim, catálogo enriquecido, modelos em piloto e porta de qualidade, qualidade da foto, várias fotos, seguimento |
  | 2d | Perfis finos (coordenador, investigador) e aviso imediato da declaração obrigatória |
  | 3a | Risco meteorológico |

- **Estratégia de testes:**
  - testes automáticos da API (pytest e httpx, sobre SQLite temporária);
  - testes da app (`flutter test`);
  - painel testado num browser automatizado (Puppeteer), contra uma API de teste;
  - casos de teste funcionais no telemóvel SOTEN R80.
- **Tabela 4.4:** juntar o painel (React 18.3, Vite 5.4, TypeScript 5.6, TanStack Query 5.62), o Alembic e a
  Open-Meteo.

### Cap. V — Resultados (41 → ~44 páginas; prosa 3 700 → ~4 300)
Nova ordem sugerida:

1. **5.1.1 Recolha de dados:** manter; encurtar as Tabelas 5.2 e 5.3, ou passá-las para anexo.
2. **5.1.2 Descrição da solução:** reescrever com os 3 componentes e o ciclo.
3. **5.1.3 Requisitos:** actores = agricultor, técnico, coordenador, investigador, administrador;
   Open-Meteo como sistema externo.
   - Manter RF01 a RF12; actualizar o RF11 (catálogo enriquecido) e o RF12 (piloto, porta de
     qualidade).
   - **Novos** (macro-requisito «Vigilância e resposta»):

     | Código | Requisito |
     |---|---|
     | RF13 | Validar diagnóstico (confirmar ou corrigir, com nota ao agricultor) |
     | RF14 | Exactidão em campo |
     | RF15 | Mapa de ocorrências |
     | RF16 | Sinais de surto |
     | RF17 | Alertas por zona (alcance e leituras) |
     | RF18 | Pedido de visita técnica |
     | RF19 | Seguimento do tratamento aos 7 dias |
     | RF20 | Declaração obrigatória com aviso imediato |
     | RF21 | Risco meteorológico |
     | RF22 | Boletim em PDF e CSV |

   - **Novos** (macro-requisito «Gestão e qualidade»):

     | Código | Requisito |
     |---|---|
     | RF23 | Perfis e zonas de actuação |
     | RF24 | Registo de auditoria |
     | RF25 | Exportar o conjunto de retreino |
     | RF26 | Verificação da qualidade da foto |
     | RF27 | Várias fotos por caso |

   - RNF novos:

     | Código | Requisito |
     |---|---|
     | RNF08 | Controlo de acesso por perfil e por zona |
     | RNF09 | Anonimização para o investigador |
     | RNF10 | Rastreabilidade (auditoria) |
     | RNF11 | O painel funciona sem internet no servidor (previsão guardada) |

   - As tabelas de requisitos **não contam palavras**: pôr nelas o pormenor e manter a prosa curta.
4. **5.1.4 Diagramas:** substituir pelos D1 a D6 (secção 5 deste roteiro).
5. **5.1.5 Arquitectura:** nova figura (D3). Texto sobre as camadas, MVVM, sincronização com UUID,
   migrações e a ligação à Open-Meteo.
6. **5.1.6 Modelo de classificação:** **condensar para ~900 palavras.**
   - **Ficar:** a configuração em duas fases numa tabela curta; as Tabelas 5.8 e 5.9 (por
     classe); a Tabela 5.10 reduzida (H1); o teste externo de 26,2%; a Tabela 5.12 (TFLite) ou
     a 5.13 (telemóvel); a Figura 5.8 (confusão) **ou** a Figura 5.9 (Grad-CAM), não as duas.
   - **Sair do texto principal:** as equações 4 a 6, a Tabela 5.7 completa (passa a duas linhas
     de texto ou vai para o anexo), a Fig. 5.7, o Gráfico 5.1 e a discussão de calibração e
     *bootstrap*.
7. **5.1.7 Protótipo:**
   - **App:** juntar as capturas em grelhas de 3 por figura, para poupar páginas. Acrescentar
     alertas, visitas, «Corrigido pelo técnico», qualidade da foto, «Juntar outra foto» e
     seguimento.
   - **Painel web** (novo): painel, vigilância (mapa, surtos, risco meteorológico, declarações),
     validação com Grad-CAM, alertas, visitas, boletim, catálogo, modelos em piloto, utilizadores
     e perfis, auditoria. Usar as melhores 8 a 10 capturas da lista da secção 6.
   - **Apagar a frase «Não se desenvolveu uma interface web de administração…»**, que agora é
     falsa.
8. **5.1.8 Testes:**
   - API: **59 testes automáticos aprovados** (antes 23);
   - app: 11 testes;
   - painel: compilação sem erros e teste no browser;
   - **T13 (Grad-CAM) passa a aprovado**: 2,4 s no 1.º pedido do milho, 2,1 s na mandioca, 0,8 s
     com o modelo já carregado;
   - casos novos T14 em diante, para as funcionalidades novas.
9. **5.1.9 e 5.1.10 Custos:** recalcular os pontos de função. Há 17 tabelas, contra 6 ficheiros
   lógicos na v1, e muitas entradas, saídas e consultas novas. O esforço, o prazo e o orçamento
   sobem. Ver a secção 8.
10. **5.2 Discussão:**
    - a plataforma fecha o ciclo;
    - a «exactidão em campo», medida pelas validações dos técnicos, responde à limitação do teste
      externo, porque mede o modelo em fotos reais de Moçambique à medida que chegam;
    - o modelo deixa de decidir sozinho: o técnico revê.

### Cap. VI — Conclusões (~800 palavras)
- **Conclusões:** por objectivo, com o 4.º agora cumprido pela plataforma completa.
- **Limitações** novas: as regras meteorológicas não foram validadas com dados locais; a
  usabilidade não foi testada com utilizadores; as capturas do painel usam dados de
  demonstração.
- **Trabalho futuro:**
  - tirar o que já foi feito: o filtro de nitidez (feito) e as línguas nacionais (se a 14 ficar
    feita);
  - juntar o calendário agrícola, as campanhas de vigilância, as machambas com GPS, as
    notificações *push*, o SMS, as organizações e o «não reconhecido» (se a tarefa D4 do Colab não correr).

### Anexos
- **Anexo 1:** actualizar a matriz de coerência ao 4.º objectivo.
- **Anexo 3:** receber o pormenor de ML que sai do cap. V (experiências E0 a E0c, calibração,
  risco–cobertura), em versão compacta. Os anexos não contam palavras, mas contam páginas.
- **Opcional — Anexo 4:** lista dos endpoints da API, em tabela de 1 a 2 páginas.

---

## 5. Diagramas novos (substituem as Figuras 5.1 a 5.6)

**Feitos** (04/11): estão em `diagramas_v2/` em `.drawio` e `.png`, no estilo da v1. Ver `diagramas_v2/LEIA-ME.md`, que diz também que figuras da v1 sair ou ficar.

| ID | Diagrama | Conteúdo |
|---|---|---|
| D1 | Casos de uso | Actores: Agricultor, Técnico, Coordenador (herda do Técnico), Investigador, Administrador; Open-Meteo como actor secundário. Agricultor: diagnosticar, historial, sincronizar, ver alertas, pedir visita, responder ao seguimento. Técnico: validar, alertas, visitas, vigilância, boletim. Coordenador: gerir contas da província, receber avisos de declaração obrigatória. Investigador: consultar (anonimizado), exportar o conjunto de retreino. Administrador: catálogo, modelos (piloto e publicação), contas, auditoria |
| D2 | Classes | Provincia, Distrito, Utilizador (perfil, zona), Cultura, Patologia (declaração obrigatória, versão do conteúdo), FotoReferencia, ModeloML (estado: PILOTO, PUBLICADO, RETIRADO; distritos piloto), Diagnostico (UUID), Imagem, Validacao, Seguimento, PedidoVisita (estados), Alerta, AlertaLeitura, Notificacao, RegistoAuditoria, PrevisaoMeteo. **Atenção:** a v1 diz que o modelo não é uma entidade persistida; agora é (ModeloML) |
| D3 | Arquitectura | App Flutter (TFLite, SQLite, sincronização) ↔ API FastAPI (rotas → serviços → repositórios; Grad-CAM; Alembic) ↔ PostgreSQL; painel React (View → ViewModel → repositórios) ↔ API; API → Open-Meteo |
| D4 | Sequência: diagnóstico e sincronização | Junta as Figuras 5.3 e 5.6 num só diagrama |
| D5 | Sequência: validação e resposta | O técnico valida → API grava a validação e a auditoria → se a praga for de declaração obrigatória, cria notificações para o coordenador e o administrador → o técnico cria um alerta → a app recebe-o na sincronização seguinte |
| D6 | Actividades: ciclo de vigilância | Diagnóstico → sincronização → validação → (surto ou risco meteorológico) → alerta → visita → seguimento → boletim |

---

## 6. Material disponível no repositório

- **Capturas do painel** (`docs/entrega_tese/dados_web/`, 43 ficheiros). Sugestão das melhores:
  - `1b_01_painel.png` (painel)
  - `2b_15_vigilancia.png` (vigilância com mapa)
  - `1c_02_detalhe_gradcam.png` (validação com Grad-CAM)
  - `1c_05_alerta_composicao.png` (alerta e pré-visualização no telemóvel)
  - `1c_09_visita_agendar.png` (visitas)
  - `2b_01_boletim_admin.png` (boletim)
  - `2b_13_modelo_piloto.png` (modelos em piloto)
  - `6b_01_coordenador_notificacoes.png` (aviso de declaração obrigatória)
  - `6b_05_investigador_detalhe.png` (anonimização)
  - `9_01_risco_meteorologico.png` (risco meteorológico)
- **Capturas da app** (`docs/entrega_tese/dados_telemovel/capturas/`): as da v1, mais
  `09_detalhe_gradcam.png`, `09b_` e `09c_`, que são o T13 aprovado.
  - **Faltam** as dos alertas, visitas, seguimento, qualidade da foto e várias fotos: dependem do
    teste no telemóvel (secção 9).
- **Texto já escrito, por entrega** (`docs/entrega_tese/03_resultados_plataforma.md`): o que se
  fez, como se testou e as limitações das entregas 1a a 3a. É a fonte de verdade para o cap. V.
- **Funcionalidades e porquês:** `docs/produto/funcionalidades_plataforma.md`.
- **Estado e decisões:** `docs/produto/estado_e_pendentes.md`.

---

## 7. Fontes novas a confirmar antes de citar

Vêm das regras do risco meteorológico (em `api/app/servicos/meteorologia.py`). **Confirmar
cada uma na fonte original antes de a pôr nas referências; não inventar dados bibliográficos.**

- Queima da folha (*Exserohilum turcicum*): infecção entre 15 e 30 °C, óptimo a cerca de 20 °C;
  esporulação com 9 h ou mais de orvalho (resumos na *Phytopathology* 73:722, 1983, e 79:1243,
  1989).
- Mancha cinzenta (*Cercospora* spp.): HR ≥ 90% e folha molhada durante 12 h ou mais (Purdue
  Extension BP-56; University of Nebraska CropWatch); 22–30 °C e HR ≥ 95% como preditor (*Plant
  Disease* 86:1127, 2002).
- Mancha castanha da mandioca: tese da KNUST (1991), `ir.knust.edu.gh/handle/123456789/3590`.
- Ácaro verde: Akinlosotu (1982); Gutierrez et al. (1988), *Journal of Applied Ecology*
  25:941; Hanna et al. (2005).
- Open-Meteo (open-meteo.com) como fonte da previsão.
- Para a secção de vigilância: a FAO e a IPPC sobre vigilância de pragas, e a app FAMEWS. A
  referência exacta está por procurar.

---

## 8. Quem faz o quê

| Tarefa | Quem |
|---|---|
| Reescrever o texto (caps. I a VI, resumo, anexos) seguindo este roteiro | Projecto do Claude na web |
| Gerar os diagramas D1 a D6 a partir do código | Claude Code (**feito**) |
| Recontar os pontos de função e refazer o COCOMO II e o orçamento | Claude Code (o texto da web usa os números) |
| Tabela de casos de teste T14 em diante, com os resultados reais | Claude Code |
| Verificar que o texto final diz a verdade sobre a plataforma (números, nomes, funcionalidades) | Claude Code, no fim |
| Montar o `.docx` final (formatação do guia, índices, numeração) e contar páginas e palavras | Claude Code ou o Yanick |
| Teste no telemóvel e capturas da app | Yanick (com o R80) |
| Tarefas D2 a D4 do plano da parte 2, no Colab (opcional) | Yanick |
| Decisões que faltam na secção 3 (a 4) | Yanick |

---

## 9. Pendências que afectam o texto

1. **Teste no telemóvel das entregas 1d e 2c:** sem ele, não se pode escrever «aprovado» nos
   casos de teste dessas funcionalidades nem há capturas da app nova.
2. **Push para o GitHub:** `git push origin main feature/api feature/painel docs/pfc`.
3. **Tarefas D2 a D4 do plano da parte 2 (Colab):** se não correrem, ficam como trabalho futuro, e o «não reconhecido» também.
4. **API de áudio (14):** sem a documentação, fica como trabalho futuro.

---

## 10. Calendário sugerido

| Dia | Trabalho |
|---|---|
| 04–05/11 | Teste no telemóvel; diagramas D1 a D6; pontos de função recontados |
| 05–07/11 | Reescrita: caps. V e IV primeiro (os que mais mudam), depois II, I, III e VI, e o resumo |
| 08/11 | Montagem do `.docx`, índices, contagem de palavras e de páginas, verificação dos factos |
| 09/11 | Revisão final e envio ao supervisor |
| 10/11 | **Entrega** |
