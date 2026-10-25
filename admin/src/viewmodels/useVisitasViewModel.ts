import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { visitasRepo } from '@/model/repositorios'
import type { EstadoVisita, Visita } from '@/model/tipos'
import { useNotificar } from '@/nucleo/notificacoes'

export type Separador = EstadoVisita | 'TODAS'

/** Valor para <input type="datetime-local"> na hora local. */
function localParaCampo(iso: string | null): string {
  const d = iso ? new Date(iso) : new Date(Date.now() + 24 * 3600 * 1000)
  if (!iso) d.setHours(9, 0, 0, 0)
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}

export function useVisitasViewModel() {
  const cliente = useQueryClient()
  const notificar = useNotificar()
  const [separador, setSeparador] = useState<Separador>('PENDENTE')
  const [aberta, setAberta] = useState<Visita | null>(null)
  const [quando, setQuando] = useState('')
  const [notas, setNotas] = useState('')

  const lista = useQuery({
    queryKey: ['visitas', separador],
    queryFn: () => visitasRepo.listar(separador === 'TODAS' ? undefined : separador),
  })
  const contagem = useQuery({ queryKey: ['visitas', 'TODAS'], queryFn: () => visitasRepo.listar() })
  const porEstado = (e: EstadoVisita) => (contagem.data ?? []).filter((v) => v.estado === e).length

  useEffect(() => {
    if (!aberta) return
    setQuando(localParaCampo(aberta.data_agendada))
    setNotas(aberta.notas_tecnico ?? '')
  }, [aberta])

  const actualizar = useMutation({
    mutationFn: (alteracoes: { estado?: EstadoVisita; data_agendada?: string | null; notas_tecnico?: string | null }) =>
      visitasRepo.actualizar(aberta!.id, alteracoes),
    onSuccess: (v) => {
      notificar({ AGENDADA: 'Visita agendada', RESOLVIDA: 'Visita resolvida', CANCELADA: 'Pedido cancelado', PENDENTE: 'Guardado' }[v.estado])
      setAberta(null)
      cliente.invalidateQueries({ queryKey: ['visitas'] })
    },
    onError: (e: Error) => notificar(e.message, 'erro'),
  })

  const notasLimpas = () => notas.trim() || null
  return {
    separador, setSeparador, porEstado,
    visitas: lista.data ?? [], aCarregar: lista.isLoading, erro: lista.error as Error | null,
    aberta, abrir: setAberta, fechar: () => setAberta(null),
    quando, setQuando, notas, setNotas,
    agendar: () => actualizar.mutate({ estado: 'AGENDADA', data_agendada: new Date(quando).toISOString(), notas_tecnico: notasLimpas() }),
    resolver: () => actualizar.mutate({ estado: 'RESOLVIDA', notas_tecnico: notasLimpas() }),
    cancelar: () => actualizar.mutate({ estado: 'CANCELADA', notas_tecnico: notasLimpas() }),
    guardarNotas: () => actualizar.mutate({ notas_tecnico: notasLimpas() }),
    aGuardar: actualizar.isPending,
  }
}
