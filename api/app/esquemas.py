"""Esquemas Pydantic de todos os pedidos e respostas (validados automaticamente)."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .tabelas import EstadoModelo, EstadoVisita, NivelAlerta, Perfil, ResultadoTratamento, Seguiu, TipoPatologia


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
    lingua: str | None = Field(default=None, pattern=r"^[a-z]{3}$")  # para ouvir as mensagens (ISO 639-3)


class UtilizadorCriar(Registo):
    """Criação por um administrador (permite escolher o perfil, ex.: TECNICO)."""

    perfil: Perfil = Perfil.AGRICULTOR
    provincia_codigo: str | None = None  # técnico provincial ou coordenador (sem distrito)


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
    lingua: str | None = None


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
    # Opcionais: se não forem enviados, ficam como estão.
    sintomas: str | None = None
    prevencao: str | None = None
    declaracao_obrigatoria: bool = False


class PatologiaCriar(PatologiaEscrever):
    cultura_id: str
    codigo: str = Field(pattern=r"^[a-z_]+$", examples=["mosaico"])


class FotoLer(Esquema):
    id: int
    legenda: str | None
    url: str  # caminho relativo à API, ex.: /fotos-referencia/3


class AudioLer(Esquema):
    id: int
    lingua: str
    lingua_nome: str
    url: str  # caminho relativo à API, ex.: /audios/ficheiros/p3_vmw_1a2b3c4d5e.webm (muda a cada gravação)
    tipo_mime: str
    tamanho_bytes: int
    duracao_s: float | None
    patologia_id: int | None = None
    alerta_id: int | None = None
    autor_id: int
    autor_nome: str
    criado_em: datetime
    validado_por_nome: str | None = None
    validado_em: datetime | None = None
    reproducoes: int = 0


class PatologiaLer(PatologiaCriar):
    id: int
    versao_conteudo: int = 1
    validado_por_nome: str | None = None
    validado_em: datetime | None = None
    fotos: list[FotoLer] = []
    audios: list[AudioLer] = []  # só as gravações já validadas (são as que a app descarrega)


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
    seguimento_respondido: bool = False  # a app só pergunta «a planta melhorou?» uma vez


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
    enviar_sms: bool = False  # também por SMS, para quem não abre a app


class ResumoSMS(Esquema):
    total: int = 0
    pendente: int = 0
    enviado: int = 0
    falhou: int = 0
    simulado: int = 0
    simulacao: bool = True  # sem fornecedor configurado: os SMS não saem


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
    sms: ResumoSMS | None = None
    audios: list[AudioLer] = []


class AlertaAgricultorLer(Esquema):
    id: int
    titulo: str
    mensagem: str
    nivel: NivelAlerta
    cultura_id: str | None
    patologia_id: int | None
    patologia_codigo: str | None = None  # a app procura a praga no catálogo local por cultura + código
    zona: str
    criado_em: datetime
    expira_em: datetime | None
    lido: bool
    audios: list[AudioLer] = []


class AlcanceAlerta(Esquema):
    zona: str
    destinatarios: int
    sms_simulacao: bool = True  # sem fornecedor de SMS configurado, os SMS ficam simulados


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
    por_distrito: list["ExactidaoDistrito"] = []
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
    # Decisão do técnico sobre este sinal, nesta janela (None = por decidir)
    decisao: str | None = None   # CONFIRMADO ou DESCARTADO
    decisao_nota: str | None = None
    decidido_por: str | None = None
    decidido_em: datetime | None = None


class DecisaoSurtoEscrever(Esquema):
    distrito_id: int
    cultura_id: str
    classe: str
    decisao: str = Field(pattern="^(CONFIRMADO|DESCARTADO)$")
    nota: str | None = Field(default=None, max_length=500)


class Ocorrencia(Esquema):
    distrito_id: int
    distrito: str
    provincia_codigo: str
    total: int
    # Tendência: com os mesmos filtros, mas nos últimos 7 dias e nos 7 anteriores
    ultimos_7d: int = 0
    anteriores_7d: int = 0


class SemanaContagem(Esquema):
    semana: date  # segunda-feira da semana
    total: int
    pragas_doencas: int


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


class NotificacaoLer(Esquema):
    id: int
    tipo: str
    titulo: str
    mensagem: str
    diagnostico_id: UUID | None
    criado_em: datetime
    lida_em: datetime | None


class ListaNotificacoes(Esquema):
    nao_lidas: int
    itens: list[NotificacaoLer]


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
    estado: EstadoModelo = EstadoModelo.PUBLICADO
    distritos_piloto: list[int] = []
    notas: str | None = None


class ModeloActualizar(Esquema):
    estado: EstadoModelo | None = None
    distritos_piloto: list[int] | None = None
    notas: str | None = None
    forcar: bool = False  # passar à frente da porta de qualidade (fica na auditoria)


class SemanaModelo(Esquema):
    semana: str  # segunda-feira da semana, AAAA-MM-DD
    versao: int | None
    diagnosticos: int
    confianca_media: float
    taxa_baixa: float  # proporção com confiança < 60%
    validados: int
    exactidao: float | None


class SinalDeriva(Esquema):
    versao: int
    taxa_baixa_inicial: float
    taxa_baixa_recente: float
    diagnosticos_recentes: int
    deriva: bool
    explicacao: str


class Monitorizacao(Esquema):
    cultura_id: str
    semanas: list[SemanaModelo]
    sinais: list[SinalDeriva]


class PortaQualidade(Esquema):
    versao: int
    validados: int
    exactidao: float | None
    referencia_versao: int | None
    referencia_exactidao: float | None
    aprovado: bool
    motivo: str


# --- Seguimento do tratamento --------------------------------------------------

class SeguimentoEscrever(Esquema):
    seguiu: Seguiu
    resultado: ResultadoTratamento
    comentario: str | None = Field(default=None, max_length=500)


class EficaciaPatologia(Esquema):
    cultura_id: str
    classe: str
    nome: str
    respostas: int
    seguiram: int        # SIM ou PARCIAL
    melhoraram: int      # dos que seguiram
    eficacia: float | None  # melhoraram / seguiram


# --- Declaração obrigatória ------------------------------------------------------

class Declaracao(Esquema):
    diagnostico_id: UUID
    cultura_id: str
    classe: str
    patologia_nome: str
    estado: str  # CONFIRMADO (validado pelo técnico) ou SUSPEITA (só previsto pelo modelo)
    confianca: float
    data: datetime
    distrito_nome: str | None
    provincia_codigo: str | None
    agricultor_nome: str
    agricultor_telefone: str


# --- Boletim ------------------------------------------------------------------

class LinhaBoletim(Esquema):
    nome: str
    valor: int
    detalhe: str | None = None


class Boletim(Esquema):
    zona: str
    inicio: datetime
    fim: datetime
    gerado_em: datetime
    diagnosticos: int
    diagnosticos_pragas_doencas: int
    agricultores_activos: int
    agricultores_novos: int
    taxa_confianca_baixa: float | None
    validados: int
    exactidao_campo: float | None
    alertas_enviados: int
    visitas_pedidas: int
    visitas_resolvidas: int
    dias_medios_resolucao: float | None
    principais_pragas: list[LinhaBoletim]
    distritos_mais_afectados: list[LinhaBoletim]
    alertas: list[AlertaLer]
    surtos: list[Surto]
    declaracoes: list[Declaracao]
    eficacia: list[EficaciaPatologia]


# --- Risco meteorológico ----------------------------------------------------------------

class RiscoDistrito(Esquema):
    distrito_id: int
    distrito: str
    provincia_codigo: str
    cultura_id: str
    classe: str
    patologia_id: int
    patologia_nome: str
    nivel: str  # ALTO ou MEDIO
    motivo: str
    dias_favoraveis: int
    de: date
    ate: date
    evidencia: str
    previsao_obtida_em: datetime


class RegraRisco(Esquema):
    cultura_id: str
    classe: str
    patologia_nome: str
    condicao: str
    fontes: list[str]
    evidencia: str
    limiares_de_projecto: list[str]


class RiscoMeteorologico(Esquema):
    gerado_em: datetime
    fonte: str
    aviso: str
    erro: str | None
    distritos_avaliados: int
    distritos_com_agricultores: int
    previsao_mais_antiga: datetime | None
    itens: list[RiscoDistrito]
    regras: list[RegraRisco]


# --- Campanhas de vigilância activa ----------------------------------------------------

class CampanhaCriar(Esquema):
    titulo: str = Field(min_length=3, max_length=120)
    mensagem: str = Field(min_length=3, max_length=1000)
    cultura_id: str
    patologia_id: int | None = None  # praga a procurar (opcional)
    provincia_codigo: str | None = None
    distrito_id: int | None = None
    inicio: date
    fim: date
    enviar_sms: bool = False


class CampanhaLer(Esquema):
    id: int
    titulo: str
    mensagem: str
    cultura_id: str
    patologia_id: int | None
    patologia_nome: str | None
    provincia_codigo: str | None
    distrito_id: int | None
    zona: str
    inicio: date
    fim: date
    estado: str  # AGENDADA, ACTIVA, TERMINADA, CANCELADA
    autor_nome: str
    criado_em: datetime
    # Progresso: agricultores activos da zona e quantos enviaram pelo menos um diagnóstico da
    # cultura no período (também conta «está saudável»).
    agricultores: int
    responderam: int
    taxa_resposta: float | None
    diagnosticos: int
    casos_praga_doenca: int
    casos_patologia: int | None  # diagnósticos da praga procurada (se houver)
    sms: ResumoSMS | None = None


class CampanhaAgricultorLer(Esquema):
    id: int
    titulo: str
    mensagem: str
    cultura_id: str
    patologia_codigo: str | None
    zona: str
    inicio: date
    fim: date
    respondeu: bool


# --- Novidades (consulta em segundo plano da app) ---------------------------------------

class NovidadeAlerta(Esquema):
    id: int
    titulo: str
    nivel: NivelAlerta


class NovidadeValidacao(Esquema):
    diagnostico_id: str
    classe_confirmada: str
    correcto: bool


class NovidadeVisita(Esquema):
    id: int
    estado: EstadoVisita
    data_agendada: datetime | None


class NovidadeCampanha(Esquema):
    id: int
    titulo: str
    fim: date


class Novidades(Esquema):
    """O que mudou para o agricultor desde `desde` (a app mostra notificações locais)."""

    agora: datetime  # a app guarda este valor e envia-o como `desde` na consulta seguinte
    alertas: list[NovidadeAlerta]
    validacoes: list[NovidadeValidacao]
    visitas: list[NovidadeVisita]
    campanhas: list[NovidadeCampanha]


# --- Calendário agrícola ---------------------------------------------------------------

class FonteCalendario(Esquema):
    id: str
    referencia: str
    url: str | None = None


class AvisoCalendario(Esquema):
    cultura_id: str
    classe: str | None
    patologia_nome: str | None
    texto: str
    confianca: str  # alta, media
    fontes: list[str]


class MesCalendario(Esquema):
    mes: int  # 1 a 12
    actividades: list[str]
    avisos: list[AvisoCalendario]


class Calendario(Esquema):
    provincia_codigo: str
    provincia: str
    regiao: str
    sementeira: str | None  # época habitual de sementeira na província (MASA)
    meses: list[MesCalendario]
    fontes: list[FonteCalendario]
    aviso: str


class ExactidaoDistrito(Esquema):
    distrito_id: int | None
    distrito: str
    validados: int
    correctos: int
    exactidao: float | None


ExactidaoCampo.model_rebuild()


# --- Línguas locais e áudio (funcionalidade 14) --------------------------------

class LinguaLer(Esquema):
    codigo: str
    nome: str
    provincias: list[str]  # onde é mais falada (só para sugerir o que gravar primeiro)


class LinguaEscrever(Esquema):
    lingua: str | None = Field(default=None, pattern=r"^[a-z]{3}$")  # None = só texto


class Reproducao(Esquema):
    audio_id: int
    vezes: int = Field(ge=1, le=1000)


class EstadoAudio(Esquema):
    id: int
    validado: bool


class LinhaCobertura(Esquema):
    patologia_id: int
    cultura_id: str
    codigo: str
    nome: str
    tipo: TipoPatologia
    audios: dict[str, EstadoAudio]  # por código de língua; as que faltam não aparecem


class CoberturaAudio(Esquema):
    linguas: list[LinguaLer]
    patologias: list[LinhaCobertura]
    agricultores_por_lingua: dict[str, int]  # na zona de quem pede
    agricultores_sem_lingua: int
    por_validar: int
