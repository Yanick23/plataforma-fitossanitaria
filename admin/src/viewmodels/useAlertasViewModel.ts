import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { alertasRepo } from '@/model/repositorios'
import type { NivelAlerta } from '@/model/tipos'
import { useNotificar } from '@/nucleo/notificacoes'
import { useSessao } from '@/nucleo/sessao'

export type Ambito = 'distrito' | 'provincia' | 'pais'

export interface Rascunho {
  titulo: string
  mensagem: string
  nivel: NivelAlerta
  patologia: string // id em texto ('' = nenhuma)
  ambito: Ambito
  provincia: string
  distrito: string
  validade: string // AAAA-MM-DD ou ''
}

export interface Preenchimento {
  titulo?: string
  mensagem?: string
  nivel?: NivelAlerta
  patologia_id?: number
  distrito_id?: number
  provincia_codigo?: string
}

function dataDaqui(dias: number): string {
  const d = new Date()
  d.setDate(d.getDate() + dias)
  return d.toISOString().slice(0, 10)
}

export function useAlertasViewModel(preenchimento?: Preenchimento | null) {
  const { utilizador, eAdministrador } = useSessao()
  const cliente = useQueryClient()
  const notificar = useNotificar()
  const [arquivados, setArquivados] = useState(false)
  const lista = useQuery({ queryKey: ['alertas', arquivados], queryFn: () => alertasRepo.listar(arquivados) })

  // Âmbitos permitidos a quem envia: administrador = todos; técnico = só a sua zona.
  const tecnicoDistrito = !eAdministrador && utilizador?.distrito_id ? String(utilizador.distrito_id) : ''
  const tecnicoProvincia = !eAdministrador && !utilizador?.distrito_id ? utilizador?.provincia_codigo ?? '' : ''
  const ambitos: Ambito[] = eAdministrador ? ['distrito', 'provincia', 'pais'] : tecnicoDistrito ? ['distrito'] : ['provincia', 'distrito']

  const vazio = (): Rascunho => ({
    titulo: '', mensagem: '', nivel: 'AVISO', patologia: '', ambito: ambitos[0],
    provincia: tecnicoProvincia, distrito: tecnicoDistrito, validade: dataDaqui(14),
  })
  const [aCompor, setACompor] = useState(false)
  const [rascunho, setRascunho] = useState<Rascunho>(vazio)

  useEffect(() => {
    if (!preenchimento) return
    setRascunho({
      ...vazio(),
      titulo: preenchimento.titulo ?? '',
      mensagem: preenchimento.mensagem ?? '',
      nivel: preenchimento.nivel ?? 'AVISO',
      patologia: preenchimento.patologia_id ? String(preenchimento.patologia_id) : '',
      ambito: preenchimento.distrito_id ? 'distrito' : preenchimento.provincia_codigo ? 'provincia' : ambitos[0],
      distrito: preenchimento.distrito_id ? String(preenchimento.distrito_id) : tecnicoDistrito,
      provincia: preenchimento.provincia_codigo ?? tecnicoProvincia,
    })
    setACompor(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [preenchimento])

  const destino = useMemo(() => ({
    provincia: rascunho.ambito === 'provincia' ? rascunho.provincia || null : null,
    distrito_id: rascunho.ambito === 'distrito' && rascunho.distrito ? Number(rascunho.distrito) : null,
  }), [rascunho.ambito, rascunho.provincia, rascunho.distrito])
  const destinoCompleto = rascunho.ambito === 'pais' || destino.provincia !== null || destino.distrito_id !== null

  const alcance = useQuery({
    queryKey: ['alcance', destino],
    queryFn: () => alertasRepo.alcance(destino.provincia, destino.distrito_id),
    enabled: aCompor && destinoCompleto,
    retry: false,
  })

  const enviar = useMutation({
    mutationFn: () => alertasRepo.criar({
      titulo: rascunho.titulo.trim(),
      mensagem: rascunho.mensagem.trim(),
      nivel: rascunho.nivel,
      patologia_id: rascunho.patologia ? Number(rascunho.patologia) : null,
      provincia_codigo: destino.provincia,
      distrito_id: destino.distrito_id,
      expira_em: rascunho.validade ? new Date(`${rascunho.validade}T23:59:59`).toISOString() : null,
    }),
    onSuccess: (a) => {
      notificar(`Alerta enviado a ${a.destinatarios} agricultor(es) — ${a.zona}`)
      setACompor(false)
      setRascunho(vazio())
      cliente.invalidateQueries({ queryKey: ['alertas'] })
      cliente.invalidateQueries({ queryKey: ['resumo'] })
    },
    onError: (e: Error) => notificar(e.message, 'erro'),
  })

  const arquivar = useMutation({
    mutationFn: alertasRepo.arquivar,
    onSuccess: () => {
      notificar('Alerta arquivado: deixa de aparecer na app')
      cliente.invalidateQueries({ queryKey: ['alertas'] })
    },
    onError: (e: Error) => notificar(e.message, 'erro'),
  })

  const alterar = <K extends keyof Rascunho>(k: K, v: Rascunho[K]) =>
    setRascunho((r) => ({ ...r, [k]: v, ...(k === 'provincia' && !tecnicoDistrito ? { distrito: '' } : {}) }))

  const valido = rascunho.titulo.trim().length >= 3 && rascunho.mensagem.trim().length >= 3 && destinoCompleto

  return {
    alertas: lista.data ?? [], aCarregar: lista.isLoading, erro: lista.error as Error | null,
    arquivados, setArquivados,
    aCompor, abrirComposicao: () => { setRascunho(vazio()); setACompor(true) }, fecharComposicao: () => setACompor(false),
    rascunho, alterar, ambitos, tecnicoDistrito, tecnicoProvincia,
    alcance: alcance.data, erroAlcance: alcance.error as Error | null, aCalcularAlcance: alcance.isFetching,
    valido, enviar: () => enviar.mutate(), aEnviar: enviar.isPending,
    arquivar: (id: number) => arquivar.mutate(id),
  }
}
