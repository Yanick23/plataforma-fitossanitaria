import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { calendarioRepo } from '@/model/repositorios'
import { useSessao } from '@/nucleo/sessao'
import { useRegioes } from './referencias'

/** Calendário agrícola de uma província (funcionalidade 10): começa na província de quem entra. */
export function useCalendarioViewModel() {
  const { utilizador } = useSessao()
  const regioes = useRegioes()
  const propria = utilizador?.provincia_codigo
    ?? (utilizador?.distrito_id ? regioes.distrito(utilizador.distrito_id)?.provincia_codigo : undefined)
  const [escolhida, setProvincia] = useState('')
  const provincia = escolhida || propria || 'MZ-L'
  const cal = useQuery({ queryKey: ['calendario', provincia], queryFn: () => calendarioRepo.obter(provincia), staleTime: 3_600_000 })
  return {
    provincia, setProvincia, opcoesProvincias: regioes.opcoesProvincias,
    calendario: cal.data, aCarregar: cal.isLoading, erro: cal.error as Error | null,
    mesActual: new Date().getMonth() + 1,
  }
}
