import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { urlProtegido } from '@/model/http'
import { diagnosticosRepo, validacoesRepo } from '@/model/repositorios'
import type { Diagnostico } from '@/model/tipos'
import { useNotificar } from '@/nucleo/notificacoes'
import { useSessao } from '@/nucleo/sessao'

export function useValidacaoViewModel() {
  const { eAdministrador } = useSessao()
  const cliente = useQueryClient()
  const notificar = useNotificar()
  const [cultura, setCultura] = useState('')
  const [aberto, setAberto] = useState<Diagnostico | null>(null)
  const [aExportar, setAExportar] = useState(false)

  const fila = useQuery({
    queryKey: ['diagnosticos', 'fila', cultura],
    queryFn: () => diagnosticosRepo.listar({ validacao: 'PENDENTE', ordem: 'confianca', cultura: cultura || undefined, limite: 20 }),
  })
  const exactidao = useQuery({ queryKey: ['exactidao', cultura], queryFn: () => validacoesRepo.exactidao(cultura || undefined) })

  const validar = useMutation({
    mutationFn: (v: { id: string; classe: string; nota: string }) => diagnosticosRepo.validar(v.id, v.classe, v.nota.trim() || null),
    onSuccess: (d) => {
      notificar(d.validacao === 'CONFIRMADO' ? 'Confirmado' : 'Correcção registada')
      cliente.invalidateQueries({ queryKey: ['diagnosticos'] })
      cliente.invalidateQueries({ queryKey: ['exactidao'] })
      // Passa logo ao seguinte da fila, para validar em sequência.
      const itens = fila.data?.itens ?? []
      const i = itens.findIndex((x) => x.id === d.id)
      setAberto(itens[i + 1] ?? null)
    },
    onError: (e: Error) => notificar(e.message, 'erro'),
  })

  const exportar = async () => {
    setAExportar(true)
    try {
      const url = await urlProtegido(validacoesRepo.caminhoExportar)
      const a = document.createElement('a')
      a.href = url
      a.download = `validados_${new Date().toISOString().slice(0, 10)}.zip`
      a.click()
      setTimeout(() => URL.revokeObjectURL(url), 5000)
    } catch (e) {
      notificar((e as Error).message, 'erro')
    } finally {
      setAExportar(false)
    }
  }

  const e = exactidao.data
  const correccoes = e ? e.validados - e.correctos : 0
  return {
    eAdministrador, cultura, setCultura,
    fila: fila.data?.itens ?? [], totalFila: fila.data?.total ?? 0, aCarregarFila: fila.isLoading,
    exactidao: e, aCarregarExactidao: exactidao.isLoading, correccoes,
    aberto, abrir: setAberto, fechar: () => setAberto(null),
    validar: (id: string, classe: string, nota: string) => validar.mutate({ id, classe, nota }), aValidar: validar.isPending,
    exportar, aExportar,
  }
}
