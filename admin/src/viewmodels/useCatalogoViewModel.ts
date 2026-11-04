import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { URL_API } from '@/model/http'
import { catalogoRepo } from '@/model/repositorios'
import type { Cultura, FotoReferencia, Patologia, PatologiaEscrita, TipoPatologia } from '@/model/tipos'
import { useNotificar } from '@/nucleo/notificacoes'
import { useSessao } from '@/nucleo/sessao'
import { useCatalogo } from './referencias'

export interface RascunhoPatologia {
  id: number | null
  cultura_id: string
  codigo: string
  nome_local: string
  nome_cientifico: string
  tipo: TipoPatologia
  recomendacao: string
  sintomas: string
  prevencao: string
  declaracao_obrigatoria: boolean
}

/** Os textos que o agricultor lê: mudá-los sobe a versão e retira a validação (regra da API). */
const CAMPOS_TEXTO = ['nome_local', 'nome_cientifico', 'recomendacao', 'sintomas', 'prevencao'] as const

export type FiltroRevisao = '' | 'por_validar' | 'declaracao'

const rascunhoDe = (p: Patologia): RascunhoPatologia => ({
  id: p.id, cultura_id: p.cultura_id, codigo: p.codigo, nome_local: p.nome_local, nome_cientifico: p.nome_cientifico,
  tipo: p.tipo, recomendacao: p.recomendacao, sintomas: p.sintomas ?? '', prevencao: p.prevencao ?? '',
  declaracao_obrigatoria: p.declaracao_obrigatoria,
})

const paraEnviar = (r: RascunhoPatologia): PatologiaEscrita => ({
  cultura_id: r.cultura_id, codigo: r.codigo, nome_local: r.nome_local.trim(), nome_cientifico: r.nome_cientifico.trim(),
  tipo: r.tipo, recomendacao: r.recomendacao.trim(), sintomas: r.sintomas.trim() || null, prevencao: r.prevencao.trim() || null,
  declaracao_obrigatoria: r.declaracao_obrigatoria,
})

export const conteudoValidado = (p: Patologia) => Boolean(p.validado_por_nome)

export function useCatalogoViewModel() {
  const { eAdministrador } = useSessao()
  const catalogo = useCatalogo()
  const cliente = useQueryClient()
  const notificar = useNotificar()
  const [cultura, setCultura] = useState('')
  const [edicao, setEdicao] = useState<RascunhoPatologia | null>(null)
  const [novaCultura, setNovaCultura] = useState<Cultura | null>(null)
  const [pesquisa, setPesquisa] = useState('')
  const [filtro, setFiltro] = useState<FiltroRevisao>('')

  useEffect(() => {
    if (!cultura && catalogo.culturas.length) setCultura(catalogo.culturas[0].id)
  }, [cultura, catalogo.culturas])

  // A versão guardada da praga aberta (fotos, validação), sempre a do servidor.
  const guardada = edicao?.id ? catalogo.patologias.find((p) => p.id === edicao.id) ?? null : null

  /** Actualiza a cache com a resposta da API (evita esperar por um novo pedido). */
  const substituir = (p: Patologia) => {
    cliente.setQueryData<Patologia[]>(['patologias'], (lista) => lista?.map((x) => (x.id === p.id ? p : x)))
  }
  const recarregar = () => {
    cliente.invalidateQueries({ queryKey: ['patologias'] })
    cliente.invalidateQueries({ queryKey: ['culturas'] })
  }
  const aoErro = (e: Error) => notificar(e.message, 'erro')

  const textoAlterado = Boolean(guardada && edicao && CAMPOS_TEXTO.some((c) => (guardada[c] ?? '').trim() !== edicao[c].trim()))
  const porGuardar = Boolean(guardada && edicao && (textoAlterado || guardada.tipo !== edicao.tipo
    || guardada.declaracao_obrigatoria !== edicao.declaracao_obrigatoria))

  const guardar = useMutation({
    mutationFn: (r: RascunhoPatologia) => (r.id === null
      ? catalogoRepo.criarPatologia(paraEnviar(r))
      : catalogoRepo.actualizarPatologia(r.id, paraEnviar(r))),
    onSuccess: (p, r) => {
      if (r.id === null) {
        notificar('Praga/doença criada. Junte fotografias e peça a um técnico que valide o texto.')
        recarregar()
        setEdicao(rascunhoDe(p))
      } else {
        notificar(conteudoValidado(p) ? 'Alterações guardadas' : `Guardado (versão ${p.versao_conteudo}); o texto fica por validar`)
        substituir(p)
        setEdicao(rascunhoDe(p))
      }
    },
    onError: aoErro,
  })
  const apagar = useMutation({
    mutationFn: (id: number) => catalogoRepo.apagarPatologia(id),
    onSuccess: () => { notificar('Praga/doença apagada'); setEdicao(null); recarregar() },
    onError: aoErro,
  })
  const validar = useMutation({
    mutationFn: (id: number) => catalogoRepo.validarConteudo(id),
    onSuccess: (p) => { notificar(`Conteúdo validado (versão ${p.versao_conteudo})`); substituir(p) },
    onError: aoErro,
  })
  const enviarFoto = useMutation({
    mutationFn: ({ id, ficheiro, legenda }: { id: number; ficheiro: File; legenda: string }) => catalogoRepo.enviarFoto(id, ficheiro, legenda),
    onSuccess: (p) => { notificar('Fotografia acrescentada'); substituir(p) },
    onError: aoErro,
  })
  const apagarFoto = useMutation({
    mutationFn: (fotoId: number) => catalogoRepo.apagarFoto(fotoId),
    onSuccess: () => { notificar('Fotografia removida'); cliente.invalidateQueries({ queryKey: ['patologias'] }) },
    onError: aoErro,
  })
  const criarCultura = useMutation({
    mutationFn: (c: Cultura) => catalogoRepo.criarCultura(c),
    onSuccess: (c) => { notificar(`Cultura «${c.nome}» criada`); setNovaCultura(null); setCultura(c.id); recarregar() },
    onError: aoErro,
  })

  const termo = pesquisa.trim().toLowerCase()
  const daCultura = catalogo.patologiasDe(cultura)
  const patologias = daCultura.filter((p) =>
    (!termo || [p.nome_local, p.nome_cientifico, p.codigo, p.recomendacao, p.sintomas ?? ''].some((t) => t.toLowerCase().includes(termo)))
    && (filtro !== 'por_validar' || !conteudoValidado(p))
    && (filtro !== 'declaracao' || p.declaracao_obrigatoria))
  const porValidar = daCultura.filter((p) => !conteudoValidado(p)).length
  /** O que falta a uma praga para o agricultor ter informação completa. */
  const emFalta = (p: Patologia) => [
    p.recomendacao.trim().length < 20 && 'recomendação',
    p.tipo !== 'SAUDAVEL' && !p.sintomas?.trim() && 'sintomas',
    p.tipo !== 'SAUDAVEL' && !p.prevencao?.trim() && 'prevenção',
    p.fotos.length === 0 && 'fotografias',
  ].filter(Boolean) as string[]

  return {
    eAdministrador, culturas: catalogo.culturas, aCarregar: catalogo.aCarregar, nomeCultura: catalogo.nomeCultura,
    cultura, setCultura, pesquisa, setPesquisa, filtro, setFiltro, patologias, porValidar, total: daCultura.length, emFalta,
    edicao, guardada, textoAlterado, porGuardar,
    editar: (p: Patologia) => setEdicao(rascunhoDe(p)),
    nova: () => setEdicao({
      id: null, cultura_id: cultura, codigo: '', nome_local: '', nome_cientifico: '', tipo: 'DOENCA', recomendacao: '',
      sintomas: '', prevencao: '', declaracao_obrigatoria: false,
    }),
    alterar: <K extends keyof RascunhoPatologia>(k: K, v: RascunhoPatologia[K]) => setEdicao((e) => (e ? { ...e, [k]: v } : e)),
    fecharEdicao: () => setEdicao(null),
    guardar: () => edicao && guardar.mutate(edicao), aGuardar: guardar.isPending,
    apagar: () => edicao?.id && apagar.mutate(edicao.id), aApagar: apagar.isPending,
    validar: () => edicao?.id && validar.mutate(edicao.id), aValidar: validar.isPending,
    enviarFoto: (ficheiro: File, legenda: string) => edicao?.id && enviarFoto.mutate({ id: edicao.id, ficheiro, legenda }),
    aEnviarFoto: enviarFoto.isPending,
    apagarFoto: (fotoId: number) => apagarFoto.mutate(fotoId),
    urlFoto: (f: FotoReferencia) => `${URL_API}${f.url}`, // pública: não precisa do token
    novaCultura, abrirNovaCultura: () => setNovaCultura({ id: '', nome: '', nome_cientifico: '' }),
    alterarCultura: (k: keyof Cultura, v: string) => setNovaCultura((c) => (c ? { ...c, [k]: v } : c)),
    fecharNovaCultura: () => setNovaCultura(null),
    guardarCultura: () => novaCultura && criarCultura.mutate(novaCultura), aGuardarCultura: criarCultura.isPending,
  }
}
