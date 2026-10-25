import { useEffect, useMemo, useState } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { urlProtegido } from '@/model/http'
import { boletimRepo, type PeriodoBoletim } from '@/model/repositorios'
import type { Boletim } from '@/model/tipos'
import { numero, percentagem } from '@/nucleo/formatos'
import { useNotificar } from '@/nucleo/notificacoes'

export type Predefinido = '7' | '30' | '90' | 'mes' | 'outro'

/** Data local (não UTC) no formato AAAA-MM-DD. */
const diaLocal = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

function periodoDe(p: Exclude<Predefinido, 'outro'>): PeriodoBoletim {
  const hoje = new Date()
  if (p === 'mes') { // o mês civil anterior, o período habitual de um boletim
    return { inicio: diaLocal(new Date(hoje.getFullYear(), hoje.getMonth() - 1, 1)), fim: diaLocal(new Date(hoje.getFullYear(), hoje.getMonth(), 0)) }
  }
  const inicio = new Date(hoje)
  inicio.setDate(hoje.getDate() - Number(p) + 1)
  return { inicio: diaLocal(inicio), fim: diaLocal(hoje) }
}

/** «1 alerta», «3 alertas». */
const n = (valor: number, singular: string, plural: string) => `${numero(valor)} ${valor === 1 ? singular : plural}`

/** Parágrafos de síntese escritos a partir dos números (o que um técnico escreveria no topo do boletim). */
function sintese(b: Boletim): string[] {
  if (b.diagnosticos === 0) return ['Não houve diagnósticos sincronizados nesta zona durante o período.']
  const frases: string[] = []
  const parte = b.diagnosticos_pragas_doencas / b.diagnosticos
  frases.push(`No período houve ${n(b.diagnosticos, 'diagnóstico', 'diagnósticos')}, feitos por `
    + `${n(b.agricultores_activos, 'agricultor', 'agricultores')}; ${numero(b.diagnosticos_pragas_doencas)} `
    + `(${percentagem(parte)}) identificaram uma praga ou doença.`)
  const [primeira] = b.principais_pragas
  const [distrito] = b.distritos_mais_afectados
  if (primeira) {
    frases.push(`A ocorrência mais frequente foi ${primeira.nome}, com ${n(primeira.valor, 'caso', 'casos')}`
      + (distrito ? `; o distrito com mais casos foi ${distrito.nome} (${numero(distrito.valor)}).` : '.'))
  }
  const urgentes = b.surtos.filter((s) => s.nivel === 'URGENTE').length
  if (b.surtos.length) {
    frases.push(`${b.surtos.length === 1 ? 'Foi detectado 1 sinal' : `Foram detectados ${numero(b.surtos.length)} sinais`} de surto`
      + `${urgentes ? ` (${numero(urgentes)} de nível urgente)` : ''}.`)
  }
  if (b.declaracoes.length) {
    const confirmadas = b.declaracoes.filter((d) => d.estado === 'CONFIRMADO').length
    frases.push(`Há ${n(b.declaracoes.length, 'caso', 'casos')} de declaração obrigatória, `
      + `${n(confirmadas, 'confirmado', 'confirmados')} pelo técnico.`)
  }
  frases.push(`Alertas emitidos: ${numero(b.alertas_enviados)}. Visitas técnicas pedidas: ${numero(b.visitas_pedidas)}`
    + (b.visitas_pedidas ? `, ${n(b.visitas_resolvidas, 'resolvida', 'resolvidas')}.` : '.'))
  return frases
}

export function useBoletimViewModel() {
  const notificar = useNotificar()
  const [predefinido, setPredefinido] = useState<Predefinido>('30')
  const [periodo, setPeriodo] = useState<PeriodoBoletim>(() => periodoDe('30'))
  const [aDescarregar, setADescarregar] = useState(false)

  const escolher = (p: Predefinido) => {
    setPredefinido(p)
    if (p !== 'outro') setPeriodo(periodoDe(p))
  }
  const mudarData = (campo: keyof PeriodoBoletim, valor: string) => {
    setPredefinido('outro')
    setPeriodo((actual) => ({ ...actual, [campo]: valor }))
  }
  const invalido = !periodo.inicio || !periodo.fim || periodo.inicio > periodo.fim

  const consulta = useQuery({
    queryKey: ['boletim', periodo],
    queryFn: () => boletimRepo.obter(periodo),
    enabled: !invalido,
    placeholderData: keepPreviousData,
  })
  const boletim = consulta.data
  const paragrafos = useMemo(() => (boletim ? sintese(boletim) : []), [boletim])

  // O nome do PDF guardado vem do título do documento.
  useEffect(() => {
    if (!boletim) return
    const anterior = document.title
    document.title = `Boletim fitossanitário — ${boletim.zona} — ${periodo.inicio} a ${periodo.fim}`
    return () => { document.title = anterior }
  }, [boletim, periodo])

  const descarregarCsv = async () => {
    setADescarregar(true)
    try {
      const url = await urlProtegido(boletimRepo.caminhoCsv(periodo))
      const a = document.createElement('a')
      a.href = url
      a.download = `boletim_${periodo.inicio}_${periodo.fim}.csv`
      a.click()
      setTimeout(() => URL.revokeObjectURL(url), 5000)
    } catch (e) {
      notificar((e as Error).message, 'erro')
    } finally {
      setADescarregar(false)
    }
  }

  return {
    predefinido, escolher, periodo, mudarData, invalido,
    boletim, paragrafos, aCarregar: consulta.isLoading, aActualizar: consulta.isFetching,
    erro: consulta.error as Error | null,
    imprimir: () => window.print(), descarregarCsv, aDescarregar,
  }
}
