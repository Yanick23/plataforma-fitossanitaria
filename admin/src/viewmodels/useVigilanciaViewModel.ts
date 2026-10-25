import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { vigilanciaRepo } from '@/model/repositorios'
import type { Surto } from '@/model/tipos'
import { diasAtras } from '@/nucleo/formatos'
import type { ValorDistrito } from '@/ui/graficos'
import type { Preenchimento } from './useAlertasViewModel'
import { useCatalogo } from './referencias'

export type Sensibilidade = 'alta' | 'normal' | 'baixa'

/** Parâmetros da regra de surto (ver api/app/servicos/vigilancia.py). */
const PARAMETROS: Record<Sensibilidade, { min_casos: number; factor: number }> = {
  alta: { min_casos: 2, factor: 1.5 },
  normal: { min_casos: 3, factor: 2 },
  baixa: { min_casos: 5, factor: 3 },
}

export function useVigilanciaViewModel() {
  const catalogo = useCatalogo()
  const navegar = useNavigate()
  const [sensibilidade, setSensibilidade] = useState<Sensibilidade>('normal')
  const [janela, setJanela] = useState(7)
  const [cultura, setCultura] = useState('')
  const [classe, setClasse] = useState('')
  const [periodo, setPeriodo] = useState(30)

  const surtos = useQuery({
    queryKey: ['surtos', sensibilidade, janela],
    queryFn: () => vigilanciaRepo.surtos({ janela_dias: janela, ...PARAMETROS[sensibilidade] }),
  })
  const filtro = { cultura: cultura || undefined, classe: classe || undefined, desde: diasAtras(periodo) }
  const ocorrencias = useQuery({ queryKey: ['ocorrencias', filtro], queryFn: () => vigilanciaRepo.ocorrencias(filtro) })

  const mapa: ValorDistrito[] = useMemo(() => (ocorrencias.data ?? []).map((o) => ({
    distrito: o.distrito, provincia_codigo: o.provincia_codigo, valor: o.total,
  })), [ocorrencias.data])

  const criarAlerta = (s: Surto) => {
    const p = catalogo.patologia(s.cultura_id, s.classe)
    const preencher: Preenchimento = {
      titulo: `${s.patologia_nome} em ${s.distrito}`,
      mensagem: `Nos últimos ${janela} dias houve ${s.casos_recentes} diagnósticos de ${s.patologia_nome.toLowerCase()} `
        + `(${catalogo.nomeCultura(s.cultura_id).toLowerCase()}) no distrito de ${s.distrito}, acima do habitual. `
        + `Inspeccione a sua machamba.${p?.recomendacao ? ` ${p.recomendacao}` : ''}`,
      nivel: s.nivel,
      patologia_id: p?.id,
      distrito_id: s.distrito_id,
    }
    navegar('/alertas', { state: { preencher } })
  }

  return {
    sensibilidade, setSensibilidade, janela, setJanela,
    surtos: surtos.data ?? [], aCarregarSurtos: surtos.isLoading,
    cultura, setCultura: (c: string) => { setCultura(c); setClasse('') }, classe, setClasse, periodo, setPeriodo,
    mapa, totalOcorrencias: mapa.reduce((s, v) => s + v.valor, 0), aCarregarMapa: ocorrencias.isLoading,
    ranking: (ocorrencias.data ?? []).slice(0, 10).map((o) => ({ chave: String(o.distrito_id), nome: o.distrito, valor: o.total })),
    criarAlerta, parametros: PARAMETROS[sensibilidade],
  }
}
