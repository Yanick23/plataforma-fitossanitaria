import { useEffect, useState } from 'react'
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { diagnosticosRepo, type FiltrosDiagnosticos } from '@/model/repositorios'
import type { Diagnostico, EstadoValidacao, TipoPatologia } from '@/model/tipos'
import { diasAtras } from '@/nucleo/formatos'
import { LIMIAR_CONFIANCA } from '@/nucleo/rotulos'
import { useNotificar } from '@/nucleo/notificacoes'

const LIMITE = 25

export interface FiltrosEcra {
  cultura: string
  classe: string
  tipo: TipoPatologia | ''
  provincia: string
  distrito: string
  periodo: '' | '7' | '30' | '90'
  validacao: EstadoValidacao | ''
  soBaixa: boolean
  ordem: 'recentes' | 'confianca'
}

const INICIAIS: FiltrosEcra = {
  cultura: '', classe: '', tipo: '', provincia: '', distrito: '', periodo: '', validacao: '', soBaixa: false, ordem: 'recentes',
}

export function useDiagnosticosViewModel(iniciais: Partial<FiltrosEcra> = {}) {
  const cliente = useQueryClient()
  const notificar = useNotificar()
  const [filtros, setFiltros] = useState<FiltrosEcra>({ ...INICIAIS, ...iniciais })
  const [deslocamento, setDeslocamento] = useState(0)
  const [aberto, setAberto] = useState<Diagnostico | null>(null)

  useEffect(() => setDeslocamento(0), [filtros])

  const pedido: FiltrosDiagnosticos = {
    cultura: filtros.cultura || undefined,
    classe: filtros.classe || undefined,
    tipo: filtros.tipo || undefined,
    provincia: filtros.provincia || undefined,
    distrito_id: filtros.distrito ? Number(filtros.distrito) : undefined,
    desde: filtros.periodo ? diasAtras(Number(filtros.periodo)) : undefined,
    validacao: filtros.validacao || undefined,
    confianca_max: filtros.soBaixa ? LIMIAR_CONFIANCA - 0.0001 : undefined,
    ordem: filtros.ordem,
    limite: LIMITE,
    deslocamento,
  }
  const lista = useQuery({
    queryKey: ['diagnosticos', pedido],
    queryFn: () => diagnosticosRepo.listar(pedido),
    placeholderData: keepPreviousData,
  })

  const validar = useMutation({
    mutationFn: (v: { id: string; classe: string; nota: string }) =>
      diagnosticosRepo.validar(v.id, v.classe, v.nota.trim() || null),
    onSuccess: (d) => {
      setAberto(d)
      notificar(d.validacao === 'CONFIRMADO' ? 'Diagnóstico confirmado' : 'Correcção registada; o agricultor recebe-a na sincronização')
      cliente.invalidateQueries({ queryKey: ['diagnosticos'] })
      cliente.invalidateQueries({ queryKey: ['exactidao'] })
      cliente.invalidateQueries({ queryKey: ['resumo'] })
    },
    onError: (e: Error) => notificar(e.message, 'erro'),
  })

  const alterar = <K extends keyof FiltrosEcra>(chave: K, valor: FiltrosEcra[K]) =>
    setFiltros((f) => {
      const novo = { ...f, [chave]: valor }
      if (chave === 'cultura') novo.classe = ''
      if (chave === 'provincia') novo.distrito = ''
      return novo
    })

  const activos = Object.entries(filtros).filter(([k, v]) => k !== 'ordem' && v !== '' && v !== false).length

  return {
    filtros, alterar, limpar: () => setFiltros(INICIAIS), activos,
    pagina: lista.data, aCarregar: lista.isLoading, aActualizar: lista.isFetching, erro: lista.error as Error | null,
    limite: LIMITE, deslocamento, setDeslocamento,
    aberto, abrir: setAberto, fechar: () => setAberto(null),
    validar: (id: string, classe: string, nota: string) => validar.mutate({ id, classe, nota }),
    aValidar: validar.isPending,
  }
}
