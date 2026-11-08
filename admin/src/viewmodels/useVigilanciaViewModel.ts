import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { vigilanciaRepo } from '@/model/repositorios'
import type { RiscoDistrito, Surto } from '@/model/tipos'
import { diasAtras } from '@/nucleo/formatos'
import { useNotificar } from '@/nucleo/notificacoes'
import { useSessao } from '@/nucleo/sessao'
import type { SerieSemanal, ValorDistrito } from '@/ui/graficos'
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
  const { podeOperar } = useSessao()
  const catalogo = useCatalogo()
  const navegar = useNavigate()
  const [sensibilidade, setSensibilidade] = useState<Sensibilidade>('normal')
  const [janela, setJanela] = useState(7)
  const [cultura, setCultura] = useState('')
  const [classe, setClasse] = useState('')
  const [periodo, setPeriodo] = useState(30)
  const [confianca, setConfianca] = useState<'' | 'alta' | 'baixa'>('')
  const [mostrarDescartados, setMostrarDescartados] = useState(false)
  const [aDescartar, setADescartar] = useState<Surto | null>(null)
  const cliente = useQueryClient()
  const notificar = useNotificar()

  const surtos = useQuery({
    queryKey: ['surtos', sensibilidade, janela],
    queryFn: () => vigilanciaRepo.surtos({ janela_dias: janela, ...PARAMETROS[sensibilidade] }),
  })
  const filtro = { cultura: cultura || undefined, classe: classe || undefined, desde: diasAtras(periodo), confianca: confianca || undefined }
  const ocorrencias = useQuery({ queryKey: ['ocorrencias', filtro], queryFn: () => vigilanciaRepo.ocorrencias(filtro) })
  // Tendência semana a semana (8 semanas), com os mesmos filtros, sem o período
  const filtroSemanas = { cultura: filtro.cultura, classe: filtro.classe, confianca: filtro.confianca, semanas: 8 }
  const semanas = useQuery({ queryKey: ['tendencia', filtroSemanas], queryFn: () => vigilanciaRepo.tendencia(filtroSemanas) })
  const tendencia = useMemo(() => {
    const lista = semanas.data ?? []
    // O gráfico recebe datas ISO e formata-as ele próprio (eixo e dica).
    const rotulos = lista.map((s) => s.semana)
    const serie = (chave: string, nome: string, cor: string, valor: (s: (typeof lista)[number]) => number): SerieSemanal => ({
      chave, nome, cor, valores: Object.fromEntries(lista.map((s, i) => [rotulos[i], valor(s)])),
    })
    return { semanas: rotulos, series: [serie('total', 'Diagnósticos', 'var(--serie-1)', (s) => s.total), serie('pragas', 'Pragas e doenças', 'var(--serie-2)', (s) => s.pragas_doencas)] }
  }, [semanas.data])
  // Declaração obrigatória e eficácia seguem o período, mas não a cultura/praga (são listas curtas).
  const declaracoes = useQuery({ queryKey: ['declaracoes', periodo], queryFn: () => vigilanciaRepo.declaracoes(diasAtras(periodo)) })
  const eficacia = useQuery({ queryKey: ['eficacia', periodo], queryFn: () => vigilanciaRepo.eficacia(diasAtras(periodo)) })

  // A previsão muda pouco: a API guarda-a 3 horas; aqui não se volta a pedir durante 10 minutos.
  const risco = useQuery({ queryKey: ['risco-meteorologico'], queryFn: vigilanciaRepo.riscoMeteorologico, staleTime: 600_000 })

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

  // Decisão do técnico sobre um sinal: confirmar (e seguir para o alerta) ou descartar (com nota).
  const decidir = useMutation({
    mutationFn: ({ s, decisao, nota }: { s: Surto; decisao: 'CONFIRMADO' | 'DESCARTADO'; nota: string | null }) =>
      vigilanciaRepo.decidirSurto({ distrito_id: s.distrito_id, cultura_id: s.cultura_id, classe: s.classe, decisao, nota }),
    onSuccess: (_, { s, decisao }) => {
      cliente.invalidateQueries({ queryKey: ['surtos'] })
      setADescartar(null)
      if (decisao === 'CONFIRMADO') criarAlerta(s)
      else notificar('Sinal descartado; fica registado na auditoria')
    },
    onError: (e: Error) => notificar(e.message, 'erro'),
  })
  const todosSurtos = surtos.data ?? []
  const descartados = todosSurtos.filter((s) => s.decisao === 'DESCARTADO').length

  /** Aviso preventivo: as condições do tempo favorecem a praga/doença (ainda não há casos). */
  const criarAlertaRisco = (r: RiscoDistrito) => {
    const p = catalogo.patologia(r.cultura_id, r.classe)
    const conselho = p?.prevencao || p?.recomendacao
    const preencher: Preenchimento = {
      titulo: `Tempo favorável a ${r.patologia_nome.toLowerCase()} em ${r.distrito}`,
      mensagem: `A previsão para os próximos dias (${r.motivo}) favorece ${r.patologia_nome.toLowerCase()} `
        + `nas plantas de ${catalogo.nomeCultura(r.cultura_id).toLowerCase()}. Vigie-as e, se vir sintomas, faça um diagnóstico na app.`
        + (conselho ? ` ${conselho}` : ''),
      nivel: r.nivel === 'ALTO' ? 'AVISO' : 'INFORMACAO',
      patologia_id: r.patologia_id,
      distrito_id: r.distrito_id,
      validade: r.ate, // o aviso vale até ao último dia da previsão (7 dias), não 14
    }
    navegar('/alertas', { state: { preencher } })
  }

  return {
    podeOperar,
    sensibilidade, setSensibilidade, janela, setJanela,
    surtos: mostrarDescartados ? todosSurtos : todosSurtos.filter((s) => s.decisao !== 'DESCARTADO'), aCarregarSurtos: surtos.isLoading,
    descartados, mostrarDescartados, setMostrarDescartados,
    confirmar: (s: Surto) => decidir.mutate({ s, decisao: 'CONFIRMADO', nota: null }),
    aDescartar, abrirDescarte: setADescartar, fecharDescarte: () => setADescartar(null),
    descartar: (nota: string) => aDescartar && decidir.mutate({ s: aDescartar, decisao: 'DESCARTADO', nota: nota.trim() || null }),
    aDecidir: decidir.isPending,
    confianca, setConfianca, tendencia, aCarregarTendencia: semanas.isLoading,
    risco: risco.data, aCarregarRisco: risco.isLoading, erroRisco: risco.error as Error | null, criarAlertaRisco,
    cultura, setCultura: (c: string) => { setCultura(c); setClasse('') }, classe, setClasse, periodo, setPeriodo,
    mapa, totalOcorrencias: mapa.reduce((s, v) => s + v.valor, 0), aCarregarMapa: ocorrencias.isLoading,
    ranking: (ocorrencias.data ?? []).slice(0, 10).map((o) => {
      const dif = o.ultimos_7d - o.anteriores_7d
      const seta = dif > 0 ? `▲ ${dif}` : dif < 0 ? `▼ ${-dif}` : '='
      return { chave: String(o.distrito_id), nome: `${o.distrito} · ${seta}`, valor: o.total,
        detalhe: `Últimos 7 dias: ${o.ultimos_7d}; 7 dias anteriores: ${o.anteriores_7d}` }
    }),
    criarAlerta, parametros: PARAMETROS[sensibilidade],
    declaracoes: declaracoes.data ?? [], aCarregarDeclaracoes: declaracoes.isLoading,
    confirmadas: (declaracoes.data ?? []).filter((d) => d.estado === 'CONFIRMADO').length,
    eficacia: eficacia.data ?? [], aCarregarEficacia: eficacia.isLoading,
  }
}
