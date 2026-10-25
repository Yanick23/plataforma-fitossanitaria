"""Esquemas Pydantic de todos os pedidos e respostas (validados automaticamente)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .tabelas import EstadoVisita, NivelAlerta, Perfil, TipoPatologia


class Esquema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Autenticação e utilizadores --------------------------------------------

TELEFONE = Field(min_length=9, max_length=20, pattern=r"^\+?\d{9,15}$", examples=["841234567"])


class Registo(Esquema):
    nome: str = Field(min_length=2, max_length=120)
    telefone: str = TELEFONE
    palavra_passe: str = Field(min_length=6, max_length=72)  # o bcrypt só usa 72 bytes
    area: str | None = Field(default=None, max_length=80, examples=["Boane"])
    distrito_id: int | None = None  # se vier, tem prioridade sobre a área em texto


class UtilizadorCriar(Registo):
    """Criação por um administrador (permite escolher o perfil, ex.: TECNICO)."""

    perfil: Perfil = Perfil.AGRICULTOR
    provincia_codigo: str | None = None  # técnico provincial (sem distrito)


class Login(Esquema):
    telefone: str = TELEFONE
    palavra_passe: str


class UtilizadorLer(Esquema):
    id: int
    nome: str
    telefone: str
    perfil: Perfil
    area: str | None
    distrito_id: int | None = None
    provincia_codigo: str | None = None
    activo: bool = True


class UtilizadorAdminLer(UtilizadorLer):
    criado_em: datetime
    distrito_nome: str | None = None
    provincia_nome: str | None = None
    diagnosticos: int = 0


class UtilizadorActualizar(Esquema):
    """Só os campos enviados são alterados."""

    nome: str | None = Field(default=None, min_length=2, max_length=120)
    perfil: Perfil | None = None
    distrito_id: int | None = None
    provincia_codigo: str | None = None
    activo: bool | None = None


class NovaPalavraPasse(Esquema):
    palavra_passe: str = Field(min_length=6, max_length=72)


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
    # Validação pelo técnico (a app mostra «Confirmado» ou «Corrigido: ...»).
    validacao: str = "PENDENTE"  # PENDENTE | CONFIRMADO | CORRIGIDO
    classe_confirmada: str | None = None
    nota_tecnico: str | None = None


class DiagnosticoAdminLer(DiagnosticoLer):
    utilizador_nome: str
    utilizador_telefone: str
    distrito_id: int | None
    distrito_nome: str | None
    provincia_codigo: str | None
    patologia_nome: str | None
    tipo: TipoPatologia | None
    tecnico_nome: str | None = None
    validado_em: datetime | None = None


class PaginaDiagnosticos(Esquema):
    total: int
    itens: list[DiagnosticoAdminLer]


class PaginaUtilizadores(Esquema):
    total: int
    itens: list[UtilizadorAdminLer]


# --- Regiões ----------------------------------------------------------------

class ProvinciaLer(Esquema):
    codigo: str
    nome: str


class DistritoLer(Esquema):
    id: int
    nome: str
    provincia_codigo: str


# --- Painel -----------------------------------------------------------------

class Contagem(Esquema):
    chave: str
    nome: str
    total: int


class DiaContagem(Esquema):
    dia: str  # AAAA-MM-DD
    total: int
    pragas: int
    doencas: int


class DistritoContagem(Esquema):
    distrito_id: int
    distrito: str
    provincia_codigo: str
    total: int
    pragas_doencas: int
    agricultores: int


class Resumo(Esquema):
    zona: str
    agricultores: int
    agricultores_novos_30d: int
    tecnicos: int
    diagnosticos: int
    diagnosticos_30d: int
    diagnosticos_30d_anteriores: int
    confianca_baixa_30d: int
    alertas_activos: int
    por_dia: list[DiaContagem]
    por_classe: list[Contagem]
    por_cultura: list[Contagem]
    por_distrito: list[DistritoContagem]


# --- Alertas ----------------------------------------------------------------

class AlertaCriar(Esquema):
    titulo: str = Field(min_length=3, max_length=120)
    mensagem: str = Field(min_length=3, max_length=2000)
    nivel: NivelAlerta = NivelAlerta.AVISO
    cultura_id: str | None = None
    patologia_id: int | None = None
    provincia_codigo: str | None = None
    distrito_id: int | None = None
    expira_em: datetime | None = None


class AlertaLer(Esquema):
    id: int
    titulo: str
    mensagem: str
    nivel: NivelAlerta
    cultura_id: str | None
    patologia_id: int | None
    patologia_nome: str | None
    provincia_codigo: str | None
    distrito_id: int | None
    zona: str
    autor_nome: str
    criado_em: datetime
    expira_em: datetime | None
    arquivado: bool
    destinatarios: int
    lidos: int


class AlertaAgricultorLer(Esquema):
    id: int
    titulo: str
    mensagem: str
    nivel: NivelAlerta
    cultura_id: str | None
    patologia_id: int | None
    zona: str
    criado_em: datetime
    expira_em: datetime | None
    lido: bool


class AlcanceAlerta(Esquema):
    zona: str
    destinatarios: int


# --- Validação pelo técnico ---------------------------------------------------

class ValidacaoEscrever(Esquema):
    classe_confirmada: str = Field(min_length=1, max_length=60)
    nota: str | None = Field(default=None, max_length=1000)


class ExactidaoClasse(Esquema):
    classe: str
    nome: str
    validados: int
    correctos: int
    exactidao: float | None


class ExactidaoVersao(Esquema):
    cultura_id: str
    versao_modelo: int | None
    validados: int
    correctos: int
    exactidao: float | None


class Confusao(Esquema):
    cultura_id: str
    prevista: str
    confirmada: str
    total: int


class ExactidaoCampo(Esquema):
    zona: str
    validados: int
    correctos: int
    exactidao: float | None
    pendentes: int
    por_classe: list[ExactidaoClasse]
    por_versao: list[ExactidaoVersao]
    confusoes: list[Confusao]


# --- Pedidos de visita --------------------------------------------------------

class VisitaCriar(Esquema):
    diagnostico_id: UUID
    mensagem: str | None = Field(default=None, max_length=1000)


class VisitaActualizar(Esquema):
    """O técnico agenda, resolve ou cancela; só os campos enviados mudam."""

    estado: EstadoVisita | None = None
    data_agendada: datetime | None = None
    notas_tecnico: str | None = Field(default=None, max_length=2000)


class VisitaLer(Esquema):
    id: int
    diagnostico_id: UUID
    estado: EstadoVisita
    mensagem: str | None
    data_agendada: datetime | None
    notas_tecnico: str | None
    criado_em: datetime
    actualizado_em: datetime
    agricultor_nome: str
    agricultor_telefone: str
    tecnico_nome: str | None
    distrito_nome: str | None
    cultura_id: str
    classe_prevista: str
    patologia_nome: str | None


# --- Vigilância ---------------------------------------------------------------

class Surto(Esquema):
    distrito_id: int
    distrito: str
    provincia_codigo: str
    cultura_id: str
    classe: str
    patologia_nome: str
    tipo: TipoPatologia
    casos_recentes: int          # nos últimos `janela_dias`
    media_anterior: float        # média por janela nas `semanas_base` anteriores
    razao: float | None          # casos_recentes / media_anterior (None se a média for 0)
    nivel: NivelAlerta           # AVISO ou URGENTE, conforme a subida


class Ocorrencia(Esquema):
    distrito_id: int
    distrito: str
    provincia_codigo: str
    total: int


# --- Auditoria ----------------------------------------------------------------

class AuditoriaLer(Esquema):
    id: int
    utilizador_nome: str | None
    accao: str
    entidade: str
    entidade_id: str | None
    detalhes: str | None
    criado_em: datetime


class PaginaAuditoria(Esquema):
    total: int
    itens: list[AuditoriaLer]


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
