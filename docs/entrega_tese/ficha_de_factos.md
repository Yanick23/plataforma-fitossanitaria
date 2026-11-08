# Ficha de factos da plataforma (para a versão 2 do PFC)

**Fonte de verdade para o texto.** Os factos vêm do código e dos testes a 04/11/2026.
**Regra para quem escreve:** se um número, nome ou funcionalidade não estiver aqui nem em
`03_resultados_plataforma.md`, **não o suponha**: pergunte ao Yanick. No fim, o Claude Code
confirma o texto contra o código.

---

## 1. Componentes

| Componente | Tecnologia | Tamanho (linhas de código) | Papel |
|---|---|---|---|
| App Android «Diagnóstico de culturas» | Flutter 3.38 / Dart 3.10; tflite_flutter 0.12.1; sqflite | ~5 200 (Dart, `app/lib`) | Diagnóstico sem internet, historial, sincronização, alertas, visitas, seguimento |
| API REST | FastAPI 0.115.6, Uvicorn, SQLAlchemy 2 (assíncrono), PostgreSQL (SQLite nos testes), Alembic 1.14, PyJWT, bcrypt, TensorFlow 2.17.1 / Keras (Grad-CAM), httpx (Open-Meteo) | ~4 000 (Python, `api/app`) | Dados, regras, permissões, Grad-CAM, previsão do tempo |
| Painel web | React 18.3, Vite 5.4, TypeScript 5.6, TanStack Query 5.62, padrão MVVM | ~4 900 (TS/TSX, `admin/src`) | Trabalho da equipa: validação, vigilância, alertas, visitas, boletim, gestão |
| Modelo | EfficientNetB0 por cultura, TFLite INT8 dinâmica (4 561 kB = 4,35 MiB cada; o PFC escreve «4,35 MB») | — | Classificação no telemóvel |

**Dados locais da app:**
- SQLite: o historial dos diagnósticos, com a validação do técnico e o seguimento;
- ficheiros JSON: o catálogo (`catalogo.json`), os alertas (`alertas.json`), as visitas (`visitas.json`) e o estado do modelo (`estado.json`, versão activa e SHA-256);
- token JWT (válido 30 dias, `jwt_validade_dias = 30`) no armazenamento seguro do Android.

**Arquitectura da API em camadas:** `rotas/` (HTTP, validação e permissões) → `servicos/` (regras de
negócio) → `repositorios/` (consultas).

**Painel em MVVM:**
- Model = `model/repositorios.ts` (uma função por rota da API);
- ViewModel = `viewmodels/use*ViewModel.ts` (*hooks*);
- View = `views/*View.tsx`.

**Base de dados:** 19 tabelas, migrações Alembic aplicadas no arranque:

| Migração | Conteúdo |
|---|---|
| 0001 | Base |
| 0002 | Plataforma |
| 0003 | Fase 2 |
| 0004 | Perfis e notificações |
| 0005 | Previsões do tempo |
| 0006 | Campanhas de vigilância e registo dos SMS |

---

## 2. Perfis (controlo de acesso por perfil e por zona)

| Perfil | Zona | Pode |
|---|---|---|
| Agricultor | o seu distrito | diagnosticar (app), ver o seu historial e as validações, receber alertas, pedir visita, responder ao seguimento |
| Técnico | um distrito (ou uma província, sem distrito) | validar diagnósticos, enviar alertas para a sua zona, agendar e resolver visitas, ver a vigilância e o boletim, validar o texto do catálogo, ver os agricultores da zona |
| Coordenador provincial | a província (obrigatória) | o mesmo que o técnico, na província toda, mais criar e alterar contas de técnicos e agricultores da província (e só esses dois perfis); recebe os avisos de declaração obrigatória |
| Investigador | o país todo, **só leitura** | painel, vigilância, boletim, exactidão em campo, exportação do conjunto de retreino; os agricultores aparecem com um pseudónimo («Agricultor 1EFC54», HMAC estável) e sem telefone |
| Administrador | o país todo | tudo, incluindo o catálogo, os modelos (piloto e publicação), as contas de qualquer perfil e a auditoria |

**Zonas:** as 11 províncias e os 157 distritos de Moçambique (geoBoundaries, INE/OCHA 2019).

---

## 3. Funcionalidades implementadas (por iteração)

| Iteração | Funcionalidades |
|---|---|
| 0 (v1 do PFC) | Diagnóstico offline, historial, sincronização sem duplicados (UUID), catálogo, publicação de modelo com SHA-256, Grad-CAM |
| 1a–1d | Regiões e zonas; validação pelo técnico; exactidão em campo; conjunto de retreino (ZIP + CSV); mapa de ocorrências; sinais de surto; alertas por zona com alcance e taxa de leitura; pedidos de visita; auditoria; gestão de contas; **painel web**; a app recebe alertas, validações, visitas e o distrito no registo |
| 2a–2c | Boletim fitossanitário (PDF e CSV); catálogo enriquecido (sintomas, prevenção, fotos de referência, validação do texto, versão); modelos em **piloto** por distrito, **porta de qualidade** e sinal de deriva; seguimento do tratamento aos 7 dias; pragas de declaração obrigatória; na app, verificação da qualidade da foto (nitidez e luz), várias fotos por caso (média das probabilidades) e «Como reconhecer» |
| 2d | Perfis de coordenador e investigador; **aviso imediato** ao coordenador da província e ao administrador quando se confirma um caso de declaração obrigatória (sino no painel) |
| 3a | **Risco meteorológico**: previsão Open-Meteo de 7 dias por distrito, 4 regras com fontes, cartão na Vigilância e alerta preventivo |
| 3b | **Campanhas de vigilância activa**; **SMS** dos alertas e campanhas (API Ola da Pavulla); **notificações na app sem Firebase** (consulta em segundo plano); **calendário agrícola** por província; correcção dos perfis novos na app |

**Não implementadas (decisão do Yanick):** severidade, inspecção FAMEWS, armadilhas, dados
abertos, segurança de produção (HTTPS, limite de tentativas, cópias de segurança), privacidade
(consentimento, apagar a conta). **Ficam para trabalho futuro:** machambas com GPS, organizações,
directório de apoio, «não reconhecido» e línguas locais em áudio (falta a API).

**Feitas com menos do que o planeado** (o texto do PFC deve descrever só o que existe):
- mapa de ocorrências: sem filtro por confiança nem tendência semana a semana;
- sinais de surto: sem «confirmar ou descartar» (só «Criar alerta»);
- exactidão em campo: por classe e por versão, não por distrito;
- conjunto de retreino: sem a divisão por folha;
- alertas: sem modelos de mensagem;
- boletim: só da zona de quem pede (não se escolhe a província ou o distrito).

---

## 4. Requisitos propostos para a v2

Os RF01 a RF12 e os RNF01 a RNF07 são os da v1.

| Código | Requisito | Actor |
|---|---|---|
| RF11 (actualizado) | Gerir o catálogo enriquecido: sintomas, prevenção, fotos de referência, validação do texto por um técnico, versão | Administrador; técnico valida |
| RF12 (actualizado) | Publicar modelo em piloto por distrito, promover a publicado ou retirar; porta de qualidade | Administrador |
| RF13 | Validar um diagnóstico: confirmar ou corrigir a classe, com nota ao agricultor | Técnico, coordenador |
| RF14 | Calcular a exactidão em campo (modelo × técnico), por classe e por versão | Técnico, investigador |
| RF15 | Mostrar o mapa de ocorrências por distrito | Equipa |
| RF16 | Detectar sinais de surto (subida acima do habitual por distrito e praga) | Equipa |
| RF17 | Enviar alertas por zona (distrito, província, país), com alcance previsto e taxa de leitura | Técnico, coordenador, administrador |
| RF18 | Pedir visita técnica a partir de um diagnóstico; o técnico agenda e resolve | Agricultor, técnico |
| RF19 | Perguntar aos 7 dias se seguiu a recomendação e se a planta melhorou | Agricultor |
| RF20 | Marcar pragas de declaração obrigatória e avisar logo o coordenador e o administrador quando um caso é confirmado | Administrador; sistema |
| RF21 | Mostrar o risco meteorológico dos próximos 7 dias por distrito | Equipa; Open-Meteo |
| RF22 | Gerar o boletim fitossanitário da zona (PDF e CSV) | Equipa |
| RF23 | Gerir contas, perfis e zonas de actuação | Administrador, coordenador |
| RF24 | Registar a auditoria (quem fez o quê, quando, com o antes e o depois) | Sistema; administrador consulta |
| RF25 | Exportar o conjunto de retreino (fotos validadas e rótulos) | Administrador, investigador |
| RF26 | Verificar a nitidez e a luz da foto antes de diagnosticar | Sistema (app) |
| RF27 | Combinar 2 a 3 fotos da mesma planta num só diagnóstico | Agricultor (app) |
| RNF08 | Controlo de acesso por perfil e por zona em todas as rotas | — |
| RNF09 | O investigador nunca vê nomes nem telefones de agricultores | — |
| RNF10 | Todas as alterações relevantes ficam na auditoria, no mesmo commit da alteração | — |
| RNF11 | Sem internet no servidor, o risco meteorológico usa a última previsão guardada e diz que não é recente | — |
| RF28 | Criar campanhas de vigilância activa numa zona (cultura, praga opcional, período até 60 dias) e acompanhar quem respondeu | Técnico, coordenador, administrador; investigador lê |
| RF29 | Enviar também por SMS os alertas e as campanhas, aos agricultores da zona | Técnico, coordenador, administrador; API Ola |
| RF30 | Notificar o agricultor no telemóvel (alertas, validações, visitas, campanhas) sem Firebase, por consulta em segundo plano | Sistema (app) |
| RF31 | Mostrar o calendário agrícola da província e, na app, «Nesta altura…» do mês actual, sem Internet | Agricultor, equipa |
| RNF12 | Sem fornecedor de SMS configurado, os SMS ficam registados como simulados e nada é enviado | — |

---

## 5. Base de dados (19 tabelas, para o diagrama de classes)

| Tabela | Campos principais |
|---|---|
| Provincia | codigo (ISO 3166-2), nome |
| Distrito | id, nome, provincia_codigo |
| Utilizador | id, nome, telefone, hash_palavra_passe, perfil, area, distrito_id, provincia_codigo, activo, criado_em |
| Cultura | id, nome, nome_cientifico |
| Patologia | id, cultura_id, codigo, nome_local, nome_cientifico, tipo (DOENCA, PRAGA, SAUDAVEL), recomendacao, sintomas, prevencao, declaracao_obrigatoria, versao_conteudo, validado_por_id, validado_em |
| FotoReferencia | id, patologia_id, caminho_ficheiro, legenda |
| ModeloML | id, cultura_id, versao, caminho_tflite, classes, acuracia_teste, tamanho_bytes, sha256, estado (PILOTO, PUBLICADO, RETIRADO), distritos_piloto, notas |
| Diagnostico | id (UUID do telemóvel), utilizador_id, cultura_id, classe_prevista, confianca, data, versao_modelo, tempo_inferencia_ms, recebido_em, distrito_id |
| Imagem | id, diagnostico_id, caminho_ficheiro, data_captura |
| Validacao | diagnostico_id, tecnico_id, classe_confirmada, correcto, nota |
| Seguimento | diagnostico_id, seguiu (SIM, PARCIAL, NAO), resultado (MELHOROU, IGUAL, PIOROU, NAO_SEI), comentario |
| PedidoVisita | id, diagnostico_id, agricultor_id, tecnico_id, distrito_id, estado (PENDENTE, AGENDADA, RESOLVIDA, CANCELADA), data_agendada, notas_tecnico |
| Alerta | id, titulo, mensagem, nivel (INFORMACAO, AVISO, URGENTE), patologia_id, provincia_codigo, distrito_id, autor_id, expira_em, arquivado |
| AlertaLeitura | alerta_id, utilizador_id, lido_em |
| Notificacao | id, utilizador_id, tipo, titulo, mensagem, diagnostico_id, lida_em |
| RegistoAuditoria | id, utilizador_id, accao, entidade, entidade_id, detalhes (antes e depois, em JSON) |
| PrevisaoMeteo | distrito_id, obtida_em, dados (previsão horária em JSON) |
| Campanha | id, titulo, mensagem, cultura_id, patologia_id, provincia_codigo, distrito_id, inicio, fim, autor_id, cancelada |
| EnvioSMS | id, alerta_id ou campanha_id, utilizador_id, telefone, conteudo, estado (PENDENTE, ENVIADO, FALHOU, SIMULADO), id_externo, erro |

**Diferença face à v1:** o modelo **passou a ser uma entidade persistida** (ModeloML). A frase da
v1 «o modelo de classificação não é uma entidade persistida» tem de sair.

---

## 6. API: 67 endpoints (mais `/saude`)

| Grupo | N.º | Exemplos |
|---|---|---|
| Autenticação e contas | 5 | `POST /auth/registar`, `/auth/login`, `/auth/renovar`, `GET /auth/eu`, `POST /utilizadores` |
| Diagnósticos | 6 | `POST /diagnosticos` (lote), `POST /diagnosticos/{id}/imagem`, `GET /diagnosticos/{id}/gradcam`, `POST /diagnosticos/{id}/seguimento` |
| Catálogo | 11 | culturas, patologias, `POST /patologias/{id}/validar`, fotos de referência |
| Modelos | 7 | `GET /modelos/{cultura}/ultima-versao`, `/monitorizacao`, `/{versao}/porta-qualidade`, `POST /modelos/{cultura}`, `PATCH /modelos/{cultura}/{versao}` |
| Regiões | 2 | `GET /provincias`, `GET /distritos` |
| Validação | 3 | `PUT /diagnosticos/{id}/validacao`, `GET /validacoes/exactidao`, `GET /validacoes/exportar` |
| Alertas | 6 | `GET /alertas/alcance`, `POST /alertas`, `GET /alertas/meus`, `POST /alertas/{id}/lido` |
| Visitas | 5 | `POST /visitas`, `GET /visitas/minhas`, `PATCH /visitas/{id}` |
| Gestão | 12 | `/gestao/resumo`, `/gestao/diagnosticos`, `/gestao/utilizadores`, `/gestao/auditoria`, `/gestao/boletim` (+ `.csv`), `/gestao/eficacia`, `/gestao/notificacoes` |
| Vigilância | 4 | `/vigilancia/ocorrencias`, `/surtos`, `/declaracoes`, `/risco-meteorologico` |
| Campanhas, novidades e calendário | 6 | `POST/GET /campanhas`, `GET /campanhas/minhas`, `POST /campanhas/{id}/cancelar`, `GET /novidades?desde=`, `GET /calendario?provincia=` |

Documentação automática em `/docs` (Swagger UI) e `/redoc`.

---

## 7. Testes

| O quê | Resultado |
|---|---|
| API (pytest + httpx, SQLite temporária) | **68 testes aprovados** (v1: 23; 59 até à entrega 3a). Também cobrem SMS (fornecedor simulado), campanhas, novidades e calendário. Cobrem autenticação, sincronização sem duplicados, permissões por perfil e zona, catálogo, modelos (piloto, porta de qualidade, deriva), Grad-CAM, alertas, visitas, vigilância e surtos, boletim, perfis finos, notificações, risco meteorológico (com a Open-Meteo simulada) e migração de uma base antiga |
| App (`flutter test`) | 21 testes (18 aprovados e 3 saltados nesta máquina, que precisam das fotos de calibração): qualidade da foto, combinação de fotos, seguimento, catálogo, sincronização com UUID, perfis, notificações, calendário e campanhas. APK de release arm64 compilado (36,4 MB) |
| Painel | `npm run build` sem erros; testado no Chrome com Puppeteer, contra uma API de teste (porta 8001, base temporária, **nunca a base real**), sem erros na consola |
| Migrações | 0003 → 0004 → 0003 → 0004 num PostgreSQL 16 temporário (Docker), sem erros |
| Telemóvel (SOTEN R80, Android 13) | T01 a T12 aprovados (v1). **T13 (Grad-CAM) aprovado em 25/10:** 2,4 s no 1.º pedido do milho, 2,1 s na mandioca, 0,8 s com o modelo já carregado. **Por fazer:** a confirmação no ecrã das iterações 1d e 2c (alertas, validação, visitas, qualidade da foto, várias fotos, seguimento) |

---

## 8. Resultados do modelo que ficam no texto (iguais aos da v1)

**Dados (CCMT, Gana):**
- milho: 5 288 imagens, 7 classes;
- mandioca: 7 508 imagens, 5 classes;
- divisão 70/15/15, com semente 42.

**Treino:** EfficientNetB0 em duas fases (cabeça, depois ajuste fino); o milho usa a configuração
E0b e a mandioca a E0.

**Teste:**

| Cultura | Exactidão | F1 mínimo | H1 |
|---|---|---|---|
| Mandioca | **93,1%** (1 049 de 1 127) | 0,885 | confirma |
| Milho | **87,0%** (691 de 794) | 3 classes abaixo de 0,85 (mancha 0,789, queima 0,779, saudável 0,820) | não confirma |

**Teste externo (iCassava, Uganda, 80 imagens):** **26,2%** (mudança de domínio).

**TFLite INT8:**
- 4,35 MiB por modelo (4,56 MB em unidades decimais); o PFC usa «4,35 MB» e deve manter a mesma unidade em todo o texto;
- milho 86,3%, mandioca 93,1%;
- inferência no telemóvel (SOTEN R80, Tabela 5.13 da v1), **duas medições diferentes que não se contradizem**:
  - 20 inferências com uma imagem sintética: média de 0,164 s (milho) e 0,174 s (mandioca);
  - 10 diagnósticos com fotografias reais: inferência de cerca de 0,22 s, mais 0,15 s de pré-processamento;
- diagnóstico completo em 0,374 s (milho) e 0,424 s (mandioca), muito abaixo dos 3 s do RNF03.

---

## 9. Regras do risco meteorológico

Os limiares de dias e de chuva são **limiares de projecto, a calibrar**.

| Praga ou doença | Dia favorável | Médio / alto |
|---|---|---|
| Queima da folha (milho) | média 15–30 °C e ≥ 9 h com HR ≥ 90% | 2 / ≥ 3 dias |
| Mancha cinzenta (milho) | ≥ 12 h com HR ≥ 90% entre 22 e 30 °C | 1 / ≥ 2 dias seguidos |
| Mancha castanha (mandioca), evidência fraca | média ≥ 20 °C e ≥ 12 h com HR ≥ 95% | 2 / ≥ 4 dias |
| Ácaro verde (mandioca) | pouca chuva na semana | < 10 mm / < 2 mm em 7 dias |

**Exemplo real (04/11/2026):**
- risco médio de mancha cinzenta em Manhiça;
- risco médio de ácaro verde em Chokwe (9,9 mm de chuva prevista);
- nenhum risco em Boane (33,7 mm de chuva prevista).

As fontes, que é preciso confirmar, estão na secção 7 do `roteiro_pfc_v2.md`.

---

## 10. SMS, notificações, campanhas e calendário (entrega 3b)

- **SMS (API Ola, da Pavulla):** `POST https://api.ola.pavulla.com/v1/messages/bulk`, autenticação
  HTTP Basic (token como utilizador, palavra-passe vazia) e números só com dígitos, com o indicativo
  258. São os mesmos parâmetros da integração que a Pavulla já usa no sistema AquaSystem. A
  documentação pública não os diz.
  - Os SMS ficam registados (tabela `envios_sms`) e são enviados depois de a API responder, em
    lotes de 100.
  - Sem `SMS_CHAVE` no `api/.env`, ficam como **SIMULADO**: nada sai, mas o resto funciona.
  - Configuração no `.env`: `SMS_CHAVE`, `SMS_PROVIDER_ID`, `SMS_REMETENTE` (nunca no Git).
- **Notificações sem Firebase:** a app regista uma tarefa periódica do Android (`workmanager`) que
  consulta `GET /novidades` e mostra notificações locais (`flutter_local_notifications`).
  - O Android só a corre **de 15 em 15 minutos, no mínimo**, e pode atrasá-la para poupar bateria.
  - Desde o Android 13, o agricultor tem de autorizar as notificações.
  - Com a app aberta, a sincronização avança o ponto de partida, para não repetir notificações.
- **Campanhas:** responder = sincronizar pelo menos um diagnóstico da cultura, na zona, no período
  (conta também «folha saudável»).
- **Calendário:** dados em `api/app/calendario_agricola.json`, com a fonte de cada linha.
  - Regiões FEWS NET (Norte; Centro e Sul); sementeira por província do MASA.
  - 5 avisos de confiança alta ou média. Ficaram de fora, por falta de fontes, o mosaico, a mancha
    castanha, a mancha bacteriana, o gafanhoto e o besouro.
