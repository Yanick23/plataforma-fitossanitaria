# Relatório para o PFC — Parte B (aplicação e API) e Parte C (texto × código)

Data: 2026-10-23. Ramo `main`, commit `e3f1c52` mais as alterações desta sessão (troca do nome visível).
A Parte A (Colab) não é tratada aqui.

---

## B1. Dispositivo de teste — **por recolher**

Nenhum telemóvel estava ligado por adb. Com o telemóvel ligado:

```
bash docs/entrega_tese/recolher_dados_telemovel.sh dispositivo
```

O script escreve marca, modelo, versão do Android, RAM total, número de núcleos e SoC em
`docs/entrega_tese/dados_telemovel/dispositivo.txt`. O ecrã «Diagnóstico técnico» também mostra
o sistema e o número de processadores.

## B2. Tempo total do diagnóstico — **por medir** (a instrumentação já existe)

O código já mede o RNF03; não foi preciso acrescentar nada:

- o `Stopwatch` arranca quando a fotografia é confirmada (`app/lib/screens/captura_screen.dart:32`);
- pára quando as probabilidades estão prontas, logo antes de abrir o ecrã de resultado
  (`app/lib/services/classificador.dart`, `cronometroTotal.stop()`);
- cada diagnóstico fica no log (`AgroDiagnostico/inferencia ... total=XXXms`), no ecrã
  «Diagnóstico técnico» e em `registo_tecnico.csv`.

Nota para o texto: o tempo vai até ao **resultado pronto**, um frame antes de o ecrã aparecer
(da ordem de dezenas de milissegundos). Pode escrever «da confirmação da fotografia até o resultado
estar pronto a apresentar».

Procedimento:

1. Instalar a versão de **release** (`flutter run --release` ou `flutter build apk --release`).
   O modo debug é muito mais lento e não serve para o RNF03.
2. `adb logcat -c` para limpar o log.
3. Fazer 10 diagnósticos de milho e 10 de mandioca.
4. `bash docs/entrega_tese/recolher_dados_telemovel.sh tempos` mostra os 10 tempos por cultura,
   a média, o mínimo e o máximo, em segundos.

O 1.º diagnóstico de cada cultura inclui o carregamento do modelo (campo `carregamento`). Convém
reportá-lo à parte, ou dizer que está incluído.

## B3. Testes funcionais T01–T13 — **por executar no telemóvel**

Preparação da API (uma vez):

1. Copiar `modelo_milho_int8_dinamica.tflite`, `modelo_mandioca_int8_dinamica.tflite`,
   `classes_milho.json` e `classes_mandioca.json` (de `app/assets/models/`) para `api/modelos/`
   **antes** do primeiro arranque da API. Assim a semente regista estes ficheiros como versão 1,
   a mesma da app. Se a pasta estiver vazia, a primeira publicação passa a ser a v1 e a app
   **ignora-a**, porque já tem a v1 embutida. Nesse caso o T11 só funciona à segunda publicação.
2. Para o T13, copiar `modelo_milho.keras` e `modelo_mandioca.keras` (Drive/Colab) para
   `api/modelos/`. **Estes ficheiros não estão neste computador.** Sem eles, o Grad-CAM devolve
   503 («Falta o ficheiro modelo_milho.keras em api/modelos/»).
3. Definir `ADMIN_TELEFONE` e `ADMIN_PALAVRA_PASSE` no `api/.env` e arrancar com
   `uvicorn app.main:app --host 0.0.0.0 --port 8000`. O ambiente `api/.venv` já está instalado.

Como executar cada caso, segundo o código:

| ID | Como fazer | O que o código faz |
|---|---|---|
| T01 | Criar conta no ecrã de registo | `POST /auth/registar` cria um AGRICULTOR e devolve o token, sem novo login |
| T02 | Modo de voo, fechar e reabrir | O token e o utilizador são lidos do `flutter_secure_storage` no arranque |
| T03/T04 | Modo de voo, milho com câmara / mandioca com galeria | A inferência é local e o diagnóstico é gravado como PENDENTE |
| T05 | Fotografar um objecto que não é folha | Se a confiança for < 0,60: «Não temos certeza — tente tirar outra foto…». Se for ≥ 0,60, registar como limitação (classificador fechado) |
| T06 | Abrir um resultado | Nome local, nome científico e recomendação vêm do catálogo local |
| T07 | Historial depois de T03/T04 | Estado PENDENTE |
| T08 | Desligar o modo de voo | Sincroniza sozinha quando a rede volta. Confirmar com `GET /diagnosticos` em `/docs` |
| T09 | Forçar o fecho durante a sincronização e reabrir | Só marca SINCRONIZADO depois da confirmação. A API ignora UUID repetidos |
| T10 | Em `/docs`: `PUT /patologias/{id}` com o token de administrador; depois sincronizar | A app substitui o catálogo local pelo de `GET /patologias` |
| T11 | Em `/docs`: `POST /modelos/milho` com o `.tflite` e as classes; depois sincronizar | Descarrega, compara o SHA-256, valida a interface e activa. Mensagem «modelo de milho actualizado» |
| T12 | Ver B2 | — |
| T13 | Abrir um diagnóstico sincronizado → «Ver onde o modelo olhou» | `GET /diagnosticos/{id}/gradcam` (precisa dos `.keras`) |

Para o T11 pode publicar-se o mesmo ficheiro INT8 como v2: a app aceita-o, porque o SHA-256 e a
interface coincidem.

## B4. Testes automáticos da API — **feito**

```
api/.venv/Scripts/python -m pytest      (Python 3.11.9, requirements.txt)
====================== 23 passed, 16 warnings in 28.06s =======================
```

**23 aprovados, 0 falhados.** O número coincide com o texto. Os 16 avisos são de depreciação
(pyparsing/matplotlib e Keras) e não afectam o resultado.

## B5. Capturas de ecrã — **por recolher**

- O nome «AgroDiagnóstico» foi retirado de tudo o que aparece ao utilizador: ecrã de login, ecrã
  inicial, título da app, nome no lançador do Android e título da página `/docs` da API.
  O substituto é «Diagnóstico de culturas» («API de diagnóstico de culturas» no `/docs`).
  O identificador interno do pacote (`mz.isutc.agrodiagnostico`) não aparece no ecrã e ficou igual.
- Não existe interface web de administração. A captura 10 deve ser a página `/docs`.
- A captura 11 corresponde ao ecrã «Diagnóstico técnico», aberto pelo ícone no ecrã inicial.
- Para capturar os ecrãs: `bash docs/entrega_tese/recolher_dados_telemovel.sh capturas` pede cada
  ecrã pela ordem e grava `NN_nome.png`.

---

## Parte C — o texto do PFC corresponde ao código?

| # | Resposta | Detalhe / correcção |
|---|---|---|
| **C1** | **Sim** | Existe RF12. `POST /modelos/{cultura}` (só administrador) grava o `.tflite`, calcula o SHA-256 e cria a versão n+1 (`api/app/rotas/modelos.py`). Na sincronização, a app consulta `GET /modelos/{cultura}/ultima-versao`, descarrega o ficheiro, **compara o SHA-256**, valida a interface (entrada float32 [1,224,224,3], saída [1,n]) e só então activa (`app/lib/services/gestor_modelos.dart`). A v1 vem dentro do APK. **Não é preciso retirar o RF12, o caso de uso nem o T11, nem recalcular o COCOMO.** Ressalva prática: ver B3, passo 1. |
| C2 | **Parcial** | As patologias (nome local, nome científico, recomendação) são actualizadas na sincronização a partir de `GET /patologias` (RF11). Mas **não ficam em SQLite**: começam em `assets/catalogo.json` e, depois da sincronização, ficam num ficheiro JSON local (`catalogo.json` na pasta de documentos da app). As **culturas são fixas no código** (enum `Cultura`: milho e mandioca), porque cada uma depende de um modelo. O SQLite guarda só o historial de diagnósticos. Sugestão: «o catálogo de patologias é guardado localmente (JSON) e actualizado na sincronização; o SQLite guarda o historial». |
| C3 | **Sim** | Login por telefone e palavra-passe (`/auth/login`). bcrypt 4.2.1 com `gensalt()`. JWT HS256 válido **30 dias** (`jwt_validade_dias = 30`), renovado em cada sincronização (`/auth/renovar`). O token fica no `flutter_secure_storage` 11.2.0, cujas chaves estão no Android Keystore. |
| C4 | **Sim** (no código) | A sessão é lida do armazenamento seguro, e o modelo, o catálogo e o historial são locais. Falta confirmar no telemóvel com T02–T04. |
| C5 | **Sim** | `Uuid().v4()` no telemóvel (`resultado_screen.dart`). Estado PENDENTE até a API devolver o id em `confirmados`; só então `marcarSincronizado`. A API é idempotente quanto ao UUID. |
| C6 | **Sim, com uma precisão** | `Isolate.run(preprocessarImagem)`. A rotação usa a **orientação EXIF** da fotografia (`bakeOrientation`) e não um sensor da câmara. Depois a imagem é esticada para 224×224 (bilinear, sem manter a proporção) e convertida para RGB float32 0–255, sem dividir por 255. Antes disso, o `image_picker` já reduz a fotografia a 1024 px no máximo (qualidade JPEG 95). |
| C7 | **Sim** | `tflite_flutter` 0.12.1, `InterpreterOptions()..threads = 1`. |
| C8 | **Sim** | Grad-CAM no servidor (`api/app/gradcam.py`) com TensorFlow 2.17.1 / Keras 3.15.1, na camada `top_activation` do EfficientNetB0. Usa os modelos **`.keras`** originais, não os TFLite. |
| C9 | **Parcial** | O técnico vê os diagnósticos dos agricultores da **mesma `area`** (e os seus). O administrador vê todos. Mas o administrador **não altera o perfil** de uma conta existente: **cria** contas com o perfil TECNICO (`POST /utilizadores`). Sugestão: «o administrador cria as contas de técnico». |
| C10 | **Sim** | URL por omissão `http://192.168.1.100:8000` e `android:usesCleartextTraffic="true"`. |
| C11 | **Sim** | `minSdk = 26` (Android 8.0). O ficheiro é **`android/app/build.gradle.kts`** (Kotlin DSL), não `build.gradle`. |
| C12 | **Sim, com versões de correcção** | Ver a tabela abaixo. |

### C12 — versões confirmadas

| Componente | PFC | Real | Fonte |
|---|---|---|---|
| Flutter / Dart | 3.38 / 3.10 | **3.38.9 / 3.10.8** | `flutter --version` |
| tflite_flutter | 0.12.1 | 0.12.1 | `pubspec.lock` |
| image_picker | 1.2.3 | 1.2.3 | 〃 |
| image | 4.10.2 | 4.10.2 | 〃 |
| sqflite | 2.4.2 | **2.4.2+1** | 〃 |
| flutter_secure_storage | 11.2.0 | 11.2.0 | 〃 |
| http | 1.6 | 1.6.0 | 〃 |
| connectivity_plus | 7.3 | **7.3.2** | 〃 |
| uuid | 4.6 | 4.6.0 | 〃 |
| crypto | 3.0 | **3.0.7** | 〃 |
| TensorFlow / Keras | 2.17.1 / 3.15.1 | 2.17.1 / 3.15.1 | `pip freeze` |
| FastAPI | 0.115.6 | 0.115.6 | 〃 |
| Uvicorn | 0.34.0 | 0.34.0 | 〃 |
| SQLAlchemy | 2.0.36 | 2.0.36 | 〃 |
| asyncpg | 0.30.0 | 0.30.0 | 〃 |
| PostgreSQL | 18.1 | 18.1 (instalação local) | `postgres --version` |
| bcrypt | 4.2.1 | 4.2.1 | `pip freeze` |
| PyJWT | 2.10.1 | 2.10.1 | 〃 |
| pytest | 8.3.4 | 8.3.4 | 〃 |
| httpx | 0.28.1 | 0.28.1 | 〃 |

Nenhuma versão está errada. Em quatro casos, a versão exacta tem mais um dígito do que o PFC indica.
Atenção: o `api/docker-compose.yml` usa a imagem `postgres:16-alpine`. Se o PFC disser que se
usou PostgreSQL 18.1, deve referir-se à instalação local (opção usada), não ao Docker.

### Outros dados úteis

- Modelos embutidos: `modelo_milho_int8_dinamica.tflite` com 4 560 904 bytes e
  `modelo_mandioca_int8_dinamica.tflite` com 4 560 064 bytes (**4,35 MiB** cada, o que confirma
  o texto).
- Limiar de confiança na app: `limiarConfianca = 0.60` (`resultado_classificacao.dart`).
