# Plataforma — estado, o que falta e calendário até 10/11/2026

Actualizado a **04/11/2026**.

**Branches (uma por projecto, a partir da `main`):**

| Branch | Pasta | Conteúdo |
|---|---|---|
| `feature/api` | `api/` | API FastAPI |
| `feature/painel` | `admin/` | Painel web (React + Vite + TypeScript) |
| `feature/app` | `app/` | App Flutter |
| `feature/ml` | `ml/` | Notebooks e scripts do modelo (treino, plano da parte 2: D2–D7) |
| `docs/pfc` | `docs/` | Documentação e texto para o PFC |

Cada branch só altera a sua pasta, por isso juntá-las na `main` não dá conflitos. Os commits das
entregas 1a–2c foram separados por pasta a partir da `feature/painel-admin`, que fica como cópia
de referência. As quatro juntas dão exactamente o mesmo conteúdo que ela. Uma alteração que
mexa em vários projectos (por exemplo, uma rota nova na API e o ecrã que a usa) faz um commit em
cada branch, com o mesmo assunto.

Este documento junta o plano que se combinou para a plataforma e o que já está feito. Também
diz o que falta para a entrega do PFC a **10/11/2026**. A lista das funcionalidades, com o porquê
de cada uma, está em [funcionalidades_plataforma.md](funcionalidades_plataforma.md). O plano dos
resultados do modelo (D1–D7) está em [plano_trabalho_parte2_pfc.md](plano_trabalho_parte2_pfc.md).

---

## 1. O plano combinado

**Objectivo.** Passar de uma app de diagnóstico a uma **plataforma de vigilância
fitossanitária**. O ciclo a fechar é diagnóstico → validação pelo técnico → vigilância → alerta
→ visita → relatório, com zonas de Moçambique (11 províncias, 157 distritos).

**Regras de trabalho**

- **Entregar por fases.** Cada fase fica a funcionar, testada e com commit antes da seguinte; não
  se faz tudo de uma vez para depois corrigir.
- **Cada fase entregue fica escrita no PFC**, no capítulo de Resultados
  ([03_resultados_plataforma.md](../entrega_tese/03_resultados_plataforma.md)): o que se fez, como
  se testou, números e capturas. No fim, o texto entra na última versão do PFC, que o Yanick envia
  quando a programação terminar.
- **Arquitectura.**
  - API: FastAPI em camadas (rotas → serviços → repositórios), com migrações Alembic.
  - Painel web: React + Vite + TypeScript em **MVVM**. O Model são os repositórios, o ViewModel
    são os hooks e a View são os componentes.
  - App: Flutter.
- **Interface profissional**, sem aspecto de «gerada por IA»: paleta de gráficos validada, estados
  sempre com ícone e texto, tema claro e escuro.
- **Os alertas chegam à app pela sincronização.** As notificações push (Firebase) ficam para a
  fase 4.
- **Culturas novas só no painel**, por agora.
- **Os testes que alteram dados correm numa API à parte** (porta 8001, base SQLite temporária)
  e num painel de teste (porta 5175), **nunca na base real**. Um modelo falso publicado em piloto
  chegaria aos telemóveis do distrito.

**Faseamento**

| Fase | Conteúdo | Estado |
|---|---|---|
| 1 — núcleo | Regiões, painel, mapa e surtos, validação e exactidão em campo, conjunto de retreino, alertas por zona, visitas, auditoria, gestão de contas, catálogo e modelos; na app: alertas, validação, visitas, distrito no registo | **Feita** (entregas 1a–1d) |
| 2 — gestão e qualidade | Boletim, catálogo enriquecido, modelos com piloto, porta de qualidade e deriva, qualidade da foto, várias fotos, seguimento do tratamento, declaração obrigatória, perfis finos | **Feita** (entregas 2a–2d) |
| 3 — contexto agrícola | Risco meteorológico, calendário agrícola, campanhas, inspecção de campo (FAMEWS) e armadilhas, machambas com GPS | **Risco meteorológico feito** (3a); FAMEWS e armadilhas não se fazem; o resto é trabalho futuro |
| 4 — alcance e abertura | Push, «não reconhecido», segurança de produção, privacidade, dados abertos; SMS, línguas locais, organizações e severidade como trabalho futuro | Línguas locais em áudio a fazer; «não reconhecido» depende da tarefa D4; segurança, privacidade, dados abertos e severidade não se fazem |

---

## 2. Feito até agora

| Entrega | Data | Commits | Resumo |
|---|---|---|---|
| 1a — API da plataforma | 25/10 | `02145e2` | Regiões, zonas, alertas, validação, visitas, vigilância, gestão, auditoria, Alembic; 38 testes |
| 1b — Painel web | 25/10 | `57155f9` | React + Vite + TypeScript em MVVM: painel, diagnósticos, alertas, catálogo, modelos, utilizadores |
| 1c — Painel: validação, visitas, vigilância, auditoria | 25/10 | `a131297` | Fila de validação com Grad-CAM, visitas, mapa e surtos, auditoria |
| 1d — App recebe o trabalho do técnico | 25/10 | `52df79b` | Alertas, validação, visitas e distrito no registo |
| 2a — API da fase 2 | 25/10 | `6842230`, `07b37dd` | Catálogo enriquecido, piloto, porta de qualidade, deriva, seguimento, declarações, boletim; 44 testes |
| 2b — Painel da fase 2 | 25/10 | `41c98aa`, `43768d5` | Boletim para imprimir, PDF e CSV; catálogo com fotos e validação; modelos com piloto; declarações e eficácia |
| 2c — App da fase 2 | 25/10 | `a5871f4`, `de9aa06` | Qualidade da foto, várias fotos, seguimento aos 7 dias, «Como reconhecer», piloto do modelo; 11 testes da app |
| 2d — Perfis finos e aviso da declaração obrigatória | 04/11 | ver `git log` | Coordenador provincial e investigador (anonimizado); notificações no painel; migração 0004; 52 testes na API |
| 3a — Risco meteorológico | 04/11 | ver `git log` | Open-Meteo por distrito, regras com fontes, cartão na Vigilância; migração 0005; 59 testes na API |

**Testes automáticos:** 59 na API (`pytest`) e 11 na app (`flutter test`), todos aprovados.
O painel compila sem erros (`npm run build`) e foi testado no Edge com Puppeteer.

### Estado das 24 funcionalidades

| N.º | Funcionalidade | Estado |
|---|---|---|
| 1 | Mapa de ocorrências | Feito (1c) |
| 1b | Detecção de surtos | Feito (1a, 1c) |
| 2 | Validação pelo técnico | Feito (1a, 1c, 1d) |
| 2b | Exactidão em campo | Feito (1a, 1c) |
| 2c | Conjunto de retreino local | Feito (1a, 1c) |
| 3 | Alertas por zona | Feito (1a, 1c, 1d) |
| 3b | Pragas de declaração obrigatória | Feito (2a, 2b, 2d): marcadas no catálogo, listadas na Vigilância e no boletim; um caso confirmado avisa logo o coordenador da província e o administrador (sino no painel) |
| 4 | Pedido de visita técnica | Feito (1a, 1c, 1d) |
| 4b | Seguimento do tratamento | Feito (2a, 2b, 2c); **falta ver no telemóvel** |
| 5 | Boletim fitossanitário | Feito (2a, 2b) |
| 6 | Registo de auditoria | Feito (1a, 1c) |
| 6b | Perfis finos (coordenador, investigador) | Feito (2d) |
| 6c | Organizações | Fase 4 (trabalho futuro) |
| 7 | Catálogo enriquecido | Feito (2a, 2b, 2c) |
| 8 | Modelos com piloto e deriva | Feito (2a, 2b, 2c) |
| 8b | Porta de qualidade | Feito (2a, 2b) |
| 9 | Risco meteorológico | Feito (3a): previsão Open-Meteo por distrito, 4 regras com fontes, cartão na Vigilância e alerta preventivo |
| 10 | Calendário agrícola | Feito (3b): por província, com fontes; na app, «Nesta altura…» sem Internet |
| 11 | Machambas georreferenciadas | Por fazer (fase 3) |
| 12 | Campanhas de vigilância activa | Feito (3b): painel, app e taxa de resposta |
| 13 | Alertas por SMS | Feito (3b): API Ola da Pavulla; simulado sem chave configurada |
| 13b | Notificações push | Feito (3b) **sem Firebase**: consulta em segundo plano de 15 em 15 min; **falta ver no telemóvel** |
| 14 | Línguas locais e áudio | **A fazer** com a API de áudio em línguas locais do Yanick (falta a documentação da API) |
| 15 | Verificação da fotografia | Feito (2c); **falta ver no telemóvel** |
| 16 | Várias fotos por caso | Feito (2c); **falta ver no telemóvel** |
| 17 | «Não reconhecido» | Por fazer (fase 4); depende da tarefa D4 |
| 18 | Severidade | Não se faz (decisão de 04/11) |
| 19 | Inspecção de campo (FAMEWS) | Não se faz (decisão de 04/11) |
| 20 | Armadilhas de feromona | Não se faz (decisão de 04/11) |
| 21 | Directório de apoio | Por fazer (fase 4, pequeno) |
| 22 | Dados agregados abertos | Não se faz (decisão de 04/11) |
| 23 | Segurança de produção | Não se faz (decisão de 04/11) |
| 24 | Privacidade | Não se faz (decisão de 04/11) |

---

## 3. O que falta

### 3.1 Fechar o que já foi feito

| Tarefa | Precisa de | Notas |
|---|---|---|
| Confirmação visual da **2c** no telemóvel: cartão de seguimento, resposta e envio, aviso de qualidade, «Juntar outra foto», «Como reconhecer» | R80 carregado e desbloqueado; na app, Definições → Servidor = IP do PC (hoje `http://192.168.109.58:8000`) | O APK novo (arm64, 33,4 MB) já está instalado |
| Confirmação visual da **1d** no telemóvel: alerta no ecrã inicial, ecrã de alertas, «Corrigido pelo técnico», visita agendada, listas no registo | O mesmo | Adiada desde 25/10 |
| **Apagar a foto de referência de teste** do Gafanhoto (id 1, «foto de teste») | Depois do teste da 2c | Foi posta na base real só para o telemóvel a descarregar |

### 3.2 Fase 3 — contexto agrícola

- **Risco meteorológico (9): feito** (entrega 3a, 04/11).
- **Línguas locais em áudio (14): a fazer**, com a API de áudio do Yanick. Falta a documentação
  da API.
- **Calendário agrícola (10) e campanhas de vigilância activa (12): feitos** (entrega 3b).
- **Trabalho futuro no PFC:** machambas com GPS (11).
- **Não se fazem** (decisão de 04/11): inspecção de campo FAMEWS (19) e armadilhas de
  feromona (20).

### 3.3 Fase 4 — alcance e abertura

- **«Não reconhecido» (17):** só se a tarefa D4 do Colab tiver resultados a tempo; senão, fica
  como trabalho futuro.
- **SMS (13) e notificações sem Firebase (13b): feitos** (entrega 3b).
- **Trabalho futuro no PFC:** organizações (6c) e directório de apoio (21).
- **Não se fazem** (decisão de 04/11): severidade (18), dados abertos (22), segurança de
  produção (23) e privacidade (24).
  - A segurança (HTTPS, cópias de segurança, trocar a palavra-passe do administrador e o
    `JWT_SEGREDO`) e a privacidade ficam só como **recomendações** no PFC, antes de qualquer
    instalação real.

### 3.4 Resultados do modelo (plano da parte 2)

O Yanick indica (04/11) que a versão `PROD_corrigido` do PFC já tem os resultados das tarefas
D2, D4 e D5. A versão que está neste repositório (`docs/PFC_..._LAST_VERSION.docx`) ainda não os
tem. A reescrita da v2 parte da `PROD_corrigido`.

### 3.5 Texto do PFC

- O Yanick envia a **última versão do PFC**.
- Integrar no capítulo de Resultados as secções 1a–2c (e as seguintes) de
  [03_resultados_plataforma.md](../entrega_tese/03_resultados_plataforma.md), com as figuras de
  `docs/entrega_tese/dados_web/`.
- Rever a Metodologia e as Conclusões para reflectir a plataforma. No trabalho futuro entra o que
  ficar por fazer.
- Juntar os resultados da parte 2 (D2–D7).

---

## 4. Calendário proposto (26/10 a 10/11)

| Dias | Trabalho |
|---|---|
| 26–27/10 | Teste no telemóvel (1d e 2c), quando houver bateria. Perfis finos (6b) e aviso da declaração obrigatória (3b). **Colab:** teste rápido do notebook; D3 a correr de noite |
| 28/10–01/11 | Fase 3: 3a (API: meteorologia, calendário, campanhas), 3b (painel), 3c (app). Inspecção, armadilhas e GPS, se couberem. **Colab:** D2 e D4 |
| 02–05/11 | Fase 4 essencial: «não reconhecido», segurança e privacidade; push, se houver tempo. D5. D7, se as fotos chegarem |
| 06–09/11 | Texto do PFC (com a última versão enviada pelo Yanick), capturas finais, revisão e ensaio da apresentação |
| 10/11 | **Entrega** |

---

## 5. Notas práticas

- **Correr a API:** `cd api; .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000`.
  As migrações Alembic correm no arranque.
- **Antes de uma migração na base real,** fazer cópia de segurança com `pg_dump`. As cópias
  ficam em `api/dados/backups/` e estão fora do Git.
- **Correr o painel:** `cd admin; npx vite --port 5174`. A porta 5173 está ocupada por outro
  projecto.
- **Testes:**
  - `cd api; .\.venv\Scripts\python.exe -m pytest -q`;
  - `cd app; flutter test`;
  - `cd admin; npm run build`.
- **APK para o R80:** `flutter build apk --release --split-per-abi` e instalar o
  `app-arm64-v8a-release.apk`. O APK universal tem 80 MB, porque leva três arquitecturas.
- **As contas de teste e as palavras-passe** estão no `api/.env` e nas notas do Yanick, nunca no
  Git.
- **Alteração local por decidir:** em `app/lib/screens/detalhe_diagnostico_screen.dart` a legenda
  do Grad-CAM foi trocada por `'.'` na cópia de trabalho. Não entrou em nenhum commit; os
  commits mantêm a legenda original.
