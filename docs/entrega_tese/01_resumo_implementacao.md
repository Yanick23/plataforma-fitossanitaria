# Resumo da implementação — AgroDiagnóstico

Base para as secções 4.4 (arquitectura e tecnologias) e 5.1.5 (protótipo) do relatório.
Estado do repositório: ramo `main`, commits até `3e9106e` e seguintes.

## 1. Arquitectura

Cliente-servidor em três camadas (secção 2.2.4), com inferência no telemóvel:

```
App Android (Flutter)                         API REST (FastAPI)                 PostgreSQL 18
 ├─ TFLite: 1 modelo por cultura  ── HTTPS/HTTP + JSON + token JWT ──▶  ├─ autenticação         ├─ utilizadores
 ├─ SQLite: historial local (offline)                                   ├─ sincronização        ├─ culturas / patologias
 └─ armazenamento seguro do token                                       ├─ catálogo             ├─ diagnósticos / imagens
                                                                        ├─ versões do modelo    └─ modelos_ml
                                                                        └─ Grad-CAM (Keras)
```

O diagnóstico **não depende da rede**: o modelo corre no telemóvel. A rede só é usada
para o primeiro login, a sincronização do historial, a actualização do catálogo e dos
modelos, e o Grad-CAM.

## 2. Tecnologias (versões usadas)

| Camada | Tecnologia | Versão | Uso |
|---|---|---|---|
| Treino | Python, TensorFlow/Keras | 3.11, 2.17.1 / 3.15.1 | EfficientNetB0, transfer learning em 2 fases |
| Treino | NumPy, Pandas, scikit-learn, Matplotlib | 1.26.4, 2.2.3, 1.5.2, 3.9.2 | Dados, divisão estratificada, métricas, gráficos |
| Treino | Google Colab (GPU T4), Google Drive | — | Treino e armazenamento dos resultados |
| Modelo | TensorFlow Lite | quantização de intervalo dinâmico (INT8 nos pesos) | Inferência no telemóvel, ~4,4 MB por modelo |
| App | Flutter / Dart | Flutter 3.38, Dart 3.10 | App Android 8.0+ (minSdk 26) |
| App | tflite_flutter | 0.12.1 | Inferência offline, 1 thread |
| App | image_picker | 1.2.3 | Câmara e galeria |
| App | image | 4.10.2 | Pré-processamento (224×224, bilinear) |
| App | sqflite (SQLite) | 2.4.2 | Historial local |
| App | flutter_secure_storage | 11.2.0 | Token JWT no Android Keystore |
| App | http, connectivity_plus, uuid, crypto | 1.6, 7.3, 4.6, 3.0 | API REST, estado da rede, UUID, verificação SHA-256 |
| API | FastAPI (Starlette, Pydantic 2) | 0.115.6 | Endpoints `async`, validação automática |
| API | Uvicorn | 0.34.0 | Servidor ASGI |
| API | OpenAPI + Swagger UI + ReDoc | — | Documentação automática em `/docs` e `/redoc` |
| API | SQLAlchemy 2 (async) + asyncpg | 2.0.36, 0.30.0 | Acesso assíncrono ao PostgreSQL |
| API | PostgreSQL | 18.1 | Base de dados do servidor |
| API | bcrypt | 4.2.1 | Hash das palavras-passe |
| API | PyJWT | 2.10.1 | Token de autenticação (JWT, HS256, 30 dias) |
| API | TensorFlow/Keras + Pillow + Matplotlib | as do treino | Grad-CAM no servidor |
| Testes | pytest + httpx | 8.3.4, 0.28.1 | 23 testes automáticos da API |
| Infra | Docker Compose (opcional) | — | PostgreSQL 16 em contentor, alternativa ao PostgreSQL local |
| Gestão | Git | 2.52 | Controlo de versões |

## 3. App Android (`app/`)

### Ecrãs e requisitos

| Ecrã | Requisitos |
|---|---|
| Login / Criar conta (telefone + palavra-passe) | RF10 |
| Inicial (estado online/offline, acesso ao historial, definições e diagnóstico técnico) | — |
| Escolha da cultura (milho / mandioca) | RF02 |
| Captura (câmara ou galeria, guia de enquadramento) | RF01 |
| Processamento | RF03 |
| Resultado: classe, confiança, nome local e científico, recomendação; aviso e "Tirar nova foto" abaixo de 60% | RF04, RF05, RF06, RF07 |
| Historial (estado PENDENTE / SINCRONIZADO, sincronização manual) | RF08, RF09 |
| Detalhe do diagnóstico com "Ver onde o modelo olhou" (Grad-CAM) | 4.6.6 |
| Definições (endereço da API, conta, versões dos modelos, sincronizar, terminar sessão) | RF10, RF12 |
| Diagnóstico técnico (tempos, memória, teste de desempenho, teste com fotografias, CSV) | RNF03, RNF04 |

### Inferência (RF03)

- Um modelo TFLite por cultura (milho: 7 classes; mandioca: 5), escolhido pela cultura seleccionada.
- Pré-processamento igual ao do treino: rotação EXIF aplicada, imagem esticada para
  224×224 RGB (bilinear), **float32 com valores 0–255, sem dividir por 255** (a normalização
  está dentro do EfficientNetB0). Entrada `[1,224,224,3]`, saída softmax `[1,n]`.
- A app confirma a interface do modelo (tipo e forma da entrada e da saída) antes de o usar.
- Interpreter com **1 thread**; o pré-processamento corre num isolate separado para não bloquear o ecrã.
- Limiar de confiança: **60%** (heurística; probabilidade softmax não calibrada).

### Historial e sincronização (RF08, RF09, RNF07)

- Cada diagnóstico recebe um **UUID gerado no telemóvel** e fica em SQLite como `PENDENTE`,
  com a fotografia copiada para a pasta da app.
- A sincronização corre ao entrar na app, quando a rede volta, depois de guardar um
  diagnóstico, ou manualmente. Ordem:
  1. renova o token (`POST /auth/renovar`);
  2. envia os pendentes em lote (`POST /diagnosticos`);
  3. envia a fotografia de cada diagnóstico confirmado (`POST /diagnosticos/{id}/imagem`);
  4. **só então** marca o diagnóstico como `SINCRONIZADO`;
  5. actualiza o catálogo (`GET /patologias`) e verifica novas versões do modelo.
- Se a rede cair a meio, o que não foi confirmado continua `PENDENTE` e é reenviado; a API
  ignora UUID repetidos, por isso nada se perde nem se duplica.

### Autenticação (RF10, RNF01)

- Registo e login por telefone + palavra-passe; o registo público cria sempre perfil AGRICULTOR.
- O token JWT e os dados do utilizador ficam no armazenamento seguro do Android; depois do
  primeiro login a app abre e diagnostica **sem rede**.

### Actualização do modelo (RF12)

- A versão 1 vem dentro do APK. Na sincronização, a app pergunta à API a última versão;
  se for mais recente, descarrega o `.tflite`, confirma o **SHA-256** e a interface do modelo,
  e só então o activa (fica guardado na pasta da app; funciona offline).

### Medições (RNF03, RNF04)

- `Stopwatch` da confirmação da imagem até ao resultado, e separadamente o pré-processamento
  e a inferência; memória residente (`ProcessInfo.currentRss` / `maxRss`).
- As medições aparecem no ecrã "Diagnóstico técnico", são escritas no log
  (`adb logcat`, etiqueta `AgroDiagnostico`) e num CSV permanente no telemóvel.

## 4. API (`api/`)

### Endpoints

| Método | Caminho | Acesso | Requisito |
|---|---|---|---|
| POST | `/auth/registar` | público (cria AGRICULTOR) | RF10 |
| POST | `/auth/login` | público | RF10 |
| POST | `/auth/renovar` | autenticado | 4.4.5 |
| GET | `/auth/eu` | autenticado | RF10 |
| POST | `/utilizadores` | ADMINISTRADOR (cria técnicos) | RF10 |
| POST | `/diagnosticos` | autenticado; lote idempotente por UUID | RF09, RNF07 |
| POST | `/diagnosticos/{id}/imagem` | dono do diagnóstico | RF09, 4.4.4 |
| GET | `/diagnosticos` | agricultor: os seus; técnico: os da sua área; admin: todos | RF08 |
| GET | `/diagnosticos/{id}/gradcam` | quem pode ver o diagnóstico | 4.6.6 |
| GET, POST, PUT | `/culturas` | leitura: todos; escrita: ADMINISTRADOR | RF11 |
| GET, POST, PUT, DELETE | `/patologias` | leitura: todos; escrita: ADMINISTRADOR | RF11 |
| GET | `/modelos/{cultura}/ultima-versao` | autenticado | RF12 |
| GET | `/modelos/{cultura}/{versao}/ficheiro` | autenticado | RF12 |
| POST | `/modelos/{cultura}` | ADMINISTRADOR | RF12 |
| GET | `/saude` | público | — |

### Base de dados (PostgreSQL)

Tabelas do diagrama de classes: `utilizadores` (perfil AGRICULTOR / TECNICO / ADMINISTRADOR,
área), `culturas`, `patologias` (tipo DOENCA / PRAGA / SAUDAVEL, recomendação),
`diagnosticos` (chave = UUID do telemóvel), `imagens` (repositório central de fotografias
para retreino) e `modelos_ml` (versão, ficheiro, classes, SHA-256, acurácia de teste).
Na primeira execução são criadas as 2 culturas, as 12 patologias, o administrador e a versão 1
de cada modelo.

### Segurança

- Palavras-passe com **bcrypt**; nunca guardadas em claro.
- **JWT** (HS256, 30 dias) emitido no login e renovado em cada sincronização.
- Permissões por perfil verificadas no servidor (testes automáticos).
- Limitação do protótipo: HTTP simples na rede local; em produção deve usar HTTPS.

### Grad-CAM

Calculado no servidor a partir do modelo Keras original (`.keras`), na camada
`top_activation` do EfficientNetB0, para a classe prevista pela app. Devolve um PNG com o
mapa de calor sobreposto à fotografia; a app mostra-o no detalhe dos diagnósticos já
sincronizados, quando há rede.

## 5. Testes automáticos

- **API: 23 testes pytest** — registo/login, hash bcrypt, token inválido, renovação do token;
  reenvio do mesmo lote sem duplicados, UUID repetido no lote, classe inválida, UUID de outro
  utilizador, envio de imagem idempotente; permissões por perfil (agricultor, técnico por
  área, administrador); publicação e descarga de modelos; Grad-CAM.
- **App: `flutter analyze` sem problemas e 2 testes unitários** (catálogo e conversão do diagnóstico).

## 6. Diferenças em relação ao texto actual da tese (a corrigir no relatório)

1. **Quantização:** os modelos usam **quantização de intervalo dinâmico** (pesos em INT8,
   entrada e saída em float32), não INT8 completa. A secção 4.4.3 deve dizê-lo (ou refaz-se a exportação).
2. **Pré-processamento (4.6.1):** os píxeis ficam em 0–255; a normalização é interna ao modelo.
3. **Tecnologias a acrescentar à 4.4:** JWT, bcrypt, SQLAlchemy, flutter_secure_storage,
   Uvicorn; Docker é opcional (foi usado o PostgreSQL 18 instalado no PC).
4. **Grad-CAM** passou a ser também uma funcionalidade da plataforma (endpoint + botão na app).
5. **Classificador fechado:** cada modelo responde sempre com uma das suas classes, mesmo
   para fotos que não são folhas ou para folhas da outra cultura; o aviso de confiança < 60%
   cobre parte destes casos. Limitação a referir em 6.3; um modelo "porteiro"
   (milho / mandioca / outro) fica como trabalho futuro (6.4).
6. **Ecrãs novos** em relação ao protótipo estático: login, criar conta, definições,
   detalhe com Grad-CAM e diagnóstico técnico.
