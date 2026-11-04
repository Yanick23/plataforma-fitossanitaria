import { useEffect, useState } from 'react'
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { utilizadoresRepo, type FiltrosUtilizadores } from '@/model/repositorios'
import type { Perfil, UtilizadorAdmin } from '@/model/tipos'
import { useNotificar } from '@/nucleo/notificacoes'
import { useSessao } from '@/nucleo/sessao'

const LIMITE = 25

export interface FormularioConta {
  id: number | null
  nome: string
  telefone: string
  palavra_passe: string
  perfil: Perfil
  provincia: string
  distrito: string
  activo: boolean
}

const VAZIO: FormularioConta = { id: null, nome: '', telefone: '', palavra_passe: '', perfil: 'TECNICO', provincia: '', distrito: '', activo: true }

export function useUtilizadoresViewModel() {
  const { eAdministrador, utilizador: eu } = useSessao()
  const cliente = useQueryClient()
  const notificar = useNotificar()
  const [filtros, setFiltros] = useState({ q: '', perfil: '' as Perfil | '', provincia: '', distrito: '', estado: '' as '' | 'activo' | 'inactivo' })
  const [pesquisa, setPesquisa] = useState('')
  const [deslocamento, setDeslocamento] = useState(0)
  const [form, setForm] = useState<FormularioConta | null>(null)
  const [novaPalavraPasse, setNovaPalavraPasse] = useState('')

  useEffect(() => { const t = setTimeout(() => setFiltros((f) => ({ ...f, q: pesquisa })), 300); return () => clearTimeout(t) }, [pesquisa])
  useEffect(() => setDeslocamento(0), [filtros])

  const pedido: FiltrosUtilizadores = {
    q: filtros.q || undefined,
    perfil: filtros.perfil || undefined,
    provincia: filtros.provincia || undefined,
    distrito_id: filtros.distrito ? Number(filtros.distrito) : undefined,
    activo: filtros.estado ? filtros.estado === 'activo' : undefined,
    limite: LIMITE,
    deslocamento,
  }
  const lista = useQuery({ queryKey: ['utilizadores', pedido], queryFn: () => utilizadoresRepo.listar(pedido), placeholderData: keepPreviousData })

  const aoMudar = (texto: string) => {
    notificar(texto)
    setForm(null)
    cliente.invalidateQueries({ queryKey: ['utilizadores'] })
    cliente.invalidateQueries({ queryKey: ['resumo'] })
  }
  const aoErro = (e: Error) => notificar(e.message, 'erro')

  const zonaDe = (f: FormularioConta) => ({
    distrito_id: f.distrito ? Number(f.distrito) : null,
    provincia_codigo: f.distrito ? null : f.provincia || null,
  })

  const guardar = useMutation({
    mutationFn: async (f: FormularioConta) => {
      if (f.id === null) {
        return utilizadoresRepo.criar({ nome: f.nome.trim(), telefone: f.telefone.replace(/\s+/g, ''), palavra_passe: f.palavra_passe, perfil: f.perfil, ...zonaDe(f) })
      }
      return utilizadoresRepo.actualizar(f.id, { nome: f.nome.trim(), perfil: f.perfil, activo: f.activo, ...zonaDe(f) })
    },
    onSuccess: (_, f) => aoMudar(f.id === null ? 'Conta criada' : 'Conta actualizada'),
    onError: aoErro,
  })
  const repor = useMutation({
    mutationFn: ({ id, palavra }: { id: number; palavra: string }) => utilizadoresRepo.reporPalavraPasse(id, palavra),
    onSuccess: () => { notificar('Palavra-passe reposta. Comunique-a ao utilizador por um canal seguro.'); setNovaPalavraPasse('') },
    onError: aoErro,
  })

  const abrir = (u: UtilizadorAdmin) => setForm({
    id: u.id, nome: u.nome, telefone: u.telefone, palavra_passe: '', perfil: u.perfil,
    provincia: u.provincia_codigo ?? '', distrito: u.distrito_id ? String(u.distrito_id) : '', activo: u.activo,
  })
  const alterarFiltro = <K extends keyof typeof filtros>(k: K, v: (typeof filtros)[K]) =>
    setFiltros((f) => ({ ...f, [k]: v, ...(k === 'provincia' ? { distrito: '' } : {}) }))
  const alterar = <K extends keyof FormularioConta>(k: K, v: FormularioConta[K]) =>
    setForm((f) => (f ? { ...f, [k]: v, ...(k === 'provincia' ? { distrito: '' } : {}) } : f))

  const valido = Boolean(form && form.nome.trim().length >= 2 && (form.id !== null
    || (/^\+?\d{9,15}$/.test(form.telefone.replace(/\s+/g, '')) && form.palavra_passe.length >= 6)))

  return {
    eAdministrador, euId: eu?.id,
    pesquisa, setPesquisa, filtros, alterarFiltro,
    pagina: lista.data, aCarregar: lista.isLoading, erro: lista.error as Error | null, limite: LIMITE, deslocamento, setDeslocamento,
    form, abrir, nova: () => setForm({ ...VAZIO }), fechar: () => { setForm(null); setNovaPalavraPasse('') }, alterar, valido,
    guardar: () => form && guardar.mutate(form), aGuardar: guardar.isPending,
    novaPalavraPasse, setNovaPalavraPasse,
    repor: () => form?.id && novaPalavraPasse.length >= 6 && repor.mutate({ id: form.id, palavra: novaPalavraPasse }), aRepor: repor.isPending,
  }
}
