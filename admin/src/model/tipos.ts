// Tipos do domínio, iguais aos esquemas da API (api/app/esquemas.py).

export type Perfil = 'AGRICULTOR' | 'TECNICO' | 'COORDENADOR' | 'INVESTIGADOR' | 'ADMINISTRADOR'
export type TipoPatologia = 'DOENCA' | 'PRAGA' | 'SAUDAVEL'
export type NivelAlerta = 'INFORMACAO' | 'AVISO' | 'URGENTE'
export type EstadoValidacao = 'PENDENTE' | 'CONFIRMADO' | 'CORRIGIDO'
export type EstadoVisita = 'PENDENTE' | 'AGENDADA' | 'RESOLVIDA' | 'CANCELADA'

export interface Utilizador {
  id: number
  nome: string
  telefone: string
  perfil: Perfil
  area: string | null
  distrito_id: number | null
  provincia_codigo: string | null
  activo: boolean
}

export interface UtilizadorAdmin extends Utilizador {
  criado_em: string
  distrito_nome: string | null
  provincia_nome: string | null
  diagnosticos: number
}

export interface Pagina<T> {
  total: number
  itens: T[]
}

export interface Provincia {
  codigo: string
  nome: string
}

export interface Distrito {
  id: number
  nome: string
  provincia_codigo: string
}

export interface Cultura {
  id: string
  nome: string
  nome_cientifico: string
}

export interface FotoReferencia {
  id: number
  legenda: string | null
  url: string // relativo à API, ex.: /fotos-referencia/3 (público)
}

export interface Patologia {
  id: number
  cultura_id: string
  codigo: string
  nome_local: string
  nome_cientifico: string
  tipo: TipoPatologia
  recomendacao: string
  sintomas: string | null
  prevencao: string | null
  declaracao_obrigatoria: boolean
  versao_conteudo: number
  validado_por_nome: string | null
  validado_em: string | null
  fotos: FotoReferencia[]
}

/** Campos do catálogo que o administrador escreve (o resto é calculado pela API). */
export type PatologiaEscrita = Pick<Patologia, 'cultura_id' | 'codigo' | 'nome_local' | 'nome_cientifico' | 'tipo'
  | 'recomendacao' | 'sintomas' | 'prevencao' | 'declaracao_obrigatoria'>

export interface Diagnostico {
  id: string
  utilizador_id: number
  cultura_id: string
  classe_prevista: string
  confianca: number
  data: string
  versao_modelo: number | null
  tempo_inferencia_ms: number | null
  tem_imagem: boolean
  validacao: EstadoValidacao
  classe_confirmada: string | null
  nota_tecnico: string | null
  utilizador_nome: string
  utilizador_telefone: string
  distrito_id: number | null
  distrito_nome: string | null
  provincia_codigo: string | null
  patologia_nome: string | null
  tipo: TipoPatologia | null
  tecnico_nome: string | null
  validado_em: string | null
}

export interface Contagem {
  chave: string
  nome: string
  total: number
}

export interface DiaContagem {
  dia: string
  total: number
  pragas: number
  doencas: number
}

export interface DistritoContagem {
  distrito_id: number
  distrito: string
  provincia_codigo: string
  total: number
  pragas_doencas: number
  agricultores: number
}

export interface Resumo {
  zona: string
  agricultores: number
  agricultores_novos_30d: number
  tecnicos: number
  diagnosticos: number
  diagnosticos_30d: number
  diagnosticos_30d_anteriores: number
  confianca_baixa_30d: number
  alertas_activos: number
  por_dia: DiaContagem[]
  por_classe: Contagem[]
  por_cultura: Contagem[]
  por_distrito: DistritoContagem[]
}

export interface Alerta {
  id: number
  titulo: string
  mensagem: string
  nivel: NivelAlerta
  cultura_id: string | null
  patologia_id: number | null
  patologia_nome: string | null
  provincia_codigo: string | null
  distrito_id: number | null
  zona: string
  autor_nome: string
  criado_em: string
  expira_em: string | null
  arquivado: boolean
  destinatarios: number
  lidos: number
}

export interface NovoAlerta {
  titulo: string
  mensagem: string
  nivel: NivelAlerta
  patologia_id: number | null
  provincia_codigo: string | null
  distrito_id: number | null
  expira_em: string | null
}

export interface Alcance {
  zona: string
  destinatarios: number
}

export type EstadoModelo = 'PILOTO' | 'PUBLICADO' | 'RETIRADO'

export interface Modelo {
  cultura_id: string
  versao: number
  classes: string[]
  acuracia_teste: number | null
  tamanho_bytes: number
  sha256: string
  url_ficheiro: string
  criado_em: string
  estado: EstadoModelo
  distritos_piloto: number[]
  notas: string | null
}

/** Pode a versão piloto passar a publicada? (validações em campo vs. a versão publicada) */
export interface PortaQualidade {
  versao: number
  validados: number
  exactidao: number | null
  referencia_versao: number | null
  referencia_exactidao: number | null
  aprovado: boolean
  motivo: string
}

export interface SemanaModelo {
  semana: string // segunda-feira, AAAA-MM-DD
  versao: number | null
  diagnosticos: number
  confianca_media: number
  taxa_baixa: number
  validados: number
  exactidao: number | null
}

export interface SinalDeriva {
  versao: number
  taxa_baixa_inicial: number
  taxa_baixa_recente: number
  diagnosticos_recentes: number
  deriva: boolean
  explicacao: string
}

export interface Monitorizacao {
  cultura_id: string
  semanas: SemanaModelo[]
  sinais: SinalDeriva[]
}

export interface Ocorrencia {
  distrito_id: number
  distrito: string
  provincia_codigo: string
  total: number
}

export interface Surto {
  distrito_id: number
  distrito: string
  provincia_codigo: string
  cultura_id: string
  classe: string
  patologia_nome: string
  tipo: TipoPatologia
  casos_recentes: number
  media_anterior: number
  razao: number | null
  nivel: NivelAlerta
}

export interface ExactidaoClasse {
  classe: string
  nome: string
  validados: number
  correctos: number
  exactidao: number | null
}

export interface ExactidaoVersao {
  cultura_id: string
  versao_modelo: number | null
  validados: number
  correctos: number
  exactidao: number | null
}

export interface Confusao {
  cultura_id: string
  prevista: string
  confirmada: string
  total: number
}

export interface ExactidaoCampo {
  zona: string
  validados: number
  correctos: number
  exactidao: number | null
  pendentes: number
  por_classe: ExactidaoClasse[]
  por_versao: ExactidaoVersao[]
  confusoes: Confusao[]
}

export interface Visita {
  id: number
  diagnostico_id: string
  estado: EstadoVisita
  mensagem: string | null
  data_agendada: string | null
  notas_tecnico: string | null
  criado_em: string
  actualizado_em: string
  agricultor_nome: string
  agricultor_telefone: string
  tecnico_nome: string | null
  distrito_nome: string | null
  cultura_id: string
  classe_prevista: string
  patologia_nome: string | null
}

export interface RegistoAuditoria {
  id: number
  utilizador_nome: string | null
  accao: string
  entidade: string
  entidade_id: string | null
  detalhes: string | null
  criado_em: string
}

// --- Boletim fitossanitário (fase 2) ---------------------------------------------------------

export interface LinhaBoletim {
  nome: string
  valor: number
  detalhe: string | null
}

export interface Declaracao {
  diagnostico_id: string
  cultura_id: string
  classe: string
  patologia_nome: string
  estado: 'CONFIRMADO' | 'SUSPEITA'
  confianca: number
  data: string
  distrito_nome: string | null
  provincia_codigo: string | null
  agricultor_nome: string
  agricultor_telefone: string
}

export interface EficaciaPatologia {
  cultura_id: string
  classe: string
  nome: string
  respostas: number
  seguiram: number
  melhoraram: number
  eficacia: number | null
}

export interface Boletim {
  zona: string
  inicio: string
  fim: string
  gerado_em: string
  diagnosticos: number
  diagnosticos_pragas_doencas: number
  agricultores_activos: number
  agricultores_novos: number
  taxa_confianca_baixa: number | null
  validados: number
  exactidao_campo: number | null
  alertas_enviados: number
  visitas_pedidas: number
  visitas_resolvidas: number
  dias_medios_resolucao: number | null
  principais_pragas: LinhaBoletim[]
  distritos_mais_afectados: LinhaBoletim[]
  alertas: Alerta[]
  surtos: Surto[]
  declaracoes: Declaracao[]
  eficacia: EficaciaPatologia[]
}

/** Aviso para a equipa (ex.: caso confirmado de praga de declaração obrigatória). */
export interface Notificacao {
  id: number
  tipo: string
  titulo: string
  mensagem: string
  diagnostico_id: string | null
  criado_em: string
  lida_em: string | null
}

export interface ListaNotificacoes {
  nao_lidas: number
  itens: Notificacao[]
}

/** Risco meteorológico: condições do tempo favoráveis a uma praga/doença num distrito (próximos 7 dias). */
export type NivelRisco = 'ALTO' | 'MEDIO'

export interface RiscoDistrito {
  distrito_id: number
  distrito: string
  provincia_codigo: string
  cultura_id: string
  classe: string
  patologia_id: number
  patologia_nome: string
  nivel: NivelRisco
  motivo: string
  dias_favoraveis: number
  de: string
  ate: string
  evidencia: 'moderada' | 'fraca'
  previsao_obtida_em: string
}

export interface RegraRisco {
  cultura_id: string
  classe: string
  patologia_nome: string
  condicao: string
  fontes: string[]
  evidencia: 'moderada' | 'fraca'
  limiares_de_projecto: string[]
}

export interface RiscoMeteorologico {
  gerado_em: string
  fonte: string
  aviso: string
  erro: string | null
  distritos_avaliados: number
  distritos_com_agricultores: number
  previsao_mais_antiga: string | null
  itens: RiscoDistrito[]
  regras: RegraRisco[]
}
