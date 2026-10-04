# Plataforma de diagnóstico fitossanitário

Diagnóstico automatizado de doenças e pragas em folhas de milho e mandioca,
com aprendizagem automática (EfficientNetB0 + TFLite), uma API FastAPI e
uma aplicação Flutter para Android.

## Estrutura

```
ml/
  data/raw/      imagens em bruto do CCMT (não versionadas)
  data/          metadados.csv e divisoes/divisao_<cultura>.csv
  notebooks/     notebooks de treino (Google Colab)
  src/           scripts Python
  models/        modelos treinados (.keras, .tflite)
  reports/       métricas, matrizes de confusão e Grad-CAM
api/             API FastAPI
app/             aplicação Flutter
```

## Preparação dos dados

1. Descarregar o CCMT (Mensah et al., 2023) e copiar **apenas a pasta
   "Raw Data"** para `ml/data/raw/`. Não usar a versão aumentada: as cópias
   aumentadas da mesma imagem podiam cair em treino e teste (fuga de dados).
2. Instalar as dependências (Python 3.11):
   ```
   pip install -r ml/requirements.txt
   ```
3. Gerar os metadados e a divisão (uma única vez):
   ```
   python ml/src/gerar_metadados.py
   python ml/src/dividir_dados.py
   ```

Os ficheiros em `ml/data/divisoes/` devem ser versionados: são a divisão
fixa reutilizada em todas as experiências.
