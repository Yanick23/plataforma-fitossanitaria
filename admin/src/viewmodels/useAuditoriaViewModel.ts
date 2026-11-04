import { useEffect, useState } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { auditoriaRepo } from '@/model/repositorios'
import type { RegistoAuditoria } from '@/model/tipos'

const LIMITE = 30

export interface Diferenca {
  campo: string
  antes: string
  depois: string
}

const mostrar = (v: unknown) => (v === null || v === undefined || v === '' ? '—' : typeof v === 'object' ? JSON.stringify(v) : String(v))

/** Transforma o JSON {antes, depois} numa lista de campos alterados. */
export function diferencas(r: RegistoAuditoria): Diferenca[] {
  if (!r.detalhes) return []
  try {
    const d = JSON.parse(r.detalhes) as { antes?: Record<string, unknown>; depois?: Record<string, unknown> }
    const campos = new Set([...Object.keys(d.antes ?? {}), ...Object.keys(d.depois ?? {})])
    return [...campos]
      .map((c) => ({ campo: c, antes: mostrar(d.antes?.[c]), depois: mostrar(d.depois?.[c]) }))
      .filter((x) => !d.antes || !d.depois || x.antes !== x.depois)
  } catch {
    return [{ campo: 'detalhes', antes: '—', depois: r.detalhes }]
  }
}

export function useAuditoriaViewModel() {
  const [entidade, setEntidade] = useState('')
  const [deslocamento, setDeslocamento] = useState(0)
  const [aberto, setAberto] = useState<RegistoAuditoria | null>(null)
  useEffect(() => setDeslocamento(0), [entidade])
  const pagina = useQuery({
    queryKey: ['auditoria', entidade, deslocamento],
    queryFn: () => auditoriaRepo.listar({ entidade: entidade || undefined, limite: LIMITE, deslocamento }),
    placeholderData: keepPreviousData,
  })
  return {
    entidade, setEntidade, deslocamento, setDeslocamento, limite: LIMITE,
    pagina: pagina.data, aCarregar: pagina.isLoading, erro: pagina.error as Error | null,
    aberto, abrir: setAberto, fechar: () => setAberto(null),
  }
}
