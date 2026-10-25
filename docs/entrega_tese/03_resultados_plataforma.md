# Resultados — plataforma de vigilância fitossanitária (para o capítulo de Resultados do PFC)

Cada entrega é registada aqui quando fica concluída: o que foi feito, como foi testado e os
números obtidos. Ramo `feature/painel-admin`.

---

## Entrega 1a — API da plataforma (25/10/2026)

### O que foi implementado

A API passou de um serviço de sincronização a uma plataforma de vigilância. Mantém o FastAPI e
fica organizada em três camadas: **rotas** (HTTP e permissões) → **serviços** (regras de
negócio) → **repositórios** (consultas). As alterações ao esquema da base de dados passam a ser
geridas com **migrações Alembic**, aplicadas automaticamente no arranque.

| Área | Funcionalidade | Rotas principais |
|---|---|---|
| Regiões | 11 províncias e 157 distritos de Moçambique (INE/OCHA 2019, via geoBoundaries). Cada agricultor fica ligado a um distrito; cada técnico a um distrito ou a uma província; o administrador actua no país todo. O distrito escrito em texto livre no registo («Boane», «chokwe») é reconhecido automaticamente | `GET /provincias`, `GET /distritos` |
| Alertas por zona | Alerta para um distrito, uma província ou o país todo, com nível (informação/aviso/urgente), praga associada e validade. O técnico só envia para a sua zona. O **alcance previsto** é calculado antes do envio e a **taxa de leitura** depois | `GET /alertas/alcance`, `POST /alertas`, `GET /alertas`, `GET /alertas/meus`, `POST /alertas/{id}/lido` |
| Validação pelo técnico | O técnico confirma ou corrige a classe prevista e deixa uma nota; o agricultor recebe a correcção na sincronização | `PUT /diagnosticos/{id}/validacao` |
| Exactidão em campo | Concordância modelo × técnico, por classe, versão do modelo e pares confundidos | `GET /validacoes/exactidao` |
| Conjunto de retreino | ZIP com as fotografias validadas (pasta por cultura/classe) e `rotulos.csv` | `GET /validacoes/exportar` |
| Pedidos de visita | O agricultor pede ajuda a partir de um diagnóstico; o técnico agenda (com data), resolve ou cancela, segundo transições controladas | `POST /visitas`, `GET /visitas`, `PATCH /visitas/{id}` |
| Vigilância | Ocorrências por distrito (mapa) e detecção de surtos: casos dos últimos 7 dias contra a média das 4 semanas anteriores (mínimo de 3 casos, subida de 2 vezes; urgente a partir de 4 vezes) | `GET /vigilancia/ocorrencias`, `GET /vigilancia/surtos` |
| Gestão | Indicadores da zona (série diária, classes, distritos), diagnósticos com filtros e paginação (incl. fila por confiança crescente), contas (perfil, zona, activar/desactivar, repor palavra-passe) | `GET /gestao/resumo`, `GET /gestao/diagnosticos`, `GET/PATCH /gestao/utilizadores` |
| Auditoria | Registo de quem alterou o catálogo, publicou modelos, criou/alterou contas, enviou alertas, validou diagnósticos ou mexeu em visitas, com valores antes/depois | `GET /gestao/auditoria` |
| Segurança | Contas desactivadas deixam de entrar; perfil «pessoal» (técnico ou administrador) para as rotas de gestão; CORS para o painel web | — |

Novas tabelas: `provincias`, `distritos`, `alertas`, `alertas_leituras`, `validacoes`,
`pedidos_visita`, `auditoria`; novas colunas em `utilizadores` (distrito, província, activo) e em
`diagnosticos` (distrito no momento da sincronização).

### Como foi testado

- **Testes automáticos:** `pytest` passou de 23 para **38 testes, todos aprovados** (os 23
  anteriores continuam a passar). Os 15 novos cobrem regiões, zona no registo, conta desactivada,
  promoção a técnico e reposição de palavra-passe, visibilidade por zona, alertas por zona
  (alcance, permissões, entrega, leitura, arquivo, validade), validação e exactidão em campo,
  exportação para retreino, ciclo do pedido de visita, detecção de surto, painel, fotografia do
  diagnóstico, auditoria e **migração de uma base criada antes do Alembic**.
- **Migração da base real (PostgreSQL 18.1):** depois de uma cópia de segurança (`pg_dump`), a
  base usada nos testes T01–T13 foi migrada no arranque da API para a revisão `0002`, sem perda
  de dados. Os 3 utilizadores e os 35 diagnósticos mantiveram-se; as contas antigas ficaram
  ligadas ao distrito escrito na área (Boane; Maputo → Cidade de Maputo) e os 35 diagnósticos
  ficaram com distrito.
- **Verificação com dados reais:** o resumo nacional devolveu 2 agricultores, 35 diagnósticos
  (1 com confiança abaixo de 60%), Boane com 29 diagnósticos (25 de pragas/doenças) e Cidade de
  Maputo com 6. A fila de validação ordena os menos certos primeiro (58%, 66%, 69%).

### Limitações da entrega 1a

- Sem histórico (todos os diagnósticos de teste são recentes), a detecção de surtos assinala
  qualquer praga com 3 ou mais casos; com semanas de dados, a comparação com a média passa a pesar.
- As 2 unidades «Ilha Licom» e «Ilha Risunodo» do ADM2 (ilhas Likoma e Chizumulu, do Malawi) foram
  excluídas; os nomes dos distritos seguem a fonte, sem acentos em alguns casos (ex.: «Chokwe»).
- Os alertas chegam à app na sincronização (sem notificações push nesta fase).

---

## Entrega 1b — Painel web de gestão (25/10/2026)

### O que foi implementado

Painel web para técnicos e administradores, em **React 18 + Vite 5 + TypeScript**, organizado
segundo a arquitectura **MVVM**:

- **Model** (`src/model/`): tipos do domínio iguais aos esquemas da API, cliente HTTP (Axios)
  com o token JWT e mensagens de erro da API, e repositórios (uma função por rota).
- **ViewModel** (`src/viewmodels/`): um hook por ecrã, com o estado, os filtros, os pedidos
  (TanStack Query, com cache e invalidação depois de cada alteração) e as acções.
- **View** (`src/views/`): componentes de apresentação, sem pedidos à API nem regras de negócio.

| Ecrã | O que mostra / permite |
|---|---|
| Entrada | Login por telefone e palavra-passe; recusa contas de agricultor (usam a app) |
| Painel | Indicadores da zona (diagnósticos e variação face ao período anterior, agricultores, distritos afectados, confiança baixa), colunas diárias de doenças e pragas, pragas mais frequentes, **mapa de Moçambique por distrito**, sinais de surto e casos menos certos por validar; períodos de 7, 30 e 90 dias |
| Diagnósticos | Lista paginada com filtros (cultura, praga, província, distrito, período, estado da validação, confiança abaixo de 60%, ordem); detalhe com fotografia, **Grad-CAM** e **validação** (confirmar ou corrigir, com nota para o agricultor) |
| Alertas | Histórico com alcance e taxa de leitura; composição com nível, praga associada, zona de destino (limitada ao perfil), validade, **número de destinatários calculado antes do envio** e **pré-visualização no telemóvel**; arquivar |
| Culturas e pragas | Catálogo por cultura com pesquisa; editor de nome local, nome científico, tipo e recomendação com **pré-visualização do ecrã de resultado da app**; criar cultura e praga/doença; só o administrador altera |
| Modelos | Versão em uso, exactidão, tamanho e classes; histórico de versões; publicação de um `.tflite` com **SHA-256 calculado no navegador** e comparado com o guardado pela API |
| Utilizadores | Pesquisa e filtros (perfil, província, distrito, estado); criar contas de técnico/administrador, atribuir zona (distrito ou província), mudar perfil, desactivar e repor palavra-passe |

Interface em português de Moçambique, tipografia IBM Plex, verde da app como cor de marca,
**modo claro e escuro**. Os gráficos seguem regras de visualização acessível: paleta categórica
validada para daltonismo (azul/laranja, todas as verificações aprovadas nos dois modos),
escala sequencial de uma só cor no mapa, legenda, dicas ao passar o rato e níveis de alerta
sempre com ícone e texto.

### Como foi testado

- `tsc --noEmit` em modo estrito sem erros; `vite build` de produção concluído (349 KB de
  JavaScript, 114 KB comprimido).
- Execução contra a API real (PostgreSQL com os dados dos testes T01–T13) e captura de todos
  os ecrãs (figuras em `docs/entrega_tese/dados_web/1b_*.png`): o painel nacional mostra
  35 diagnósticos, 2 distritos com casos (Boane e Cidade de Maputo), 5 sinais de surto e a fila
  dos menos certos (58%, 66%, 69%…), e o mapa colore Boane.
- Durante a verificação foram encontrados e corrigidos dois defeitos: o mapa desenhava-se
  como um rectângulo (orientação dos polígonos invertida para o d3-geo; corrigido no gerador
  do mapa) e as barras de confiança não mostravam o preenchimento (elemento inline sem largura).

### Limitações da entrega 1b

- As gavetas (validar, compor alerta, editar recomendação, publicar modelo) foram verificadas
  no código e na compilação, mas as capturas automáticas só cobrem as listas (o navegador sem
  interface não clica). A verificação manual completa fica para a entrega 1c.
- Ainda sem os ecrãs de Validação (fila e exactidão em campo), Visitas, Vigilância (surtos) e
  Auditoria: são a entrega 1c.

---

## Entrega 1c — Validação, visitas, vigilância e auditoria no painel (25/10/2026)

### O que foi implementado

Quatro ecrãs novos no painel (mesma arquitectura MVVM), que fecham o ciclo
**diagnóstico → validação → vigilância → alerta → visita**:

| Ecrã | O que mostra / permite |
|---|---|
| Validação | Fila dos diagnósticos por validar (menos certos primeiro; depois de validar abre o seguinte); **exactidão em campo** (concordância modelo × técnico), exactidão por praga, pares que o modelo confunde e exactidão por versão do modelo; **exportação do conjunto de retreino** (ZIP, só administrador) |
| Visitas | Pedidos dos agricultores por estado (contador de pendentes na navegação); agendar com data e hora, reagendar, resolver ou cancelar, com notas que o agricultor vê |
| Vigilância | Sinais de surto com janela (7/14 dias) e sensibilidade (sensível, normal, conservador); **«Criar alerta» abre o alerta já preenchido** (título, mensagem com a recomendação do catálogo, nível, praga e distrito); mapa e ranking de ocorrências por cultura, praga e período |
| Auditoria | Registo de todas as alterações (só administrador), com filtro por tipo e detalhe campo a campo (antes → depois) |

### Como foi testado

Teste ponta-a-ponta automatizado: um navegador real (Microsoft Edge, conduzido com
`puppeteer-core`) entra no painel e executa as acções como um utilizador, contra a API e a
base de dados reais. **9 de 9 passos aprovados, sem erros na consola do navegador:**

1. Diagnósticos — abrir o caso de 58% (previsto «mancha cinzenta»), ver a fotografia e o
   Grad-CAM, corrigir para «listrado do milho» com nota → «Correcção registada».
2. Validação — exactidão em campo passa a 1 validado, 1 corrigido, 34 por validar; o par
   «mancha cinzenta → listrado do milho» aparece em «O modelo confunde».
3. Alertas — compor um alerta urgente de gafanhoto para Boane; o rodapé mostra «Vai chegar a
   1 agricultor(es) · Distrito de Boane» antes do envio → «Alerta enviado a 1 agricultor(es)».
4. Vigilância — «Criar alerta» num surto abre o alerta preenchido («Mancha cinzenta da folha
   em Boane»).
5. Visitas — agendar o pedido de visita do agricultor (gafanhoto) → «Visita agendada».
6. Utilizadores — criar a conta «Técnica de Boane» (técnico, distrito de Boane) → «Conta criada».
7. Catálogo — editor de recomendação com a pré-visualização do ecrã da app.
8. Modelos — gaveta de publicação com as 5 classes da versão actual pré-preenchidas.
9. Auditoria — lista e detalhe (antes → depois) das acções anteriores.

Teste da vista do **técnico** (conta criada no passo 6): zona «Boane, Maputo»; a Auditoria não
aparece; no alerta, a província e o distrito ficam fixos em Maputo/Boane (1 destinatário); em
Utilizadores vê apenas o agricultor da sua zona.

TypeScript estrito sem erros; build de produção 375 KB (120 KB comprimido).
Capturas: `docs/entrega_tese/dados_web/1c_*.png` (16 figuras).

### Limitações da entrega 1c

- A detecção de surtos só ganha significado com semanas de dados; com os dados de teste
  (todos recentes) todos os sinais são «sem histórico».
- A exactidão em campo tem, por agora, uma só validação; é um indicador que cresce com o uso.
- O agricultor ainda não vê na app o alerta, a correcção nem a visita agendada: é a entrega 1d.

---

## Entrega 1d — A app recebe o trabalho do técnico (25/10/2026)

### O que foi implementado (app Flutter)

| Funcionalidade | Como funciona na app |
|---|---|
| Alertas da zona | Na sincronização, a app pede `GET /alertas/meus` e guarda os alertas no telemóvel (`alertas.json`), para se lerem sem rede. Ecrã inicial com **sino e número de alertas por ler** e **cartão do último alerta novo**; ecrã «Alertas» com o detalhe e a recomendação da praga associada. Abrir um alerta sem rede marca-o como lido localmente; a leitura é enviada (`POST /alertas/{id}/lido`) na sincronização seguinte |
| Validação do técnico | A sincronização pede `GET /diagnosticos` e grava no historial (SQLite, versão 2 com migração) o estado: **«Confirmado pelo técnico»** ou **«Corrigido pelo técnico»**, a classe confirmada e a nota. No detalhe, se o técnico corrigiu, o nome e a **recomendação passam a ser os da classe correcta**, com a indicação do que a app tinha previsto |
| Pedido de visita | Botão **«Pedir visita do técnico»** no detalhe de um diagnóstico sincronizado (com mensagem opcional; precisa de rede). O estado (à espera, agendada com data e técnico, feita) e as notas do técnico chegam na sincronização (`GET /visitas/minhas`) |
| Distrito no registo | Província e distrito escolhidos em **listas** (11 províncias, 157 distritos, `GET /provincias` e `GET /distritos`), em vez de texto livre; o distrito decide que alertas o agricultor recebe |
| API | `GET /alertas/meus` passa a devolver também o código da praga (`patologia_codigo`), para a app a encontrar no catálogo local |

A mensagem da sincronização resume as novidades (ex.: «1 alerta(s) novo(s) · 1 diagnóstico(s) revisto(s) pelo técnico · 1 visita(s) actualizada(s)»).

### Como foi testado

- `flutter analyze`: sem problemas; APK de release compilado (46,0 MB) e instalado no SOTEN R80.
- API: 38 testes aprovados (o teste dos alertas verifica o novo `patologia_codigo`).
- **Sincronização real no telemóvel:** depois de instalar a nova versão, a API registou os pedidos novos da app — `GET /diagnosticos`, `GET /alertas/meus` e `GET /visitas/minhas`, todos com resposta 200 — logo a seguir aos já existentes (renovar token, catálogo, modelos). Nesse momento havia na base: 1 alerta urgente para Boane, 1 diagnóstico corrigido pelo técnico e 1 visita agendada (criados no teste da entrega 1c).

### Por fazer nesta entrega

- **Confirmação visual no telemóvel** (capturas do ecrã inicial com o alerta, do ecrã de alertas, do historial com «Corrigido pelo técnico», do detalhe com a nota e a visita agendada, e do registo com as listas): adiada porque o telemóvel estava com 6% de bateria e em uso. Fazer quando estiver a carregar.

---

## Entrega 2a — API da fase 2: conteúdo, modelos, seguimento e boletim (25/10/2026)

### O que foi implementado

| Área | Funcionalidade | Rotas principais |
|---|---|---|
| Catálogo enriquecido | Cada praga/doença passa a ter **sintomas**, **prevenção** e a indicação de **declaração obrigatória**, além da recomendação. Os textos iniciais das 12 classes foram escritos e entram na base no arranque | `GET/PUT /patologias/{id}` |
| Revisão do conteúdo | O texto que o agricultor lê tem **versão**. Um técnico (ou o administrador) **valida** o conteúdo; se o texto mudar depois, a versão sobe e a validação é retirada, porque o texto novo ainda não foi revisto | `POST /patologias/{id}/validar` |
| Fotografias de referência | O administrador junta fotografias de exemplo (JPEG/PNG, até 5 MB, com legenda) a cada praga/doença; são públicas para a app as poder guardar e mostrar sem rede | `POST /patologias/{id}/fotos`, `GET/DELETE /fotos-referencia/{id}` |
| Versões piloto do modelo | Uma versão nova pode ser publicada só para alguns distritos (**piloto**). A app de um agricultor desses distritos recebe a versão piloto; os restantes continuam na versão **publicada**. Uma versão pode ser **retirada**, e todos voltam à anterior | `POST /modelos/{cultura}`, `PATCH /modelos/{cultura}/{versao}`, `GET /modelos/{cultura}/ultima-versao` |
| Porta de qualidade | Para passar de piloto a publicado, a versão precisa de **pelo menos 10 diagnósticos validados em campo** e de uma exactidão **não inferior** à da versão publicada. O administrador pode forçar a promoção; fica registado na auditoria | `GET /modelos/{cultura}/{versao}/porta-qualidade` |
| Monitorização do modelo | Por semana e versão: número de diagnósticos, confiança média, proporção abaixo de 60% e exactidão em campo. **Sinal de deriva** quando a proporção de confiança baixa nas últimas 2 semanas sobe 10 pontos ou mais face às primeiras semanas da versão (com pelo menos 20 diagnósticos recentes) | `GET /modelos/{cultura}/monitorizacao` |
| Seguimento do tratamento | Dias depois do diagnóstico, o agricultor responde se seguiu a recomendação (sim/em parte/não) e se a planta melhorou. Responder outra vez substitui a resposta | `POST /diagnosticos/{id}/seguimento` |
| Eficácia das recomendações | Por praga/doença: respostas, quantos seguiram a recomendação e, desses, quantos viram melhoria | `GET /gestao/eficacia` |
| Declaração obrigatória | Casos de pragas/doenças de declaração obrigatória na zona, marcados como **suspeita** (só o modelo) ou **confirmado** (validado pelo técnico), com o contacto do agricultor | `GET /vigilancia/declaracoes` |
| Boletim fitossanitário | Resumo da zona num período (por omissão, 30 dias): diagnósticos, agricultores activos e novos, confiança baixa, exactidão em campo, principais pragas, distritos mais afectados, alertas, surtos, visitas, declarações e eficácia. Exportação **CSV** por distrito, cultura e praga (abre directamente no Excel) | `GET /gestao/boletim`, `GET /gestao/boletim.csv` |

Migração `0003`: novas colunas em `patologias` (sintomas, prevenção, declaração obrigatória,
versão do conteúdo, validação) e em `modelos_ml` (estado, distritos do piloto, notas); novas
tabelas `fotos_referencia` e `seguimentos`.

### Como foi testado

- **Testes automáticos:** `pytest` passou de 38 para **44 testes, todos aprovados**. Os 6 novos
  usam uma cultura criada só para o teste, e cobrem:
  - versão e validação do conteúdo, incluindo o caso em que mudar só a declaração obrigatória
    mantém a validação;
  - fotografias de referência: permissões, tipo de ficheiro, acesso público e remoção;
  - piloto por distrito: um agricultor de Boane recebe a v2, um de Moamba a v1;
  - porta de qualidade: fechada com 0 validações e aberta com 10 validações e 90% de exactidão;
    depois a promoção e a retirada da versão;
  - sinal de deriva numa versão cuja confiança caiu nas últimas semanas;
  - seguimento: substituição da resposta e eficácia de 50% (2 seguiram, 1 melhorou);
  - declarações suspeitas e confirmadas, boletim, CSV e intervalo de datas inválido.
- **Migração da base real (PostgreSQL 18.1):** depois de uma cópia de segurança (`pg_dump`), a
  API migrou a base para a revisão `0003` no arranque, sem erros. As 12 classes ficaram com
  sintomas e prevenção, as 2 versões do modelo do milho ficaram como «publicado», e o boletim
  nacional devolveu os 35 diagnósticos, 1 validado e as 8 principais pragas.

### Limitações da entrega 2a

- Os sintomas e a prevenção iniciais foram escritos a partir da literatura usada no PFC e ainda
  **não foram revistos por um técnico**: na base aparecem como conteúdo por validar.
- A porta de qualidade depende das validações dos técnicos; sem elas, só a promoção forçada é
  possível (e fica na auditoria).
- O seguimento já é recebido pela API, mas a app ainda não pergunta ao agricultor (entrega 2c).
- O boletim é gerado em JSON e CSV; a versão para imprimir em PDF fica no painel (entrega 2b).

---

## Entrega 2b — Painel da fase 2 (em curso)

### Boletim fitossanitário no painel (25/10/2026)

Nova página **Boletim** no menu «Visão geral». Mostra o boletim da zona de quem o abre: o
administrador vê o país, um técnico de Boane vê «Boane, Maputo». O período escolhe-se com atalhos
(7, 30 ou 90 dias, mês anterior) ou com datas à escolha.

| Parte do boletim | Conteúdo |
|---|---|
| Cabeçalho | Zona, período, data de geração e quem o preparou |
| 1. Síntese | Parágrafos escritos automaticamente a partir dos números (ex.: «A ocorrência mais frequente foi Mancha cinzenta da folha (Milho), com 6 casos; o distrito com mais casos foi Boane (25).») |
| 2. Indicadores | Diagnósticos, agricultores activos e novos, confiança abaixo de 60%, exactidão em campo, alertas, sinais de surto, visitas resolvidas e tempo médio até resolver |
| 3–4. Gráficos | Principais pragas e doenças; distritos mais afectados |
| 5–8. Tabelas | Sinais de surto; casos de declaração obrigatória (suspeita/confirmado); alertas emitidos com a taxa de leitura; eficácia das recomendações |
| Notas | Como cada número é calculado (origem dos dados, distrito, classe corrigida, exactidão, regra de surto) |

- **Imprimir ou PDF:** o botão usa a impressão do navegador, com uma folha de estilos própria
  (A4, sem menu nem botões, sempre em fundo claro, mesmo com o painel no tema escuro). O título do
  documento dá o nome ao PDF guardado (ex.: «Boletim fitossanitário — Moçambique — 2026-09-26 a 2026-10-25»).
- **Privacidade:** o telefone do agricultor nos casos de declaração obrigatória aparece no ecrã,
  mas **não sai na impressão**, porque um boletim impresso circula.
- **CSV:** descarrega as contagens por distrito, cultura e praga do mesmo período.
- Ajuste na API: os alertas do boletim passaram a vir completos (destino, nível, praga, leituras),
  e as pragas aparecem com o nome da cultura («Milho» em vez de «milho»).

**Como foi testado:** 44 testes da API aprovados (o teste do boletim verifica o alerta). No
navegador (Edge, automatizado), com os dados reais: boletim nacional com os 35 diagnósticos,
31 com praga ou doença, 5 sinais de surto e 1 alerta urgente lido por 1 de 1 agricultor; boletim
do técnico de Boane; atalho «Mês anterior» = 01/09 a 30/09/2026; sem erros na consola; sem
deslocamento horizontal num ecrã de telemóvel (390 px). O PDF gerado tem 3 páginas A4 e sai em
fundo claro também a partir do tema escuro.

Figuras: `dados_web/2b_01_boletim_admin.png` (boletim nacional), `dados_web/2b_04_boletim_tecnico.png`
(técnico de Boane), `dados_web/2b_03_boletim_escuro.png` (tema escuro) e `dados_web/2b_boletim_exemplo.pdf` (PDF impresso).
