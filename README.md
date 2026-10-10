# Plataforma de diagnóstico fitossanitário — AgroDiagnóstico

Diagnóstico automatizado de doenças e pragas em folhas de milho e mandioca,
com aprendizagem automática (EfficientNetB0 + TFLite), uma app Flutter para
Android que funciona offline e uma API FastAPI com PostgreSQL.

```
ml/    treino e avaliação dos modelos (Python, TensorFlow/Keras, Colab)
app/   app Android "AgroDiagnóstico" (Flutter, tflite_flutter, SQLite)
api/   API REST (FastAPI, PostgreSQL, JWT, Grad-CAM)   → ver api/README.md
```

## Fluxo da plataforma

1. Na app, o utilizador entra (telefone + palavra-passe) — só é preciso rede na primeira vez.
2. Escolhe a cultura, fotografa a folha e o modelo TFLite dessa cultura corre no
   telemóvel, sem internet. A app mostra a classe, a confiança, o nome local e
   científico e uma recomendação; abaixo de 60% de confiança sugere nova foto.
3. O diagnóstico fica no historial (SQLite) como PENDENTE.
4. Quando há rede, a app envia os pendentes à API (cada um com um UUID, para não
   duplicar), envia as fotografias e só então os marca como SINCRONIZADO. Na mesma
   sincronização actualiza o catálogo e descarrega novas versões do modelo.
5. Na API, o técnico vê os diagnósticos dos agricultores da sua área, o
   administrador gere o catálogo e publica modelos, e qualquer diagnóstico
   sincronizado pode ser explicado com Grad-CAM.

## Preparação dos dados e treino (ml/)

1. Copiar a pasta **Raw Data** do CCMT (Mensah et al., 2023) para `ml/data/raw/`.
   Não usar a versão aumentada (fuga de dados entre treino e teste).
2. `pip install -r ml/requirements.txt` (Python 3.11)
3. `python ml/src/gerar_metadados.py` e `python ml/src/dividir_dados.py`
4. Treino no Google Colab com `ml/notebooks/02_treino.ipynb`.

Os ficheiros em `ml/data/divisoes/` são a divisão fixa reutilizada em todas as experiências.

## App (app/)

Copiar para `app/assets/models/` os modelos exportados (Google Drive, `PFC/modelos_tflite`):
`modelo_milho_int8_dinamica.tflite`, `classes_milho.json`,
`modelo_mandioca_int8_dinamica.tflite`, `classes_mandioca.json`. Depois:

```
cd app
flutter build apk --release
flutter install            # com o telemóvel ligado por USB ou Wi-Fi (depuração)
```

O APK fica em `app/build/app/outputs/flutter-apk/app-release.apk`.
