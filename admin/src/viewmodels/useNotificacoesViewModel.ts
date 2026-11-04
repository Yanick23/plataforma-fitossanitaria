import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { notificacoesRepo } from '@/model/repositorios'
import { useNotificar } from '@/nucleo/notificacoes'
import { useSessao } from '@/nucleo/sessao'

/** Avisos da equipa (casos confirmados de declaração obrigatória). Actualiza a cada minuto. */
export function useNotificacoesViewModel() {
  const { podeOperar } = useSessao()
  const cliente = useQueryClient()
  const notificar = useNotificar()
  const lista = useQuery({
    queryKey: ['notificacoes'], queryFn: notificacoesRepo.listar, enabled: podeOperar, refetchInterval: 60_000,
  })
  const actualizar = () => cliente.invalidateQueries({ queryKey: ['notificacoes'] })
  const aoErro = (e: Error) => notificar(e.message, 'erro')

  const lida = useMutation({ mutationFn: notificacoesRepo.marcarLida, onSuccess: actualizar, onError: aoErro })
  const todas = useMutation({ mutationFn: notificacoesRepo.marcarTodas, onSuccess: actualizar, onError: aoErro })

  return {
    disponivel: podeOperar,
    itens: lista.data?.itens ?? [],
    naoLidas: lista.data?.nao_lidas ?? 0,
    aCarregar: lista.isLoading,
    marcarLida: (id: number) => lida.mutate(id),
    marcarTodas: () => todas.mutate(),
  }
}
