"""Esquemas Pydantic de todos os pedidos e respostas (validados automaticamente)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .tabelas import Perfil, TipoPatologia


class Esquema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Autenticação e utilizadores --------------------------------------------

TELEFONE = Field(min_length=9, max_length=20, pattern=r"^\+?\d{9,15}$", examples=["841234567"])


class Registo(Esquema):
    nome: str = Field(min_length=2, max_length=120)
    telefone: str = TELEFONE
    palavra_passe: str = Field(min_length=6, max_length=72)  # o bcrypt só usa 72 bytes
    area: str | None = Field(default=None, max_length=80, examples=["Boane"])


class UtilizadorCriar(Registo):
    """Criação por um administrador (permite escolher o perfil, ex.: TECNICO)."""

    perfil: Perfil = Perfil.AGRICULTOR


class Login(Esquema):
    telefone: str = TELEFONE
    palavra_passe: str


class UtilizadorLer(Esquema):
    id: int
    nome: str
    telefone: str
    perfil: Perfil
    area: str | None


class Token(Esquema):
    access_token: str
    token_type: str = "bearer"
    utilizador: UtilizadorLer


# --- Catálogo ---------------------------------------------------------------

class CulturaEscrever(Esquema):
    nome: str
    nome_cientifico: str


class CulturaCriar(CulturaEscrever):
    id: str = Field(pattern=r"^[a-z_]+$", examples=["milho"])


class CulturaLer(CulturaCriar):
    pass


class PatologiaEscrever(Esquema):
    nome_local: str
    nome_cientifico: str
    tipo: TipoPatologia
    recomendacao: str


class PatologiaCriar(PatologiaEscrever):
    cultura_id: str
    codigo: str = Field(pattern=r"^[a-z_]+$", examples=["mosaico"])


class PatologiaLer(PatologiaCriar):
    id: int


# --- Diagnósticos e sincronização -------------------------------------------

class DiagnosticoEnviar(Esquema):
    id: UUID  # gerado no telemóvel
    cultura_id: str
    classe_prevista: str
    confianca: float = Field(ge=0, le=1)
    data: datetime
    versao_modelo: int | None = None
    tempo_inferencia_ms: int | None = Field(default=None, ge=0)


class ResultadoSincronizacao(Esquema):
    # Ids gravados agora ou já existentes do mesmo utilizador: a app pode marcá-los SINCRONIZADO.
    confirmados: list[UUID]
    # Ids rejeitados (cultura/classe inválida ou id pertencente a outro utilizador).
    rejeitados: list[UUID]


class DiagnosticoLer(Esquema):
    id: UUID
    utilizador_id: int
    cultura_id: str
    classe_prevista: str
    confianca: float
    data: datetime
    versao_modelo: int | None
    tempo_inferencia_ms: int | None
    tem_imagem: bool


# --- Modelos ML -------------------------------------------------------------

class ModeloLer(Esquema):
    cultura_id: str
    versao: int
    classes: list[str]
    acuracia_teste: float | None
    tamanho_bytes: int
    sha256: str
    url_ficheiro: str
    criado_em: datetime
