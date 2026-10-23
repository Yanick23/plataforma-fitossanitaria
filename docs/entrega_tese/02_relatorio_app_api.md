# Relatório para o PFC — Parte B (aplicação e API) e Parte C (texto × código)

Data: 2026-10-23. Ramo `main`, commit `e3f1c52` mais as alterações desta sessão (troca do nome visível).
A Parte A (Colab) não é tratada aqui.

---

## B1. Dispositivo de teste — **feito** (adb, 2026-10-23)

| Campo | Valor |
|---|---|
| Marca / modelo | SOTEN R80 (compilação `R80-FK26-T-EN-GMS-O`) |
| Android | 13 (API 33) |
| RAM total | 5,67 GB visíveis ao sistema (5 947 140 kB), ou seja, 6 GB nominais |
| Processador | MediaTek MT8788 (plataforma mt6771), **8 núcleos** até 1,99 GHz, arm64-v8a |

Ficheiro: `docs/entrega_tese/dados_telemovel/dispositivo.txt`.

### Teste de desempenho com imagem sintética (ecrã «Diagnóstico técnico»)

Mede só a inferência (`Interpreter.run`), com 1 thread, modelo INT8 v1 e 20 repetições depois
de uma de aquecimento. Versão release.

| Cultura | Média | Mín. | Máx. | Memória residente após o teste |
|---|---|---|---|---|
| Milho | 163,9 ms | 157 ms | 273 ms | 271,1 MB |
| Mandioca | 174,2 ms | 161 ms | 197 ms | 285,5 MB (pico 288,1 MB) |

Este valor não substitui o B2, que mede o tempo total com fotografias reais
(descodificação + pré-processamento + inferência).

## B2. Tempo total do diagnóstico — **feito** (SOTEN R80, APK release, 2026-10-23)

10 diagnósticos por cultura, feitos na app como um utilizador: cultura → Galeria → escolher a
imagem (teste CCMT) → resultado. Tempos em segundos, pela ordem em que foram feitos:

| Cultura | 10 tempos (s) | Média | Mín. | Máx. |
|---|---|---|---|---|
| Milho | 0,448 · 0,378 · 0,373 · 0,340 · 0,347 · 0,386 · 0,331 · 0,322 · 0,444 · 0,372 | **0,374** | 0,322 | 0,448 |
| Mandioca | 0,415 · 0,336 · 0,401 · 0,319 · 0,313 · 0,392 · 0,365 · 0,400 · 0,586 · 0,710 | **0,424** | 0,313 | 0,710 |

- **RNF03 cumprido com folga:** o pior caso (0,710 s) fica muito abaixo dos 3 s. A média dos 20
  é 0,399 s, igual ao valor que a app calcula no ecrã «Diagnóstico técnico» (398,9 ms).
- Composição média: inferência 0,223 s, pré-processamento cerca de 0,15 s; o resto é a leitura
  da imagem. Memória residente entre 303 e 318 MB.
- O 1.º diagnóstico de cada cultura inclui o carregamento do modelo: 32 ms no milho e 12 ms na
  mandioca. É pouco, porque o modelo é lido directamente da memória.
- Os dois últimos de mandioca (0,586 e 0,710 s) foram feitos com a bateria a 18–20% e sem
  carregador. É provável que o processador estivesse limitado nessa altura.
- Os valores por diagnóstico estão em `docs/entrega_tese/dados_telemovel/b2_tempos.csv`.

O código já mede o RNF03; não foi preciso acrescentar nada:

- o `Stopwatch` arranca quando a fotografia é confirmada (`app/lib/screens/captura_screen.dart:32`);
- pára quando as probabilidades estão prontas, logo antes de abrir o ecrã de resultado
  (`app/lib/services/classificador.dart`, `cronometroTotal.stop()`);
- cada diagnóstico fica no log (`AgroDiagnostico/inferencia ... total=XXXms`), no ecrã
  «Diagnóstico técnico» e em `registo_tecnico.csv`.

Nota para o texto: o tempo vai até ao **resultado pronto**, um frame antes de o ecrã aparecer
(da ordem de dezenas de milissegundos). Pode escrever «da confirmação da fotografia até o resultado
estar pronto a apresentar».

## B3. Testes funcionais T01–T13 — **12 aprovados, 1 bloqueado (T13)**

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

### Execução (2026-10-23, SOTEN R80, APK release)

**Ligação à API durante os testes:** o PC estava ligado ao hotspot do próprio telemóvel, numa
rede que o Windows classificou como «Pública». A firewall bloqueava a porta 8000 e o IP do PC
mudava a cada nova ligação. Por isso a app usou `http://127.0.0.1:8000` através de um túnel
`adb reverse tcp:8000 tcp:8000`, que também passa pela ligação Wi-Fi. A comunicação continua a
ser HTTP sem TLS, por isso o C10 mantém-se. Se o texto disser «numa rede local», a
configuração real da demonstração é esta.

| ID | Estado | O que aconteceu |
|---|---|---|
| T01 | **Aprovado** | Conta «Agricultor Teste» (841234567, Boane) criada na app. A app entrou logo no ecrã inicial, com o estado «Online». Na base de dados: perfil AGRICULTOR, hash `$2b$12$…` (bcrypt). Capturas 01b e 02. |
| T02 | **Aprovado** (variante) | Sem nenhuma rede activa (`dumpsys connectivity`: «Active default network: none»), a app foi fechada à força e reaberta. A sessão manteve-se e a app mostrou «Offline». Usou-se «dados móveis desligados» em vez do modo de voo, porque o modo de voo cortaria o adb sem fios. |
| T03 | **Aprovado** (pela galeria) | Milho, `milho_0013_mancha_da_folha` (teste CCMT) → «Mancha cinzenta da folha», 96%. Os diagnósticos foram feitos sem acesso ao servidor (túnel da API desligado). A rede móvel ficou ligada porque dá internet ao PC. **A câmara do telemóvel está avariada**: falha mesmo quando aberta directamente (`CamAp_QuickActivity onDestroy`, `Error configuring streams: Broken pipe`). Por isso usou-se a galeria. |
| T04 | **Aprovado** | Mandioca pela galeria, `mandioca_0010_mosaico` → «Mosaico da mandioca». Guardado como pendente. |
| T05 | **Aprovado** (pela galeria) | Fotografia de uma chávena de café (Wikimedia Commons, «A small cup of coffee»), no milho → «Possível: Mancha cinzenta da folha», **22%**, com o aviso «Não temos certeza — tente tirar outra foto…» e os botões «Tirar Nova Foto» / «Guardar Mesmo Assim». Captura 07. Neste caso o limiar travou o objecto estranho. O classificador continua fechado: um objecto mais parecido com uma folha pode passar dos 60%. |
| T06 | **Aprovado** | O resultado mostra o nome local (Mancha cinzenta da folha), o nome científico (*Cercospora zeina*), a confiança (96%) e a recomendação. Captura 06. |
| T07 | **Aprovado** | O historial mostrou «20 por sincronizar», com o ícone laranja em cada diagnóstico. Prova `provas/T07_historial_20_pendentes.png`. |
| T08 | **Aprovado** | Com o servidor de novo acessível, «Sincronizar agora» → a API passou de 0 para **20 diagnósticos + 20 imagens** deste utilizador (verificado em PostgreSQL), e o aviso «por sincronizar» desapareceu. |
| T09 | **Aprovado** | Com 3 pendentes, fechei a app à força 80 ms depois de tocar em «Sincronizar». A API ficou com 25 diagnósticos e **só 23 imagens**: a sincronização foi interrompida a meio. Ao reabrir, a app voltou a enviar o lote (a API respondeu «confirmados» para os UUID que já tinha) e enviou as 2 imagens em falta. Estado final: **25 diagnósticos, 25 UUID distintos, 25 imagens**. Nada perdido, nada duplicado. |
| T10 | **Aprovado** | O administrador alterou a recomendação da mancha cinzenta (`PUT /patologias/5`). Depois de sincronizar, o detalhe de um diagnóstico mostra o texto novo («[T10] Recomendação alterada pelo administrador…»). Prova `provas/T10_recomendacao_alterada.png`. No fim, a recomendação original foi reposta. |
| T11 | **Aprovado** | O administrador publicou a v2 do modelo de milho (`POST /modelos/milho`). Na sincronização, a app pediu `ultima-versao`, descarregou `/modelos/milho/2/ficheiro`, verificou o SHA-256 e a interface, e escreveu no log «modelo milho actualizado para a versão 2». O diagnóstico seguinte correu com `[milho v2]` (carregamento 26 ms). Usou-se o mesmo ficheiro INT8; a v2 ficou publicada na base de dados. |
| T12 | **Aprovado** | Ver B2: 20 tempos entre 0,313 e 0,710 s, todos ≤ 3 s. Fizeram-se mais de 60 inferências seguidas (20 do B2, 7 extra, 36 do teste com fotografias) sem nenhum encerramento inesperado da app. Pico de memória: 327,7 MB. |
| T13 | **Bloqueado** | «Ver onde o modelo olhou» → a app mostra «Falta o ficheiro modelo_milho.keras em api/modelos/» (a API responde 503). O fluxo está implementado, mas faltam os `.keras` do treino neste PC. Prova `provas/T13_gradcam_sem_keras.png`. |

### Teste com fotografias no telemóvel (36 imagens de teste do CCMT, 3 por classe)

O ecrã «Diagnóstico técnico» → «Executar com fotografias» corre o pipeline completo da app
(leitura, pré-processamento, TFLite INT8) sobre a pasta de teste.

| Cultura | Acertos | Abaixo de 60% |
|---|---|---|
| Milho | 19 / 21 | 1 (`milho_0011_listrado_do_milho` → mancha cinzenta, 57%) |
| Mandioca | 15 / 15 | 0 |
| **Total** | **34 / 36** | 1 |

Erros: `milho_0008_lagarta_do_cartucho` → besouro-da-folha (98%, sem aviso) e `milho_0011`
(acima). Tempo total médio: 0,500 s (0,307–0,643). Inferência média: 0,308 s. Por imagem:
`dados_telemovel/teste_fotografias_36.csv`. **Isto é só uma verificação de funcionamento**
(n = 36, 3 por classe). Não substitui a exactidão do teste completo (A2).

Nota: a mesma imagem pode dar confianças um pouco diferentes conforme o caminho. Por exemplo,
`mandioca_0002` deu 69% pela galeria e 82% no teste com fotografias. O `image_picker` volta a
gravar a fotografia em JPEG com qualidade 95 antes de a app a ler; o teste lê o ficheiro original.

Imagens usadas: 36 imagens do **conjunto de teste do CCMT** (3 por classe; divisão fixa, semente
42), descarregadas do Mendeley Data com `ml/src/descarregar_teste_ccmt.py`. Foram copiadas para
os álbuns `Pictures/Milho_teste` e `Pictures/Mandioca_teste` do telemóvel e escolhidas no
selector de ficheiros do Android.

## B4. Testes automáticos da API — **feito**

```
api/.venv/Scripts/python -m pytest      (Python 3.11.9, requirements.txt)
====================== 23 passed, 16 warnings in 28.06s =======================
```

**23 aprovados, 0 falhados.** O número coincide com o texto. Os 16 avisos são de depreciação
(pyparsing/matplotlib e Keras) e não afectam o resultado.

## B5. Capturas de ecrã — **12 de 13 feitas** (falta a 09)

Em `docs/entrega_tese/dados_telemovel/capturas/` (SOTEN R80, vertical, PNG, conta de teste):

| Ficheiro | Conteúdo |
|---|---|
| `01_inicio_sessao.png`, `01b_criar_conta.png` | Login e criação de conta |
| `02_ecra_inicial.png` | Ecrã inicial («Diagnóstico de culturas», estado Online) |
| `03_seleccao_cultura.png` | Escolha entre milho e mandioca |
| `04_captura.png` | Ecrã de captura (câmara / galeria) |
| `05_processamento.png` | «A analisar imagem…». O ecrã dura menos de 0,4 s, por isso a captura apanhou-o ainda a aparecer, um pouco esbatido. |
| `06_resultado_confianca_alta.png` | Mancha cinzenta da folha, *Cercospora zeina*, 96%, recomendação |
| `07_resultado_confianca_baixa.png` | Chávena (T05), 22%, aviso |
| `07b_resultado_confianca_baixa_folha.png` | Alternativa: folha real de listrado classificada com 58%, aviso |
| `08_historial.png` | 2 pendentes (laranja) + sincronizados (verde) |
| `10_administracao_ou_docs.png` | `/docs` no navegador do telemóvel |
| `11_diagnostico_tecnico.png` | Ecrã de desempenho com as 20 medições do B2 |
| **`09_detalhe_gradcam.png`** | **Em falta**: precisa dos `.keras` (ver T13) |

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
