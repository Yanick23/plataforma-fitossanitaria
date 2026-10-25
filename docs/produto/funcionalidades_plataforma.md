# Plataforma de vigilância fitossanitária — funcionalidades e faseamento

Base: o que o sistema já tem. Cada diagnóstico regista **cultura, praga ou doença, confiança,
fotografia, data, versão do modelo e distrito do agricultor**, feito offline no telemóvel e
sincronizado com a API. Hoje esses dados só servem para o historial. As funcionalidades abaixo
transformam-nos em **vigilância, decisão e resposta**.

Actores: **agricultor** (app), **técnico/extensionista** (distrito ou província, painel),
**coordenador** (província, painel), **administrador** (país, painel), **investigador** (dados
anonimizados, só leitura).

Esforço: P (dias), M (1–2 semanas), G (mais de 2 semanas).

---

## 1. Vigilância e resposta (núcleo)

| # | Funcionalidade | Para quem | O que faz | Usa | App? | Esforço |
|---|---|---|---|---|---|---|
| 1 | **Mapa de ocorrências** | técnico, coordenador | Mapa de Moçambique por distrito; filtros por praga, cultura, período e confiança; tendência semana a semana | diagnósticos + distritos | não | M |
| 1b | **Detecção de surtos** | técnico | Sinal automático quando uma praga sobe acima do normal num distrito (ex.: casos dos últimos 7 dias contra a média das 4 semanas anteriores, com mínimo de casos). O técnico confirma ou descarta; ao confirmar, abre um alerta pré-preenchido | diagnósticos | não | M |
| 2 | **Validação pelo técnico** | técnico | Fila de revisão com os casos de confiança baixa primeiro; ver a foto e o Grad-CAM; **confirmar ou corrigir** a classe e escrever uma nota | diagnósticos + imagens | sim (mostrar «Confirmado/Corrigido» na sincronização) | M |
| 2b | **Exactidão em campo** | coordenador, investigador | A concordância modelo × técnico, por classe, distrito e versão do modelo. É a medida real do modelo em Moçambique, actualizada continuamente | validações | não | P |
| 2c | **Conjunto de retreino local** | investigador | Exportar as imagens validadas (ZIP + CSV, com a mesma divisão por folha) para treinar no Colab. Responde à queda de exactidão fora do CCMT | validações | não | P |
| 3 | **Alertas por zona** | técnico, administrador | Distrito, província ou país; nível; praga associada; validade; modelos de mensagem; **alcance previsto** antes de enviar e **taxa de leitura** depois. O técnico só envia para a sua zona | agricultores por distrito | sim (receber na sincronização) | M |
| 3b | **Pragas de declaração obrigatória** | administrador | Lista de pragas quarentenárias ou de risco nacional; um caso confirmado notifica logo o coordenador e o administrador | catálogo + validações | não | P |
| 4 | **Pedido de visita técnica** | agricultor, técnico | A partir de um diagnóstico: «pedir ajuda» → o técnico agenda → visita → resolvido, com notas. Indicador: tempo de resposta | diagnósticos | sim (botão + estado) | M |
| 4b | **Seguimento do tratamento** | agricultor | 7 dias depois, a app pergunta «Seguiu a recomendação? A planta melhorou?» (sim/não/não sei). Mede se as recomendações funcionam | diagnósticos | sim | P |

## 2. Gestão, transparência e confiança

| # | Funcionalidade | O que faz | App? | Esforço |
|---|---|---|---|---|
| 5 | **Boletim fitossanitário** | Resumo semanal/mensal por distrito e província (casos, pragas principais, alertas enviados, visitas), em PDF e CSV, para os SDAE e as direcções provinciais | não | M |
| 6 | **Registo de auditoria** | Quem alterou que recomendação, enviou que alerta, validou que caso ou desactivou que conta, e quando, com o valor antes e depois | não | P |
| 6b | **Perfis finos** | Administrador nacional, coordenador provincial, técnico distrital, investigador (só leitura, dados anonimizados) | não | P |
| 6c | **Organizações** | IIAM, SDAE, ONG, cada uma com os seus técnicos e zonas; dados partilhados conforme regras | não | M |
| 7 | **Catálogo enriquecido** | Fotos de referência por praga, sintomas, prevenção, tratamento, «validado por [técnico] em [data]» e versão da recomendação | sim (mostrar fotos/sintomas) | M |
| 8 | **Gestão de modelos (MLOps leve)** | Versões com métricas; **piloto** num distrito antes de publicar para todos; confiança média e taxa de confiança baixa por versão; **sinal de deriva** quando a confiança baixa sobe | sim (piloto por distrito) | M |
| 8b | **Porta de qualidade** | Uma versão nova só pode ser publicada para todos se não piorar a exactidão no conjunto de validação local (2c) | não | P |

## 3. Qualidade do diagnóstico (no telemóvel)

| # | Funcionalidade | O que faz | Esforço |
|---|---|---|---|
| 15 | **Verificação da fotografia** | Antes de inferir, medir a nitidez e a luz; se a foto estiver desfocada ou escura, pedir outra. Reduz erros sem mexer no modelo | P |
| 16 | **Várias fotos por caso** | 2–3 fotos da mesma planta; a classe final sai da média das probabilidades. Mais robusto do que uma só foto | P |
| 17 | **«Não reconhecido»** | Pontuação de fora do âmbito (energia/temperatura, tarefa D4) para dizer «isto não parece milho/mandioca», em vez de forçar uma classe (o caso da folha de manga) | M |
| 18 | **Severidade** | Percentagem da folha afectada (modelo de segmentação futuro); ajuda a decidir se vale a pena tratar | G |

## 4. Contexto agrícola

| # | Funcionalidade | O que faz | Esforço |
|---|---|---|---|
| 9 | **Risco meteorológico** | Previsão por distrito (Open-Meteo, grátis); regras simples, por exemplo humidade alta e chuva durante vários dias aumentam o risco de queima e de mancha cinzenta; aviso preventivo ao técnico | M |
| 10 | **Calendário agrícola por província** | Épocas de sementeira e riscos típicos por mês (ex.: lagarta-do-cartucho no início das chuvas); a app mostra «nesta altura, vigie…» | P |
| 11 | **Machambas georreferenciadas** | O agricultor regista a machamba (cultura, área, GPS); mapa mais fino do que o distrito; com consentimento explícito | M |
| 12 | **Campanhas de vigilância activa** | O técnico pede aos agricultores de uma zona que fotografem as plantas esta semana; conta quantos responderam | P |
| 19 | **Inspecção de campo estruturada** | Formulário do técnico (plantas observadas, % afectadas, severidade, estádio da cultura), alinhado com o **FAMEWS da FAO** para a lagarta-do-cartucho; exportável | M |
| 20 | **Armadilhas de feromona** | Registo semanal das capturas de traças da lagarta-do-cartucho por local; curva de capturas no mapa | P |

## 5. Alcance e inclusão

| # | Funcionalidade | O que faz | Esforço |
|---|---|---|---|
| 13 | **Alertas por SMS** | Para quem não tem smartphone; exige contrato com operadora (Vodacom, Movitel, Tmcel) ou agregador | M + custos |
| 13b | **Notificações push (Firebase)** | Alerta no telemóvel mesmo com a app fechada | M |
| 14 | **Línguas locais e áudio** | Recomendações e alertas em emakhuwa, xichangana, cisena…, com áudio para quem tem pouca literacia | M |
| 21 | **Directório de apoio** | Contactos do SDAE e do técnico do distrito, lojas de insumos por distrito | P |

## 6. Dados abertos e plataforma

| # | Funcionalidade | O que faz | Esforço |
|---|---|---|---|
| 22 | **Dados agregados abertos** | Casos por distrito e semana, anonimizados (CSV/GeoJSON e API pública), para investigadores e parceiros | P |
| 23 | **Segurança de produção** | HTTPS, tokens de renovação, limite de tentativas de login, cópias de segurança automáticas, monitorização | M |
| 24 | **Privacidade** | Consentimento no registo, anonimização nas exportações, apagar a conta e os dados a pedido | P |

---

## Faseamento proposto

Tudo o que foi escolhido é viável, mas não de uma vez. A ordem segue o valor: primeiro fechar o
ciclo **diagnóstico → validação → vigilância → alerta → visita → relatório**.

**Fase 1 — núcleo da plataforma (agora)**
Regiões de Moçambique · painel web · mapa de ocorrências e detecção de surtos (1, 1b) ·
validação pelo técnico com exactidão em campo e conjunto de retreino (2, 2b, 2c) ·
alertas por zona (3) · pedido de visita técnica (4) · registo de auditoria (6) ·
gestão de utilizadores, catálogo e modelos.
App: receber alertas, ver a validação, pedir visita, escolher o distrito no registo.

**Fase 2 — gestão e qualidade**
Boletim PDF/CSV (5) · catálogo enriquecido (7) · modelos com piloto e deriva (8, 8b) ·
verificação da fotografia e várias fotos (15, 16) · seguimento do tratamento (4b) ·
pragas de declaração obrigatória (3b) · perfis finos (6b).

**Fase 3 — contexto agrícola**
Risco meteorológico (9) · calendário (10) · campanhas (12) · inspecção estruturada e armadilhas (19, 20) ·
machambas com GPS (11).

**Fase 4 — alcance e abertura**
Push (13b) · SMS (13) · línguas locais e áudio (14) · dados abertos (22) · organizações (6c) ·
«não reconhecido» e severidade (17, 18) · segurança de produção (23, 24).

No PFC, a Fase 1 entra como implementada; as Fases 2–4 entram como trabalho futuro fundamentado.
