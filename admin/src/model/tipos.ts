// Tipos do domínio, iguais aos esquemas da API (api/app/esquemas.py).

export type Perfil = 'AGRICULTOR' | 'TECNICO' | 'ADMINISTRADOR'
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

export interface Patologia {
  id: number
  cultura_id: string
  codigo: string
  nome_local: string
  nome_cientifico: string
  tipo: TipoPatologia
  recomendacao: string
}

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

export interface Modelo {
  cultura_id: string
  versao: number
  classes: string[]
  acuracia_teste: number | null
  tamanho_bytes: number
  sha256: string
  url_ficheiro: string
  criado_em: string
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
