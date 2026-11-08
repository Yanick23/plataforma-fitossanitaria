import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { URL_API } from '@/model/http'
import { audiosRepo } from '@/model/repositorios'
import type { Audio, Lingua } from '@/model/tipos'
import { useNotificar } from '@/nucleo/notificacoes'
import { useSessao } from '@/nucleo/sessao'
import type { AudioGravado } from '@/ui/Gravador'
import { useCatalogo } from './referencias'

/** As línguas mudam só com uma versão nova da API. */
export function useLinguas() {
  const q = useQuery({ queryKey: ['linguas'], queryFn: audiosRepo.linguas, staleTime: Infinity })
  const linguas: Lingua[] = q.data ?? []
  return { linguas, nomeLingua: (c: string) => linguas.find((l) => l.codigo === c)?.nome ?? c }
}

/** Ficheiros públicos: o <audio> do painel toca-os sem o token. */
export const urlAudio = (a: Audio) => `${URL_API}${a.url}`

/** Gravações de uma praga ou doença do catálogo: gravar, ouvir, validar (outra pessoa) e apagar. */
export function useAudiosPatologia(patologiaId: number | null) {
  const { utilizador, podeOperar } = useSessao()
  const { linguas } = useLinguas()
  const cliente = useQueryClient()
  const notificar = useNotificar()
  const [lingua, setLingua] = useState('')
  const [gravacao, setGravacao] = useState<AudioGravado | null>(null)

  const chave = ['audios', patologiaId]
  const lista = useQuery({ queryKey: chave, queryFn: () => audiosRepo.daPatologia(patologiaId!), enabled: patologiaId !== null })
  const audios = lista.data ?? []
  const actualizar = () => {
    cliente.invalidateQueries({ queryKey: chave })
    cliente.invalidateQueries({ queryKey: ['patologias'] }) // a app só recebe as validadas
    cliente.invalidateQueries({ queryKey: ['cobertura-audio'] })
  }
  const aoErro = (e: Error) => notificar(e.message, 'erro')

  const guardar = useMutation({
    mutationFn: () => audiosRepo.gravar({ patologia_id: patologiaId! }, { blob: gravacao!.blob, lingua, duracao_s: gravacao!.duracao_s }),
    onSuccess: (a) => {
      notificar(`Gravação em ${a.lingua_nome} guardada. Falta outra pessoa da equipa validá-la.`)
      setGravacao(null)
      setLingua('')
      actualizar()
    },
    onError: aoErro,
  })
  const validar = useMutation({
    mutationFn: audiosRepo.validar,
    onSuccess: (a) => { notificar(`Gravação em ${a.lingua_nome} validada: chega à app na próxima sincronização`); actualizar() },
    onError: aoErro,
  })
  const apagar = useMutation({
    mutationFn: audiosRepo.apagar,
    onSuccess: () => { notificar('Gravação apagada'); actualizar() },
    onError: aoErro,
  })

  const substitui = audios.find((a) => a.lingua === lingua) ?? null
  return {
    audios, aCarregar: lista.isLoading, linguas, podeGravar: podeOperar,
    lingua, setLingua, gravacao, setGravacao, substitui,
    /** Quem gravou não valida: outra pessoa confirma que diz o mesmo que o texto. */
    podeValidar: (a: Audio) => podeOperar && !a.validado_em && a.autor_id !== utilizador?.id,
    guardar: () => gravacao && lingua && guardar.mutate(), aGuardar: guardar.isPending,
    validar: (id: number) => validar.mutate(id), aValidar: validar.isPending,
    apagar: (id: number) => apagar.mutate(id),
  }
}

/** Quadro: que pragas já têm voz em cada língua, e que línguas escolheram os agricultores da zona. */
export function useCoberturaAudio() {
  const catalogo = useCatalogo()
  const q = useQuery({ queryKey: ['cobertura-audio'], queryFn: audiosRepo.cobertura })
  const [cultura, setCultura] = useState('')
  const c = q.data

  // Colunas: o português e as línguas que os agricultores escolheram ou que já têm gravações,
  // pela ordem de quantos agricultores as escolheram.
  const colunas = useMemo(() => {
    if (!c) return []
    const comAudio = new Set(c.patologias.flatMap((p) => Object.keys(p.audios)))
    return c.linguas
      .filter((l) => l.codigo === 'por' || comAudio.has(l.codigo) || (c.agricultores_por_lingua[l.codigo] ?? 0) > 0)
      .sort((a, b) => (a.codigo === 'por' ? -1 : b.codigo === 'por' ? 1
        : (c.agricultores_por_lingua[b.codigo] ?? 0) - (c.agricultores_por_lingua[a.codigo] ?? 0)))
  }, [c])

  const linhas = (c?.patologias ?? []).filter((p) => !cultura || p.cultura_id === cultura)
  const totalAgricultores = c ? Object.values(c.agricultores_por_lingua).reduce((s, n) => s + n, 0) + c.agricultores_sem_lingua : 0
  const preferencias = c ? c.linguas
    .map((l) => ({ chave: l.codigo, nome: l.nome, valor: c.agricultores_por_lingua[l.codigo] ?? 0 }))
    .filter((x) => x.valor > 0)
    .sort((a, b) => b.valor - a.valor) : []
  /** Por língua: quantas pragas já têm gravação validada (a app só recebe essas). */
  const prontas = (codigo: string) => (c?.patologias ?? []).filter((p) => p.audios[codigo]?.validado).length

  return {
    aCarregar: q.isLoading, erro: q.error as Error | null, cobertura: c, colunas, linhas, preferencias, prontas,
    totalAgricultores, culturas: catalogo.culturas, nomeCultura: catalogo.nomeCultura, cultura, setCultura,
  }
}
