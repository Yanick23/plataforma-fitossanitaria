import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { catalogoRepo } from '@/model/repositorios'
import type { Cultura, Patologia, TipoPatologia } from '@/model/tipos'
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
}

export function useCatalogoViewModel() {
  const { eAdministrador } = useSessao()
  const catalogo = useCatalogo()
  const cliente = useQueryClient()
  const notificar = useNotificar()
  const [cultura, setCultura] = useState('')
  const [edicao, setEdicao] = useState<RascunhoPatologia | null>(null)
  const [novaCultura, setNovaCultura] = useState<Cultura | null>(null)
  const [pesquisa, setPesquisa] = useState('')

  useEffect(() => {
    if (!cultura && catalogo.culturas.length) setCultura(catalogo.culturas[0].id)
  }, [cultura, catalogo.culturas])

  const recarregar = () => {
    cliente.invalidateQueries({ queryKey: ['patologias'] })
    cliente.invalidateQueries({ queryKey: ['culturas'] })
  }
  const aoErro = (e: Error) => notificar(e.message, 'erro')

  const guardar = useMutation({
    mutationFn: (r: RascunhoPatologia) => (r.id === null
      ? catalogoRepo.criarPatologia({ cultura_id: r.cultura_id, codigo: r.codigo, nome_local: r.nome_local, nome_cientifico: r.nome_cientifico, tipo: r.tipo, recomendacao: r.recomendacao })
      : catalogoRepo.actualizarPatologia({ ...r, id: r.id } as Patologia)),
    onSuccess: (_, r) => {
      notificar(r.id === null ? 'Praga/doença criada' : 'Alterações guardadas; a app recebe-as na próxima sincronização')
      setEdicao(null)
      recarregar()
    },
    onError: aoErro,
  })
  const apagar = useMutation({
    mutationFn: (id: number) => catalogoRepo.apagarPatologia(id),
    onSuccess: () => { notificar('Praga/doença apagada'); setEdicao(null); recarregar() },
    onError: aoErro,
  })
  const criarCultura = useMutation({
    mutationFn: (c: Cultura) => catalogoRepo.criarCultura(c),
    onSuccess: (c) => { notificar(`Cultura «${c.nome}» criada`); setNovaCultura(null); setCultura(c.id); recarregar() },
    onError: aoErro,
  })

  const termo = pesquisa.trim().toLowerCase()
  const patologias = catalogo.patologiasDe(cultura).filter((p) =>
    !termo || [p.nome_local, p.nome_cientifico, p.codigo, p.recomendacao].some((t) => t.toLowerCase().includes(termo)))
  const recomendacaoEmFalta = (p: Patologia) => p.recomendacao.trim().length < 20

  return {
    eAdministrador, culturas: catalogo.culturas, aCarregar: catalogo.aCarregar, nomeCultura: catalogo.nomeCultura,
    cultura, setCultura, pesquisa, setPesquisa, patologias, recomendacaoEmFalta,
    edicao, editar: (p: Patologia) => setEdicao({ ...p }),
    nova: () => setEdicao({ id: null, cultura_id: cultura, codigo: '', nome_local: '', nome_cientifico: '', tipo: 'DOENCA', recomendacao: '' }),
    alterar: <K extends keyof RascunhoPatologia>(k: K, v: RascunhoPatologia[K]) => setEdicao((e) => (e ? { ...e, [k]: v } : e)),
    fecharEdicao: () => setEdicao(null),
    guardar: () => edicao && guardar.mutate(edicao), aGuardar: guardar.isPending,
    apagar: () => edicao?.id && apagar.mutate(edicao.id), aApagar: apagar.isPending,
    novaCultura, abrirNovaCultura: () => setNovaCultura({ id: '', nome: '', nome_cientifico: '' }),
    alterarCultura: (k: keyof Cultura, v: string) => setNovaCultura((c) => (c ? { ...c, [k]: v } : c)),
    fecharNovaCultura: () => setNovaCultura(null),
    guardarCultura: () => novaCultura && criarCultura.mutate(novaCultura), aGuardarCultura: criarCultura.isPending,
  }
}
