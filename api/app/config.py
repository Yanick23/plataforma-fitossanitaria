"""Configuração lida de variáveis de ambiente (ou do ficheiro api/.env)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PASTA_API = Path(__file__).resolve().parent.parent


class Definicoes(BaseSettings):
    model_config = SettingsConfigDict(env_file=PASTA_API / ".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://agrodiagnostico:agrodiagnostico@localhost:5433/agrodiagnostico"

    jwt_segredo: str = "mude-esta-chave"
    jwt_algoritmo: str = "HS256"
    jwt_validade_dias: int = 30

    admin_telefone: str | None = None
    admin_palavra_passe: str | None = None
    admin_nome: str = "Administrador"

    # Origens do painel web autorizadas (CORS). No .env: CORS_ORIGENS=["http://localhost:5173"]
    cors_origens: list[str] = [f"http://{h}:{p}" for h in ("localhost", "127.0.0.1") for p in (5173, 5174, 4173)]

    # Previsão do tempo (risco meteorológico): Open-Meteo, gratuita e sem chave.
    meteo_url: str = "https://api.open-meteo.com/v1/forecast"
    meteo_validade_horas: float = 3.0  # depois disto pede-se uma previsão nova

    # SMS (API Ola, da Pavulla), como na integração da AquaSystem: POST {SMS_URL}/v1/messages/bulk,
    # autenticação HTTP Basic com o token como utilizador e palavra-passe vazia, números só com dígitos.
    # Sem SMS_CHAVE, a plataforma regista os SMS como SIMULADO e não envia nada (testes, demonstração).
    sms_url: str = "https://api.ola.pavulla.com"
    sms_chave: str | None = None
    sms_provider_id: str | None = None
    sms_remetente: str | None = None
    # Os telefones guardam-se sem indicativo (ex.: 841234567); acrescenta-se este aos números locais
    # de 9 dígitos. Vazio = enviar o número como está guardado.
    sms_indicativo: str = "258"
    sms_lote: int = 100                   # mensagens por pedido (o limite não está documentado)
    sms_max_caracteres: int = 300

    # Ficheiros guardados pela API (fora do Git).
    pasta_modelos: Path = PASTA_API / "modelos"
    pasta_imagens: Path = PASTA_API / "dados" / "imagens"


definicoes = Definicoes()
