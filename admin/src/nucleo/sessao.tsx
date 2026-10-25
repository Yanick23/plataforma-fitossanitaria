import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { definirToken, ErroApi, obterToken, quandoSessaoExpirar } from '@/model/http'
import { authRepo } from '@/model/repositorios'
import type { Utilizador } from '@/model/tipos'

interface Sessao {
  utilizador: Utilizador | null
  aVerificar: boolean
  eAdministrador: boolean
  entrar: (telefone: string, palavraPasse: string) => Promise<void>
  sair: () => void
}

const Contexto = createContext<Sessao | null>(null)

/** ViewModel da sessão: guarda o token, confirma a conta e expõe o perfil. Só o pessoal entra. */
export function FornecedorSessao({ children }: { children: ReactNode }) {
  const cliente = useQueryClient()
  const [utilizador, setUtilizador] = useState<Utilizador | null>(null)
  const [aVerificar, setAVerificar] = useState(Boolean(obterToken()))

  const sair = useCallback(() => {
    definirToken(null)
    setUtilizador(null)
    cliente.clear()
  }, [cliente])

  useEffect(() => quandoSessaoExpirar(() => setUtilizador(null)), [])

  useEffect(() => {
    if (!obterToken()) return
    authRepo.eu()
      .then((u) => (u.perfil === 'AGRICULTOR' ? sair() : setUtilizador(u)))
      .catch(() => sair())
      .finally(() => setAVerificar(false))
  }, [sair])

  const entrar = useCallback(async (telefone: string, palavraPasse: string) => {
    const r = await authRepo.entrar(telefone.replace(/\s+/g, ''), palavraPasse)
    if (r.utilizador.perfil === 'AGRICULTOR') {
      throw new ErroApi('Este painel é para técnicos e administradores. Os agricultores usam a aplicação móvel.')
    }
    definirToken(r.access_token)
    setUtilizador(r.utilizador)
  }, [])

  const valor = useMemo<Sessao>(() => ({
    utilizador, aVerificar, entrar, sair, eAdministrador: utilizador?.perfil === 'ADMINISTRADOR',
  }), [utilizador, aVerificar, entrar, sair])

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

export function useSessao(): Sessao {
  const s = useContext(Contexto)
  if (!s) throw new Error('useSessao fora do FornecedorSessao')
  return s
}
