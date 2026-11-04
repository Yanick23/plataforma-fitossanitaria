# Diagramas da versão 2 do PFC

Seguem o estilo dos diagramas da v1: draw.io, preto e branco, cabeçalhos em cinzento claro,
Helvetica, notação UML. Foram gerados a partir do código a 04/11/2026: as classes vêm de
`api/app/tabelas.py` e os passos das sequências das rotas e dos serviços.

Cada diagrama tem dois ficheiros:
- `.drawio`, que se abre e edita em [app.diagrams.net](https://app.diagrams.net) ou no draw.io;
- `.png`, com cerca de 3 700 a 5 200 px de largura, pronto para o Word.

| Ficheiro | Diagrama | Substitui na v1 |
|---|---|---|
| `D1_casos_de_uso` | Casos de uso: 5 actores (Equipa abstracta → Técnico → Coordenador → Administrador; Investigador), Open-Meteo, RF01 a RF27 | Figura 5.1 |
| `D2_classes` | Classes: as 17 entidades da base de dados, com multiplicidades, composições e enumerados | Figura 5.2 |
| `D3_arquitectura` | Arquitectura: app offline, painel web em MVVM, API em camadas, armazenamento, Open-Meteo; passos 1 a 9 | Figura 5.5 |
| `D4_sequencia_diagnostico` | Sequência do diagnóstico offline e da sincronização | Figuras 5.3 e 5.6 (juntas) |
| `D5_sequencia_validacao` | Sequência da validação, do aviso de declaração obrigatória e do alerta | Nova |
| `D6_actividades_vigilancia` | Actividades do ciclo de vigilância (3 raias) | Figura 5.4 |

## Outras figuras da v1

- **A retirar** (abordagem de engenharia de software, menos ML):
  - Fig. 2.6 (IA, ML e DL);
  - Fig. 2.7 (rede neuronal);
  - Fig. 2.8 (CNN genérica);
  - Fig. 2.12 (matriz de confusão genérica);
  - Fig. 2.13 (ciclo de vida do software);
  - Fig. 2.16 (pedido GET);
  - Fig. 5.7 (estrutura do modelo);
  - Gráfico 5.1;
  - Fig. 5.18 (`/docs`, agora substituída pelo painel web).
- **A manter:**
  - Fig. 2.1, 2.3 e 2.4 (culturas e sintomas);
  - Gráfico 2.1;
  - Fig. 2.5 (*pipeline*);
  - Fig. 2.9 (*transfer learning*);
  - Fig. 2.14 (prototipagem);
  - Fig. 3.1 (fluxo actual);
  - Fig. 5.8 **ou** 5.9 (confusão ou Grad-CAM);
  - capturas da app, juntas em grelhas.
- **A decidir:**
  - Fig. 2.2 (inflorescência do milho), 2.10 (EfficientNet) e 2.11 (aumento de dados): podem sair, para poupar páginas;
  - Fig. 2.15 (três camadas genérica): pode ficar como base teórica do D3.

## Regenerar

O código está em `fonte/` (`drawio.py` com o estilo comum, e `d1_*.py` a `d6_*.py`). A exportação
usa o draw.io headless em Docker:

```
bash fonte/gerar.sh d2_classes.py      # gera D2_classes.drawio e o .png nesta pasta
```

Para pequenos ajustes, é mais simples abrir o `.drawio` no draw.io, mexer e exportar
(Ficheiro → Exportar como → PNG, zoom 200%, margem 20).
