// Repositórios: uma função por rota da API. A camada Model não sabe nada de ecrãs.

import { http } from './http'
import type {
  Alcance, Alerta, Boletim, Cultura, Diagnostico, Distrito, EstadoValidacao, EstadoVisita, ExactidaoCampo, Modelo,
  NovoAlerta, Ocorrencia, Pagina, Patologia, Perfil, Provincia, RegistoAuditoria, Resumo, Surto, TipoPatologia,
  Utilizador, UtilizadorAdmin, Visita,
} from './tipos'

const dados = <T>(p: Promise<{ data: T }>) => p.then((r) => r.data)

/** Remove parâmetros vazios antes de os enviar na query string. */
function limpar<T extends object>(params: T): Partial<T> {
  return Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')) as Partial<T>
}

export const authRepo = {
  entrar: (telefone: string, palavra_passe: string) =>
    dados(http.post<{ access_token: string; utilizador: Utilizador }>('/auth/login', { telefone, palavra_passe })),
  eu: () => dados(http.get<Utilizador>('/auth/eu')),
}

export const regioesRepo = {
  provincias: () => dados(http.get<Provincia[]>('/provincias')),
  distritos: () => dados(http.get<Distrito[]>('/distritos')),
}

export const painelRepo = {
  resumo: (dias: number) => dados(http.get<Resumo>('/gestao/resumo', { params: { dias } })),
}

export interface FiltrosDiagnosticos {
  cultura?: string
  classe?: string
  tipo?: TipoPatologia
  provincia?: string
  distrito_id?: number
  desde?: string
  ate?: string
  confianca_max?: number
  validacao?: EstadoValidacao
  ordem?: 'recentes' | 'confianca'
  limite?: number
  deslocamento?: number
}

export const diagnosticosRepo = {
  listar: (f: FiltrosDiagnosticos) =>
    dados(http.get<Pagina<Diagnostico>>('/gestao/diagnosticos', { params: limpar(f) })),
  validar: (id: string, classe_confirmada: string, nota: string | null) =>
    dados(http.put<Diagnostico>(`/diagnosticos/${id}/validacao`, { classe_confirmada, nota })),
  caminhoImagem: (id: string) => `/diagnosticos/${id}/imagem`,
  caminhoGradcam: (id: string) => `/diagnosticos/${id}/gradcam`,
}

export const catalogoRepo = {
  culturas: () => dados(http.get<Cultura[]>('/culturas')),
  patologias: () => dados(http.get<Patologia[]>('/patologias')),
  criarCultura: (c: Cultura) => dados(http.post<Cultura>('/culturas', c)),
  actualizarCultura: (c: Cultura) =>
    dados(http.put<Cultura>(`/culturas/${c.id}`, { nome: c.nome, nome_cientifico: c.nome_cientifico })),
  criarPatologia: (p: Omit<Patologia, 'id'>) => dados(http.post<Patologia>('/patologias', p)),
  actualizarPatologia: (p: Patologia) =>
    dados(http.put<Patologia>(`/patologias/${p.id}`, {
      nome_local: p.nome_local, nome_cientifico: p.nome_cientifico, tipo: p.tipo, recomendacao: p.recomendacao,
    })),
  apagarPatologia: (id: number) => http.delete(`/patologias/${id}`),
}

export const modelosRepo = {
  historico: (cultura: string) => dados(http.get<Modelo[]>(`/modelos/${cultura}`)),
  publicar: (cultura: string, ficheiro: File, classes: string[], acuracia: number | null) => {
    const form = new FormData()
    form.append('ficheiro', ficheiro)
    form.append('classes', JSON.stringify(classes))
    if (acuracia !== null) form.append('acuracia_teste', String(acuracia))
    return dados(http.post<Modelo>(`/modelos/${cultura}`, form, { timeout: 120_000 }))
  },
}

export interface FiltrosUtilizadores {
  q?: string
  perfil?: Perfil
  provincia?: string
  distrito_id?: number
  activo?: boolean
  limite?: number
  deslocamento?: number
}

export interface NovoUtilizador {
  nome: string
  telefone: string
  palavra_passe: string
  perfil: Perfil
  distrito_id: number | null
  provincia_codigo: string | null
}

export const utilizadoresRepo = {
  listar: (f: FiltrosUtilizadores) =>
    dados(http.get<Pagina<UtilizadorAdmin>>('/gestao/utilizadores', { params: limpar(f) })),
  criar: (u: NovoUtilizador) => dados(http.post<Utilizador>('/utilizadores', u)),
  actualizar: (id: number, alteracoes: Partial<Pick<UtilizadorAdmin, 'nome' | 'perfil' | 'distrito_id' | 'provincia_codigo' | 'activo'>>) =>
    dados(http.patch<UtilizadorAdmin>(`/gestao/utilizadores/${id}`, alteracoes)),
  reporPalavraPasse: (id: number, palavra_passe: string) =>
    http.post(`/gestao/utilizadores/${id}/palavra-passe`, { palavra_passe }),
}

export const alertasRepo = {
  listar: (arquivados: boolean) => dados(http.get<Alerta[]>('/alertas', { params: { arquivados } })),
  alcance: (provincia: string | null, distrito_id: number | null) =>
    dados(http.get<Alcance>('/alertas/alcance', { params: limpar({ provincia, distrito_id }) })),
  criar: (a: NovoAlerta) => dados(http.post<Alerta>('/alertas', a)),
  arquivar: (id: number) => http.post(`/alertas/${id}/arquivar`),
}

export const vigilanciaRepo = {
  ocorrencias: (f: { cultura?: string; classe?: string; tipo?: TipoPatologia; desde?: string }) =>
    dados(http.get<Ocorrencia[]>('/vigilancia/ocorrencias', { params: limpar(f) })),
  surtos: (p: { janela_dias?: number; semanas_base?: number; min_casos?: number; factor?: number } = {}) =>
    dados(http.get<Surto[]>('/vigilancia/surtos', { params: limpar(p) })),
}

export const validacoesRepo = {
  exactidao: (cultura?: string) =>
    dados(http.get<ExactidaoCampo>('/validacoes/exactidao', { params: limpar({ cultura }) })),
  caminhoExportar: '/validacoes/exportar',
}

export const visitasRepo = {
  listar: (estado?: EstadoVisita) => dados(http.get<Visita[]>('/visitas', { params: limpar({ estado }) })),
  actualizar: (id: number, alteracoes: { estado?: EstadoVisita; data_agendada?: string | null; notas_tecnico?: string | null }) =>
    dados(http.patch<Visita>(`/visitas/${id}`, alteracoes)),
}

export const auditoriaRepo = {
  listar: (f: { accao?: string; entidade?: string; limite?: number; deslocamento?: number }) =>
    dados(http.get<Pagina<RegistoAuditoria>>('/gestao/auditoria', { params: limpar(f) })),
}

/** Período do boletim: dias inteiros no formato AAAA-MM-DD. */
export interface PeriodoBoletim {
  inicio: string
  fim: string
}

export const boletimRepo = {
  obter: (p: PeriodoBoletim) => dados(http.get<Boletim>('/gestao/boletim', { params: p })),
  caminhoCsv: (p: PeriodoBoletim) => `/gestao/boletim.csv?inicio=${p.inicio}&fim=${p.fim}`,
}
