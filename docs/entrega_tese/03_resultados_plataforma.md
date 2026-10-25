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

### Limitações desta entrega

- Sem histórico (todos os diagnósticos de teste são recentes), a detecção de surtos assinala
  qualquer praga com 3 ou mais casos; com semanas de dados, a comparação com a média passa a pesar.
- As 2 unidades «Ilha Licom» e «Ilha Risunodo» do ADM2 (ilhas Likoma e Chizumulu, do Malawi) foram
  excluídas; os nomes dos distritos seguem a fonte, sem acentos em alguns casos (ex.: «Chokwe»).
- Os alertas chegam à app na sincronização (sem notificações push nesta fase).
