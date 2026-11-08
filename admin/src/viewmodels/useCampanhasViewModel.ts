import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { alertasRepo, campanhasRepo } from '@/model/repositorios'
import { useNotificar } from '@/nucleo/notificacoes'
import { useSessao } from '@/nucleo/sessao'
import type { Ambito } from './useAlertasViewModel'

export interface RascunhoCampanha {
  titulo: string
  mensagem: string
  cultura: string
  patologia: string // id em texto ('' = nenhuma em particular)
  ambito: Ambito
  provincia: string
  distrito: string
  inicio: string // AAAA-MM-DD
  fim: string
  sms: boolean
}

function dataDaqui(dias: number): string {
  const d = new Date()
  d.setDate(d.getDate() + dias)
  return d.toISOString().slice(0, 10)
}

/** Campanhas de vigilância activa: pedir aos agricultores de uma zona que fotografem uma cultura. */
export function useCampanhasViewModel() {
  const { utilizador, eAdministrador, podeOperar } = useSessao()
  const cliente = useQueryClient()
  const notificar = useNotificar()
  const [antigas, setAntigas] = useState(false)
  const lista = useQuery({ queryKey: ['campanhas', antigas], queryFn: () => campanhasRepo.listar(antigas) })

  // Zona de quem cria, como nos alertas: administrador = todas; técnico e coordenador = a sua zona.
  const tecnicoDistrito = !eAdministrador && utilizador?.distrito_id ? String(utilizador.distrito_id) : ''
  const tecnicoProvincia = !eAdministrador && !utilizador?.distrito_id ? utilizador?.provincia_codigo ?? '' : ''
  const ambitos: Ambito[] = eAdministrador ? ['distrito', 'provincia', 'pais'] : tecnicoDistrito ? ['distrito'] : ['provincia', 'distrito']

  const vazio = (): RascunhoCampanha => ({
    titulo: '', mensagem: 'Fotografe 3 plantas desta cultura, mesmo que pareçam saudáveis, e sincronize a app.',
    cultura: 'milho', patologia: '', ambito: ambitos[0], provincia: tecnicoProvincia, distrito: tecnicoDistrito,
    inicio: dataDaqui(0), fim: dataDaqui(7), sms: false,
  })
  const [aCriar, setACriar] = useState(false)
  const [rascunho, setRascunho] = useState<RascunhoCampanha>(vazio)

  const destino = useMemo(() => ({
    provincia: rascunho.ambito === 'provincia' ? rascunho.provincia || null : null,
    distrito_id: rascunho.ambito === 'distrito' && rascunho.distrito ? Number(rascunho.distrito) : null,
  }), [rascunho.ambito, rascunho.provincia, rascunho.distrito])
  const destinoCompleto = rascunho.ambito === 'pais' || destino.provincia !== null || destino.distrito_id !== null

  // Os destinatários de uma campanha são os mesmos de um alerta para a mesma zona.
  const alcance = useQuery({
    queryKey: ['alcance', destino],
    queryFn: () => alertasRepo.alcance(destino.provincia, destino.distrito_id),
    enabled: aCriar && destinoCompleto,
    retry: false,
  })

  const criar = useMutation({
    mutationFn: () => campanhasRepo.criar({
      titulo: rascunho.titulo.trim(), mensagem: rascunho.mensagem.trim(), cultura_id: rascunho.cultura,
      patologia_id: rascunho.patologia ? Number(rascunho.patologia) : null,
      provincia_codigo: destino.provincia, distrito_id: destino.distrito_id,
      inicio: rascunho.inicio, fim: rascunho.fim, enviar_sms: rascunho.sms,
    }),
    onSuccess: (c) => {
      notificar(`Campanha criada para ${c.agricultores} agricultor(es) — ${c.zona}${rascunho.sms ? ', também por SMS' : ''}`)
      setACriar(false)
      setRascunho(vazio())
      cliente.invalidateQueries({ queryKey: ['campanhas'] })
    },
    onError: (e: Error) => notificar(e.message, 'erro'),
  })

  const cancelar = useMutation({
    mutationFn: campanhasRepo.cancelar,
    onSuccess: () => {
      notificar('Campanha cancelada: deixa de aparecer na app')
      cliente.invalidateQueries({ queryKey: ['campanhas'] })
    },
    onError: (e: Error) => notificar(e.message, 'erro'),
  })

  const alterar = <K extends keyof RascunhoCampanha>(k: K, v: RascunhoCampanha[K]) =>
    setRascunho((r) => ({
      ...r, [k]: v,
      ...(k === 'provincia' && !tecnicoDistrito ? { distrito: '' } : {}),
      ...(k === 'cultura' ? { patologia: '' } : {}),
    }))

  const datasValidas = rascunho.inicio !== '' && rascunho.fim !== '' && rascunho.fim >= rascunho.inicio
  const valido = rascunho.titulo.trim().length >= 3 && rascunho.mensagem.trim().length >= 3 && destinoCompleto && datasValidas

  return {
    podeCriar: podeOperar,
    campanhas: lista.data ?? [], aCarregar: lista.isLoading, erro: lista.error as Error | null, antigas, setAntigas,
    aCriar, abrir: () => { setRascunho(vazio()); setACriar(true) }, fechar: () => setACriar(false),
    rascunho, alterar, ambitos, tecnicoDistrito, tecnicoProvincia, datasValidas,
    alcance: alcance.data, erroAlcance: alcance.error as Error | null, aCalcularAlcance: alcance.isFetching,
    valido, criar: () => criar.mutate(), aGuardar: criar.isPending,
    cancelar: (id: number) => cancelar.mutate(id),
  }
}
