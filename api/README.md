# API AgroDiagnóstico (FastAPI)

Camada de serviço da plataforma (secções 4.4.2–4.4.5 do relatório): recebe os
diagnósticos feitos offline na app, autentica os utilizadores, gere o catálogo
de culturas e patologias, distribui novas versões do modelo e gera mapas
Grad-CAM.

| Tecnologia | Uso |
|---|---|
| FastAPI (Starlette + Pydantic) | Endpoints `async`, validação automática, OpenAPI/JSON Schema |
| Swagger UI / ReDoc | Documentação automática em `/docs` e `/redoc` |
| PostgreSQL 16 (Docker) | Base de dados do servidor |
| SQLAlchemy 2 (asyncpg) | Acesso assíncrono à base de dados |
| bcrypt + JWT | Palavras-passe com hash; token de autenticação |
| TensorFlow/Keras | Grad-CAM a partir dos modelos `.keras` do treino |
| pytest | Testes (SQLite temporário, não toca no PostgreSQL) |

## Endpoints

| Método | Caminho | Quem | Requisito |
|---|---|---|---|
| POST | `/auth/registar` | público (cria AGRICULTOR) | RF10 |
| POST | `/auth/login` | público | RF10 |
| POST | `/auth/renovar` | autenticado | 4.4.5 |
| GET | `/auth/eu` | autenticado | RF10 |
| POST | `/utilizadores` | ADMINISTRADOR (cria TECNICO) | RF10 |
| POST | `/diagnosticos` | autenticado (lote, idempotente por UUID) | RF09, RNF07 |
| POST | `/diagnosticos/{id}/imagem` | dono do diagnóstico | RF09, 4.4.4 |
| GET | `/diagnosticos` | agricultor: os seus; técnico: a sua área; admin: todos | RF08 |
| GET | `/diagnosticos/{id}/gradcam` | quem pode ver o diagnóstico | 4.6.6 |
| GET/POST/PUT | `/culturas` | leitura: todos; escrita: ADMINISTRADOR | RF11 |
| GET/POST/PUT/DELETE | `/patologias` | leitura: todos; escrita: ADMINISTRADOR | RF11 |
| GET | `/modelos/{cultura}/ultima-versao` | autenticado | RF12 |
| GET | `/modelos/{cultura}/{versao}/ficheiro` | autenticado | RF12 |
| POST | `/modelos/{cultura}` | ADMINISTRADOR | RF12 |

## Arrancar no PC (Windows, PowerShell, a partir da raiz do repositório)

```powershell
# 1. Ambiente Python (uma vez)
.venv\Scripts\activate
pip install -r api\requirements.txt

# 2. Configuração (uma vez): copie e edite as palavras-passe
copy api\.env.example api\.env

# 3. PostgreSQL (Docker Desktop tem de estar aberto)
cd api
docker compose up -d

# 4. Modelos (uma vez): copie para api\modelos\
#    modelo_milho.keras, modelo_mandioca.keras                 (Grad-CAM)
#    modelo_milho_int8_dinamica.tflite + classes_milho.json      (versão 1 do modelo)
#    modelo_mandioca_int8_dinamica.tflite + classes_mandioca.json

# 5. API, acessível na rede local (porta 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Abra `http://localhost:8000/docs`. Para usar os endpoints protegidos: faça
`POST /auth/login`, copie o `access_token` e clique em **Authorize**.

Na primeira execução são criadas as tabelas, as 2 culturas, as 12 patologias,
o administrador (`ADMIN_TELEFONE`/`ADMIN_PALAVRA_PASSE` do `.env`) e a versão 1
de cada modelo (se os `.tflite` estiverem em `api\modelos\`).

**Firewall:** na primeira vez, o Windows pergunta se o Python pode aceitar
ligações; permita em **redes privadas**, senão o telemóvel não chega à API.

## Testes

```powershell
cd api
python -m pytest -q
```

## Publicar uma nova versão do modelo (RF12)

Em `/docs`, como administrador: `POST /modelos/{cultura}` com o ficheiro
`.tflite`, a lista `classes` em JSON e, opcionalmente, `acuracia_teste`.
As apps descarregam-na na próxima sincronização.
