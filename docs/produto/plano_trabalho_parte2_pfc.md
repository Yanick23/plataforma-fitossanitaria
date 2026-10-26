# Plano de trabalho — parte 2 (resultados do modelo para o PFC)

> **Estado a 26/10/2026.** O plano original segue abaixo, sem alterações.
>
> | Tarefa | Estado | Onde está |
> |---|---|---|
> | D1. T13 (Grad-CAM na app) | **Feito** (25/10). Aprovado: 2,4 s no 1.º pedido de milho, 2,1 s na mandioca, 0,8 s com o modelo já carregado | `docs/entrega_tese/02_relatorio_app_api.md` (T13), commit `bca2ac5` |
> | D2. Mandioca: M-E0a, M-E0b, M-E0c (validação) | **Por correr.** O código está no notebook | `ml/notebooks/03_parte2.ipynb`, secção 5 |
> | D3. Milho: 4 configurações × 3 sementes (validação) | **Por correr** (cerca de 5 h; pode correr de noite) | `ml/notebooks/03_parte2.ipynb`, secção 6 |
> | D4. Calibração e fotos fora do âmbito | **Por correr** (cerca de 30 min, sem treino) | `ml/notebooks/03_parte2.ipynb`, secção 7 |
> | D5. Teste externo do milho | **Por fazer.** Falta escolher um conjunto público (Tanzânia/Quénia: listrado do milho; lagarta-do-cartucho) | — |
> | D6. Treino CCMT + iCassava (opcional) | **Por fazer** (opcional) | — |
> | D7. Fotografias locais (Maputo/Boane) | **À espera das fotos** (30–50, com `rotulos.csv`) | — |
>
> **Próximo passo:** abrir o notebook no Colab com GPU, correr o teste rápido (secção 2) e depois
> as secções 5–7. A secção 8 gera o relatório em Markdown no formato do fim deste plano.
> O resultado da D4.2 (AUROC das fotos de fora do CCMT) serve de base à funcionalidade
> «não reconhecido» da plataforma (n.º 17, fase 4).

---

# Plano de trabalho — parte 2: reforçar os resultados do PFC

**Projecto:** Plataforma de diagnóstico de doenças e pragas do milho e da mandioca (PFC de Yanick Ribeiro Mussagy, ISUTC)
**Para:** o agente que trabalha no código da aplicação (Flutter), na API (FastAPI) e nos notebooks do Colab
**Objectivo:** responder às críticas que o júri vai fazer. As tarefas estão por ordem de prioridade; cada uma é independente das outras.

---

## 0. Regras (ler antes de começar)

1. **O conjunto de teste do CCMT não se usa em nenhuma tarefa nova.** Já foi usado uma vez para avaliar os modelos finais. As comparações novas fazem-se **só no conjunto de validação**. Excepções: a tarefa D4, que usa previsões de teste já existentes, e a tarefa D7, que é um conjunto novo.
2. **A divisão dos dados não muda:** CCMT em bruto, 70/15/15, estratificada, **semente 42**, com as fotografias da mesma folha no mesmo subconjunto. Na validação há 793 imagens de milho e 1 126 de mandioca.
3. **Usar o código de treino que gerou E0 a E0c.** Só mudam os parâmetros indicados em cada tarefa. Lote 32, Adam, dropout 0,3, `class_weight` balanced, paragem antecipada sobre `val_loss` (paciência 5, repõe os melhores pesos), até 20 épocas na fase 1 e até 30 na fase 2, BatchNormalization sempre congelada.
4. **Pré-processamento:** RGB, 224×224, float32 de 0 a 255, sem dividir por 255.
5. **Reportar números em bruto** (n, acertos, erros) e não só percentagens. Se algo não for possível, dizer porquê e o que se fez em vez disso. Não inventar valores.
6. **Não alterar os modelos que estão na aplicação** (milho E0b, mandioca E0).

---

## D1. Fechar o T13 (Grad-CAM na aplicação) — 15 minutos

1. Copiar `modelo_milho.keras` e `modelo_mandioca.keras` do Drive para `api/modelos/`.
2. Reiniciar a API e repetir o T13: abrir um diagnóstico sincronizado e tocar em «Ver onde o modelo olhou».
3. Gravar a captura `09_detalhe_gradcam.png`, uma para o milho e, se possível, outra para a mandioca.

**Opcional:** se houver outro telemóvel com câmara a funcionar, repetir o **T03** e o **T05** com a câmara e tirar a captura `04_captura.png` com a pré-visualização da câmara.

**Devolver:** o estado do T13 (aprovado ou não, com o que se viu), o tempo de resposta do Grad-CAM e as capturas.

---

## D2. Experiências na mandioca (validação) — cerca de 2 horas

O milho teve quatro configurações; a mandioca só teve a E0. Correr na mandioca as mesmas variações:

| ID | Fase 2 |
|---|---|
| M-E0a | blocos 6 e 7 e topo descongelados (59 camadas treináveis), lr = 10⁻⁴ |
| M-E0b | igual a M-E0a, com lr = 5 × 10⁻⁵ |
| M-E0c | igual a M-E0b, com label smoothing = 0,1 nas duas fases |

**Não avaliar no teste.** Os modelos são só para comparar no conjunto de validação.

**Devolver**, para M-E0a, M-E0b e M-E0c e repetindo a E0 da mandioca já existente:
- épocas e val_acc da fase 1;
- épocas e val_acc da fase 2;
- val_loss final;
- tempo de treino;
- F1 por classe e F1 ponderado na validação (tabela como a A3.1);
- uma frase: alguma configuração supera a E0 na validação? Por quanto?

---

## D3. Repetir as configurações do milho com várias sementes (validação) — cerca de 5 horas, pode correr de noite

As diferenças entre E0a, E0b e E0c são menores do que 1 ponto, com uma só execução cada. Repetir **E0, E0a, E0b e E0c** do milho com **3 sementes de treino** (por exemplo 1, 2 e 3).

- A semente da divisão dos dados fica sempre em 42; muda só a semente do treino: pesos da cabeça, ordem dos lotes e aumento de dados.
- Fixar `tf.keras.utils.set_random_seed(semente)` e, se possível, `tf.config.experimental.enable_op_determinism()`.

**Devolver:**
- por configuração e por semente: val_acc final, val_loss e F1 ponderado na validação;
- por configuração: **média ± desvio-padrão** da val_acc e do F1 ponderado;
- uma frase: as diferenças entre as configurações são maiores do que a variação entre sementes?
- se for simples, um teste de McNemar entre E0 e E0b na validação, com a semente 1.

---

## D4. Calibração e detecção de fotografias fora do âmbito — cerca de 30 minutos

Usa as **previsões já existentes**; não é preciso treinar nada.

### D4.1 Temperature scaling

1. Com os **logits da validação** (modelo Keras final de cada cultura), encontrar a temperatura T que minimiza a NLL.
2. Aplicar T aos logits do **teste** e recalcular:
   - ECE (15 intervalos), Brier e NLL, antes e depois;
   - a tabela risco–cobertura com τ = 0,60, 0,80 e 0,90: cobertura, exactidão sem aviso e erros avisados, como na Tabela A3.4.
3. Se os logits não estiverem guardados, calculá-los de novo com os modelos `.keras`. Isto não conta como uso novo do teste, porque o modelo não muda.

### D4.2 A confiança separa imagens do CCMT de imagens de outra origem?

- **Positivos (fora do âmbito):** as 80 imagens do iCassava, mais as 10 de CBSD, ou seja, 90 imagens.
- **Negativos (dentro do âmbito):** as 1 127 imagens de teste da mandioca.
- **Pontuação:** 1 − confiança máxima, com e sem temperatura.

**Devolver:** a AUROC e, para o limiar de 60%, a percentagem de imagens do iCassava que recebem aviso e a percentagem das do CCMT que o recebem.

---

## D5. Teste externo do milho — cerca de 2 a 3 horas

Procurar um conjunto **público** de folhas de milho fotografadas no campo, fora do Gana, com pelo menos duas classes que existam no modelo. Exemplos a verificar:
- conjuntos da Tanzânia ou do Quénia com folhas saudáveis e com listrado do milho (*maize streak virus*);
- outros com lagarta-do-cartucho (*fall armyworm*).

Procedimento igual ao do Uganda (A1):
1. Amostra estratificada com semente 42, até 20 imagens por classe com correspondência no modelo.
2. Classes sem correspondência (por exemplo, MLN) ficam fora da exactidão e listam-se à parte.
3. Verificar duplicados com o CCMT por dHash (limiar ≤ 4).
4. Modelo **TFLite INT8 do milho (E0b)**.

**Devolver:**
- nome do conjunto, URL, licença, país e citação;
- correspondência entre as classes;
- tabela por classe com imagens, acertos, exactidão e IC de Wilson a 95%;
- matriz de confusão;
- quantas imagens ficaram abaixo de 60%;
- CSV por imagem;
- causa provável dos erros.

Se não houver nenhum conjunto acessível, dizer quais se procuraram e porque não serviram.

---

## D6. (Opcional) Treino com dados de várias origens — meio dia

Objectivo: mostrar que a queda no Uganda vem dos dados e não do modelo.

1. Dividir o iCassava, **sem as 80 imagens já usadas no teste externo**, em treino e validação, nas 4 classes com correspondência.
2. Treinar a configuração E0 da mandioca com **CCMT + iCassava** no treino.
3. Avaliar no **mesmo teste externo de 80 imagens** do iCassava e no conjunto de **validação** do CCMT. O teste do CCMT continua sem ser usado.

**Devolver:** imagens usadas de cada origem; exactidão no iCassava (80 imagens), antes (26,2%) e depois, com IC de Wilson; exactidão na validação do CCMT, antes e depois.

---

## D7. Fotografias locais (quando o Yanick as enviar)

O Yanick vai tirar 30 a 50 fotografias em Maputo/Boane, **uma folha de perto em cada**, com um ficheiro `rotulos.csv`:

```
ficheiro,cultura,classe,local,data,confirmado_por
```

`confirmado_por` fica vazio quando o rótulo não foi confirmado por um técnico.

**Fazer:** correr cada imagem no **TFLite INT8** da cultura respectiva, com o mesmo procedimento do A1.

**Devolver:**
- tabela por cultura e por classe com imagens, acertos, exactidão e IC de Wilson;
- os mesmos números só para as imagens com rótulo confirmado;
- matriz de confusão;
- quantas imagens ficaram abaixo de 60%;
- CSV por imagem;
- três exemplos de erro com a causa provável.

---

## Modelo do relatório

```
# RELATÓRIO PARA O PFC — parte 2 — <data>

## D1. T13 e capturas
Estado: … | Tempo do Grad-CAM: … | Ficheiros: …

## D2. Mandioca, validação
| ID | F1 épocas | F1 val_acc | F2 épocas | F2 val_acc | val_loss | Tempo (min) | F1 ponderado |
F1 por classe (tabela). Conclusão: …

## D3. Milho, sementes
| Config. | Semente | val_acc | val_loss | F1 ponderado |
Médias ± DP. Conclusão: … | McNemar E0 × E0b: …

## D4. Calibração e fora do âmbito
T (milho) = … ; T (mandioca) = …
| Cultura | ECE antes/depois | Brier antes/depois | NLL antes/depois |
Risco–cobertura com T (tabela). AUROC: … | % com aviso (iCassava / CCMT): …

## D5. Teste externo do milho
Conjunto: … | Classes: … | Tabela | Matriz | Abaixo de 60%: … | Conclusão: …

## D6. Várias origens (se feito)
…

## D7. Fotografias locais (se recebidas)
…

## Observações
Tudo o que foi diferente do pedido e porquê.
```
