FROM python:3.11-slim

# Dependências de sistema (curl para healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalação de dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Código da aplicação e ficheiros de configuração/migrações
COPY alembic.ini .
COPY migracoes/ ./migracoes/
COPY app/ ./app/

# Pastas de dados e modelos
RUN mkdir -p /app/dados/imagens /app/modelos

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=5 --start-period=30s \
  CMD curl -f http://localhost:8000/saude || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
