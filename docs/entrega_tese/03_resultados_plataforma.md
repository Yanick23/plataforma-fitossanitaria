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
