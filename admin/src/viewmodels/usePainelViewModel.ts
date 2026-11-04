import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { diagnosticosRepo, painelRepo, vigilanciaRepo } from '@/model/repositorios'
import type { ValorDistrito } from '@/ui/graficos'
import { numero } from '@/nucleo/formatos'

export type Periodo = 7 | 30 | 90

export function usePainelViewModel() {
  const [periodo, setPeriodo] = useState<Periodo>(30)
  const resumo = useQuery({ queryKey: ['resumo', periodo], queryFn: () => painelRepo.resumo(periodo) })
  const surtos = useQuery({ queryKey: ['surtos'], queryFn: () => vigilanciaRepo.surtos() })
  const porValidar = useQuery({
    queryKey: ['diagnosticos', 'fila-painel'],
    queryFn: () => diagnosticosRepo.listar({ ordem: 'confianca', validacao: 'PENDENTE', limite: 5 }),
  })

  const derivados = useMemo(() => {
    const r = resumo.data
    if (!r) return null
    const anterior = r.diagnosticos_30d_anteriores
    const variacao = anterior > 0 ? (r.diagnosticos_30d - anterior) / anterior : null
    const mapa: ValorDistrito[] = r.por_distrito.map((d) => ({
      distrito: d.distrito,
      provincia_codigo: d.provincia_codigo,
      valor: d.pragas_doencas,
      detalhe: [
        { nome: 'Todos os diagnósticos', valor: numero(d.total) },
        { nome: 'Agricultores registados', valor: numero(d.agricultores) },
      ],
    }))
    const ranking = r.por_classe
      .filter((c) => !c.chave.endsWith(':saudavel'))
      .slice(0, 7)
      .map((c) => ({ chave: c.chave, nome: c.nome, valor: c.total }))
    const taxaBaixa = r.diagnosticos_30d ? r.confianca_baixa_30d / r.diagnosticos_30d : null
    return { variacao, mapa, ranking, taxaBaixa, distritosComCasos: r.por_distrito.filter((d) => d.pragas_doencas > 0).length }
  }, [resumo.data])

  return {
    periodo,
    setPeriodo,
    resumo: resumo.data,
    aCarregar: resumo.isLoading,
    erro: resumo.error as Error | null,
    derivados,
    surtos: surtos.data ?? [],
    porValidar: porValidar.data?.itens ?? [],
    totalPorValidar: porValidar.data?.total ?? 0,
  }
}
