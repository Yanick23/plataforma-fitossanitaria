// ViewModels partilhados: dados de referência (regiões e catálogo) usados por vários ecrãs.

import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { catalogoRepo, regioesRepo } from '@/model/repositorios'
import type { Cultura, Distrito, Patologia, Provincia } from '@/model/tipos'

const UMA_HORA = 60 * 60 * 1000

export function useRegioes() {
  const provincias = useQuery({ queryKey: ['provincias'], queryFn: regioesRepo.provincias, staleTime: UMA_HORA })
  const distritos = useQuery({ queryKey: ['distritos'], queryFn: regioesRepo.distritos, staleTime: UMA_HORA })
  return useMemo(() => {
    const listaProvincias: Provincia[] = provincias.data ?? []
    const listaDistritos: Distrito[] = distritos.data ?? []
    const nomeProvincia = new Map(listaProvincias.map((p) => [p.codigo, p.nome]))
    const distritoPorId = new Map(listaDistritos.map((d) => [d.id, d]))
    return {
      provincias: listaProvincias,
      distritos: listaDistritos,
      nomeProvincia: (codigo: string | null | undefined) => (codigo ? nomeProvincia.get(codigo) ?? codigo : '—'),
      distrito: (id: number | null | undefined) => (id ? distritoPorId.get(id) : undefined),
      distritosDe: (codigo: string | null | undefined) =>
        codigo ? listaDistritos.filter((d) => d.provincia_codigo === codigo) : listaDistritos,
      opcoesProvincias: listaProvincias.map((p) => ({ valor: p.codigo, nome: p.nome })),
    }
  }, [provincias.data, distritos.data])
}

export function useCatalogo() {
  const culturas = useQuery({ queryKey: ['culturas'], queryFn: catalogoRepo.culturas, staleTime: UMA_HORA })
  const patologias = useQuery({ queryKey: ['patologias'], queryFn: catalogoRepo.patologias, staleTime: UMA_HORA })
  return useMemo(() => {
    const listaCulturas: Cultura[] = culturas.data ?? []
    const listaPatologias: Patologia[] = patologias.data ?? []
    const porChave = new Map(listaPatologias.map((p) => [`${p.cultura_id}:${p.codigo}`, p]))
    const nomeCultura = new Map(listaCulturas.map((c) => [c.id, c.nome]))
    return {
      culturas: listaCulturas,
      patologias: listaPatologias,
      aCarregar: culturas.isLoading || patologias.isLoading,
      nomeCultura: (id: string) => nomeCultura.get(id) ?? id,
      patologia: (cultura: string, codigo: string) => porChave.get(`${cultura}:${codigo}`),
      nomeClasse: (cultura: string, codigo: string) => porChave.get(`${cultura}:${codigo}`)?.nome_local ?? codigo,
      patologiasDe: (cultura: string) => listaPatologias.filter((p) => p.cultura_id === cultura),
    }
  }, [culturas.data, patologias.data, culturas.isLoading, patologias.isLoading])
}
