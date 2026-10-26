# Plataforma — estado, o que falta e calendário até 10/11/2026

Actualizado a **26/10/2026**.

**Branches (uma por projecto, a partir da `main`):**

| Branch | Pasta | Conteúdo |
|---|---|---|
| `feature/api` | `api/` | API FastAPI |
| `feature/painel` | `admin/` | Painel web (React + Vite + TypeScript) |
| `feature/app` | `app/` | App Flutter |
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
| 2 — gestão e qualidade | Boletim, catálogo enriquecido, modelos com piloto, porta de qualidade e deriva, qualidade da foto, várias fotos, seguimento do tratamento, declaração obrigatória, perfis finos | **Feita, menos os perfis finos** (entregas 2a–2c) |
| 3 — contexto agrícola | Risco meteorológico, calendário agrícola, campanhas, inspecção de campo (FAMEWS) e armadilhas, machambas com GPS | Por fazer |
| 4 — alcance e abertura | Push, «não reconhecido», segurança de produção, privacidade, dados abertos; SMS, línguas locais, organizações e severidade como trabalho futuro | Por fazer |

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

**Testes automáticos:** 44 na API (`pytest`) e 11 na app (`flutter test`), todos aprovados.
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
| 3b | Pragas de declaração obrigatória | **Parcial** (2a, 2b): os casos são marcados e listados na Vigilância e no boletim. **Falta:** avisar logo o coordenador e o administrador quando um caso é confirmado |
| 4 | Pedido de visita técnica | Feito (1a, 1c, 1d) |
| 4b | Seguimento do tratamento | Feito (2a, 2b, 2c); **falta ver no telemóvel** |
| 5 | Boletim fitossanitário | Feito (2a, 2b) |
| 6 | Registo de auditoria | Feito (1a, 1c) |
| 6b | Perfis finos (coordenador, investigador) | **Por fazer** (fase 2) |
| 6c | Organizações | Fase 4 (trabalho futuro) |
| 7 | Catálogo enriquecido | Feito (2a, 2b, 2c) |
| 8 | Modelos com piloto e deriva | Feito (2a, 2b, 2c) |
| 8b | Porta de qualidade | Feito (2a, 2b) |
| 9 | Risco meteorológico | Por fazer (fase 3) |
| 10 | Calendário agrícola | Por fazer (fase 3) |
| 11 | Machambas georreferenciadas | Por fazer (fase 3) |
| 12 | Campanhas de vigilância activa | Por fazer (fase 3) |
| 13 | Alertas por SMS | Fase 4 (trabalho futuro: exige contrato com operadora) |
| 13b | Notificações push | Por fazer (fase 4) |
| 14 | Línguas locais e áudio | Fase 4 (trabalho futuro: exige tradutores) |
| 15 | Verificação da fotografia | Feito (2c); **falta ver no telemóvel** |
| 16 | Várias fotos por caso | Feito (2c); **falta ver no telemóvel** |
| 17 | «Não reconhecido» | Por fazer (fase 4); depende da tarefa D4 |
| 18 | Severidade | Trabalho futuro (precisa de um modelo de segmentação) |
| 19 | Inspecção de campo (FAMEWS) | Por fazer (fase 3) |
| 20 | Armadilhas de feromona | Por fazer (fase 3) |
| 21 | Directório de apoio | Por fazer (fase 4, pequeno) |
| 22 | Dados agregados abertos | Por fazer (fase 4) |
| 23 | Segurança de produção | Por fazer (fase 4) |
| 24 | Privacidade | Por fazer (fase 4) |

---

## 3. O que falta

### 3.1 Fechar o que já foi feito

| Tarefa | Precisa de | Notas |
|---|---|---|
| Confirmação visual da **2c** no telemóvel: cartão de seguimento, resposta e envio, aviso de qualidade, «Juntar outra foto», «Como reconhecer» | R80 carregado e desbloqueado; na app, Definições → Servidor = IP do PC (hoje `http://192.168.109.58:8000`) | O APK novo (arm64, 33,4 MB) já está instalado |
| Confirmação visual da **1d** no telemóvel: alerta no ecrã inicial, ecrã de alertas, «Corrigido pelo técnico», visita agendada, listas no registo | O mesmo | Adiada desde 25/10 |
| **Apagar a foto de referência de teste** do Gafanhoto (id 1, «foto de teste») | Depois do teste da 2c | Foi posta na base real só para o telemóvel a descarregar |
| **Perfis finos (6b)**: coordenador provincial (vê e gere a província) e investigador (só leitura, dados anonimizados) | — | Cerca de 1 dia (API, painel e testes) |
| **Declaração obrigatória (3b)**: aviso ao coordenador e ao administrador quando um caso é confirmado | Perfis finos | Por exemplo, um aviso no painel e no registo |

### 3.2 Fase 3 — contexto agrícola

Por ordem de prioridade. Se o tempo não chegar, as últimas passam para trabalho futuro no PFC.

1. **Risco meteorológico (9).** Previsão por distrito com a Open-Meteo, que é grátis e não pede
   chave. Regras simples, por exemplo: humidade alta e chuva durante vários dias aumentam o risco
   de queima da folha e de mancha cinzenta. O técnico vê o aviso no painel e pode transformá-lo
   em alerta.
2. **Calendário agrícola por província (10).** Épocas de sementeira e riscos típicos por mês. A
   app mostra «nesta altura, vigie…».
3. **Campanhas de vigilância activa (12).** O técnico pede aos agricultores de uma zona que
   fotografem as plantas nessa semana e vê quantos responderam.
4. **Inspecção de campo estruturada (19) e armadilhas de feromona (20).** Formulário do técnico
   alinhado com o FAMEWS da FAO para a lagarta-do-cartucho e registo semanal de capturas.
5. **Machambas com GPS (11),** com consentimento explícito do agricultor.

Entregas previstas: 3a (API), 3b (painel), 3c (app), cada uma testada e escrita no PFC.

### 3.3 Fase 4 — alcance e abertura

A fazer (o que mais pesa na defesa):

- **«Não reconhecido» (17):** «isto não parece milho nem mandioca», em vez de forçar uma classe
  (o caso da folha de manga). Usa o resultado da D4.2.
- **Segurança de produção (23):**
  - HTTPS;
  - limite de tentativas de login;
  - cópias de segurança automáticas da base de dados e da pasta de imagens;
  - **trocar a palavra-passe do administrador e o `JWT_SEGREDO`** antes de qualquer instalação
    real.
- **Privacidade (24):** consentimento no registo, anonimização nas exportações, apagar a conta e
  os dados a pedido.
- **Notificações push (13b),** se houver tempo.
- **Dados agregados abertos (22)** e **directório de apoio (21),** se houver tempo.

Entram no PFC como trabalho futuro fundamentado: SMS (13), línguas locais e áudio (14),
organizações (6c) e severidade (18).

### 3.4 Resultados do modelo (plano da parte 2)

| Tarefa | Quem | Notas |
|---|---|---|
| Teste rápido do notebook `03_parte2.ipynb` no Colab | Yanick (Colab com GPU) | Secção 2 do notebook |
| D2, D3, D4 | Colab | D3 demora cerca de 5 h e pode correr de noite |
| D5 — teste externo do milho | Agente | Procurar um conjunto público de fora do Gana |
| D6 (opcional) | Colab | Só se sobrar tempo |
| D7 — fotos locais | Yanick tira as fotos; o agente analisa | 30–50 fotos com `rotulos.csv` |

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
