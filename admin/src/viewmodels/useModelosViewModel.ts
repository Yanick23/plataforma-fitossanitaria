import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ErroApi } from '@/model/http'
import { modelosRepo } from '@/model/repositorios'
import type { EstadoModelo, Modelo } from '@/model/tipos'
import { useNotificar } from '@/nucleo/notificacoes'
import { useSessao } from '@/nucleo/sessao'
import { useCatalogo, useRegioes } from './referencias'

async function sha256(ficheiro: File): Promise<string> {
  const resumo = await crypto.subtle.digest('SHA-256', await ficheiro.arrayBuffer())
  return Array.from(new Uint8Array(resumo)).map((b) => b.toString(16).padStart(2, '0')).join('')
}

export type Distribuicao = 'todos' | 'piloto'

/** Cor fixa por versão (segue a entidade, não a posição): v1, v4… azul; v2, v5… laranja; v3, v6… verde. */
const CORES = ['var(--serie-1)', 'var(--serie-2)', 'var(--serie-3)']
export const corVersao = (versao: number) => CORES[(versao - 1) % CORES.length]

export function useModelosViewModel() {
  const { eAdministrador } = useSessao()
  const catalogo = useCatalogo()
  const regioes = useRegioes()
  const cliente = useQueryClient()
  const notificar = useNotificar()
  const [cultura, setCultura] = useState('')
  useEffect(() => {
    if (!cultura && catalogo.culturas.length) setCultura(catalogo.culturas[0].id)
  }, [cultura, catalogo.culturas])

  const historico = useQuery({
    queryKey: ['modelos', cultura], queryFn: () => modelosRepo.historico(cultura), enabled: Boolean(cultura),
  })
  const versoes = historico.data ?? []
  // A versão que a maioria usa: a publicada mais recente (as piloto só chegam aos seus distritos).
  const emUso = versoes.find((m) => m.estado === 'PUBLICADO')
  const pilotos = versoes.filter((m) => m.estado === 'PILOTO')
  const ultima = versoes[0]

  const monitorizacao = useQuery({
    queryKey: ['modelos', cultura, 'monitorizacao'], queryFn: () => modelosRepo.monitorizacao(cultura), enabled: Boolean(cultura),
  })
  const grafico = useMemo(() => {
    const m = monitorizacao.data
    if (!m) return null
    const semanas = [...new Set(m.semanas.map((s) => s.semana))].sort()
    const porVersao = new Map<number, typeof m.semanas>()
    m.semanas.forEach((s) => { if (s.versao !== null) porVersao.set(s.versao, [...(porVersao.get(s.versao) ?? []), s]) })
    const series = [...porVersao.entries()].sort(([a], [b]) => a - b).map(([versao, lista]) => ({
      chave: String(versao), nome: `v${versao}`, cor: corVersao(versao),
      valores: Object.fromEntries(lista.map((s) => [s.semana, s.taxa_baixa])),
      detalhe: Object.fromEntries(lista.map((s) => [s.semana, `${s.diagnosticos} diag.`])),
    }))
    return { semanas, series, total: m.semanas.reduce((t, s) => t + s.diagnosticos, 0) }
  }, [monitorizacao.data])
  const sinais = monitorizacao.data?.sinais ?? []

  const recarregar = () => cliente.invalidateQueries({ queryKey: ['modelos', cultura] })
  const aoErro = (e: Error) => notificar(e.message, 'erro')
  const nomesDistritos = (ids: number[]) => ids.map((id) => regioes.distrito(id)?.nome ?? `#${id}`)

  // --- Publicação ------------------------------------------------------------------------------
  const [aPublicar, setAPublicar] = useState(false)
  const [ficheiro, setFicheiro] = useState<File | null>(null)
  const [resumoLocal, setResumoLocal] = useState<string | null>(null)
  const [classes, setClasses] = useState('')
  const [acuracia, setAcuracia] = useState('')
  const [distribuicao, setDistribuicao] = useState<Distribuicao>('piloto')
  const [distritosPiloto, setDistritosPiloto] = useState<number[]>([])
  const [notas, setNotas] = useState('')

  useEffect(() => {
    setResumoLocal(null)
    if (ficheiro) sha256(ficheiro).then(setResumoLocal)
  }, [ficheiro])

  const abrirPublicacao = () => {
    setFicheiro(null)
    setAcuracia('')
    setNotas('')
    setDistritosPiloto([])
    // Com uma versão já em uso, o caminho seguro é o piloto; a primeira versão vai para todos.
    setDistribuicao(emUso ? 'piloto' : 'todos')
    setClasses((ultima?.classes ?? catalogo.patologiasDe(cultura).map((p) => p.codigo).sort()).join('\n'))
    setAPublicar(true)
  }

  const listaClasses = classes.split(/\s*\n\s*/).map((c) => c.trim()).filter(Boolean)
  const desconhecidas = listaClasses.filter((c) => !catalogo.patologia(cultura, c))
  const acuraciaNumero = acuracia.trim() ? Number(acuracia.replace(',', '.')) / 100 : null
  const acuraciaValida = acuraciaNumero === null || (acuraciaNumero >= 0 && acuraciaNumero <= 1)

  const publicar = useMutation({
    mutationFn: () => modelosRepo.publicar(cultura, ficheiro!, listaClasses, acuraciaNumero,
      distribuicao === 'piloto' ? distritosPiloto : [], notas),
    onSuccess: (m) => {
      const integro = resumoLocal === m.sha256
      const destino = m.estado === 'PILOTO' ? `em piloto em ${m.distritos_piloto.length === 1 ? "1 distrito" : `${m.distritos_piloto.length} distritos`}` : 'para todos os agricultores'
      notificar(integro
        ? `Versão ${m.versao} publicada ${destino} e verificada (SHA-256 igual).`
        : `Versão ${m.versao} publicada, mas o SHA-256 não coincide — publique de novo.`, integro ? 'sucesso' : 'erro')
      setAPublicar(false)
      recarregar()
    },
    onError: aoErro,
  })

  // --- Uma versão aberta: estado, distritos do piloto, porta de qualidade ----------------------
  const [abertaVersao, setAbertaVersao] = useState<number | null>(null)
  const aberta = versoes.find((m) => m.versao === abertaVersao) ?? null
  const [distritosEdicao, setDistritosEdicao] = useState<number[]>([])
  const [notasEdicao, setNotasEdicao] = useState('')
  const [bloqueio, setBloqueio] = useState<string | null>(null) // motivo da porta, quando a promoção foi recusada

  const abrir = (m: Modelo) => {
    setAbertaVersao(m.versao)
    setDistritosEdicao(m.distritos_piloto)
    setNotasEdicao(m.notas ?? '')
    setBloqueio(null)
  }
  const porta = useQuery({
    queryKey: ['modelos', cultura, aberta?.versao, 'porta'],
    queryFn: () => modelosRepo.portaQualidade(cultura, aberta!.versao),
    enabled: aberta?.estado === 'PILOTO',
  })

  const actualizar = useMutation({
    mutationFn: (alt: { estado?: EstadoModelo; distritos_piloto?: number[]; notas?: string | null; forcar?: boolean }) =>
      modelosRepo.actualizar(cultura, aberta!.versao, alt),
    onSuccess: (m, alt) => {
      setBloqueio(null)
      const mensagens: Record<EstadoModelo, string> = {
        PUBLICADO: `v${m.versao} publicada para todos os agricultores${alt.forcar ? ' (forçado; fica na auditoria)' : ''}`,
        PILOTO: `v${m.versao} em piloto`,
        RETIRADO: `v${m.versao} retirada; as apps voltam à versão anterior na próxima sincronização`,
      }
      notificar(alt.estado ? mensagens[m.estado] : 'Alterações guardadas')
      recarregar()
    },
    onError: (e: Error, alt) => {
      if (e instanceof ErroApi && e.estado === 409 && alt.estado === 'PUBLICADO') setBloqueio(e.mensagem)
      else aoErro(e)
    },
  })

  const pilotoAlterado = Boolean(aberta && (
    [...distritosEdicao].sort().join() !== [...aberta.distritos_piloto].sort().join() || notasEdicao.trim() !== (aberta.notas ?? '')))

  return {
    eAdministrador, culturas: catalogo.culturas, nomeCultura: catalogo.nomeCultura, nomeClasse: catalogo.nomeClasse,
    cultura, setCultura: (c: string) => { setCultura(c); setAbertaVersao(null) },
    versoes, emUso, pilotos, ultima, aCarregar: historico.isLoading, erro: historico.error as Error | null, nomesDistritos,
    grafico, sinais, aCarregarMonitorizacao: monitorizacao.isLoading,
    aPublicar, abrirPublicacao, fecharPublicacao: () => setAPublicar(false),
    ficheiro, setFicheiro, resumoLocal, classes, setClasses, listaClasses, desconhecidas, acuracia, setAcuracia, acuraciaValida,
    distribuicao, setDistribuicao, distritosPiloto, setDistritosPiloto, notas, setNotas,
    podePublicar: Boolean(ficheiro && ficheiro.name.endsWith('.tflite') && listaClasses.length >= 2 && acuraciaValida && resumoLocal
      && (distribuicao === 'todos' || distritosPiloto.length > 0)),
    publicar: () => publicar.mutate(), aEnviar: publicar.isPending,
    aberta, abrir, fechar: () => setAbertaVersao(null),
    porta: porta.data, aCarregarPorta: porta.isLoading, bloqueio,
    distritosEdicao, setDistritosEdicao, notasEdicao, setNotasEdicao, pilotoAlterado,
    guardarPiloto: () => actualizar.mutate({ distritos_piloto: distritosEdicao, notas: notasEdicao }),
    promover: (forcar = false) => actualizar.mutate({ estado: 'PUBLICADO', forcar }),
    retirar: () => actualizar.mutate({ estado: 'RETIRADO' }),
    reporPiloto: () => actualizar.mutate({ estado: 'PILOTO' }),
    aActualizar: actualizar.isPending,
  }
}
