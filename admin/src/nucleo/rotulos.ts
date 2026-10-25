import type { EstadoValidacao, EstadoVisita, NivelAlerta, Perfil, TipoPatologia } from '@/model/tipos'

export type Tom = 'neutro' | 'marca' | 'bom' | 'aviso' | 'critico' | 'info'

export const PERFIL: Record<Perfil, { nome: string; tom: Tom }> = {
  AGRICULTOR: { nome: 'Agricultor', tom: 'neutro' },
  TECNICO: { nome: 'Técnico', tom: 'info' },
  ADMINISTRADOR: { nome: 'Administrador', tom: 'marca' },
}

export const NIVEL: Record<NivelAlerta, { nome: string; tom: Tom }> = {
  INFORMACAO: { nome: 'Informação', tom: 'info' },
  AVISO: { nome: 'Aviso', tom: 'aviso' },
  URGENTE: { nome: 'Urgente', tom: 'critico' },
}

export const TIPO: Record<TipoPatologia, { nome: string; tom: Tom }> = {
  DOENCA: { nome: 'Doença', tom: 'neutro' },
  PRAGA: { nome: 'Praga', tom: 'neutro' },
  SAUDAVEL: { nome: 'Saudável', tom: 'bom' },
}

export const VALIDACAO: Record<EstadoValidacao, { nome: string; tom: Tom }> = {
  PENDENTE: { nome: 'Por validar', tom: 'neutro' },
  CONFIRMADO: { nome: 'Confirmado', tom: 'bom' },
  CORRIGIDO: { nome: 'Corrigido', tom: 'aviso' },
}

export const VISITA: Record<EstadoVisita, { nome: string; tom: Tom }> = {
  PENDENTE: { nome: 'Pendente', tom: 'aviso' },
  AGENDADA: { nome: 'Agendada', tom: 'info' },
  RESOLVIDA: { nome: 'Resolvida', tom: 'bom' },
  CANCELADA: { nome: 'Cancelada', tom: 'neutro' },
}

export const LIMIAR_CONFIANCA = 0.6 // o mesmo da app (RF05)

export const ACCOES_AUDITORIA: Record<string, string> = {
  'alerta.enviar': 'Enviou um alerta',
  'alerta.arquivar': 'Arquivou um alerta',
  'patologia.criar': 'Criou uma praga/doença',
  'patologia.actualizar': 'Alterou uma praga/doença',
  'patologia.apagar': 'Apagou uma praga/doença',
  'cultura.criar': 'Criou uma cultura',
  'cultura.actualizar': 'Alterou uma cultura',
  'modelo.publicar': 'Publicou um modelo',
  'utilizador.criar': 'Criou uma conta',
  'utilizador.actualizar': 'Alterou uma conta',
  'utilizador.repor_palavra_passe': 'Repôs uma palavra-passe',
  'diagnostico.validar': 'Validou um diagnóstico',
  'visita.pedir': 'Pediu uma visita',
  'visita.actualizar': 'Actualizou uma visita',
  'visita.cancelar': 'Cancelou uma visita',
}
