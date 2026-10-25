import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { modelosRepo } from '@/model/repositorios'
import { useNotificar } from '@/nucleo/notificacoes'
import { useSessao } from '@/nucleo/sessao'
import { useCatalogo } from './referencias'

async function sha256(ficheiro: File): Promise<string> {
  const resumo = await crypto.subtle.digest('SHA-256', await ficheiro.arrayBuffer())
  return Array.from(new Uint8Array(resumo)).map((b) => b.toString(16).padStart(2, '0')).join('')
}

export function useModelosViewModel() {
  const { eAdministrador } = useSessao()
  const catalogo = useCatalogo()
  const cliente = useQueryClient()
  const notificar = useNotificar()
  const [cultura, setCultura] = useState('')
  useEffect(() => {
    if (!cultura && catalogo.culturas.length) setCultura(catalogo.culturas[0].id)
  }, [cultura, catalogo.culturas])

  const historico = useQuery({
    queryKey: ['modelos', cultura], queryFn: () => modelosRepo.historico(cultura), enabled: Boolean(cultura),
  })
  const actual = historico.data?.[0]

  // Publicação
  const [aPublicar, setAPublicar] = useState(false)
  const [ficheiro, setFicheiro] = useState<File | null>(null)
  const [resumoLocal, setResumoLocal] = useState<string | null>(null)
  const [classes, setClasses] = useState('')
  const [acuracia, setAcuracia] = useState('')

  useEffect(() => {
    setResumoLocal(null)
    if (ficheiro) sha256(ficheiro).then(setResumoLocal)
  }, [ficheiro])

  const abrirPublicacao = () => {
    setFicheiro(null)
    setAcuracia('')
    setClasses((actual?.classes ?? catalogo.patologiasDe(cultura).map((p) => p.codigo).sort()).join('\n'))
    setAPublicar(true)
  }

  const listaClasses = classes.split(/\s*\n\s*/).map((c) => c.trim()).filter(Boolean)
  const desconhecidas = listaClasses.filter((c) => !catalogo.patologia(cultura, c))
  const acuraciaNumero = acuracia.trim() ? Number(acuracia.replace(',', '.')) / 100 : null
  const acuraciaValida = acuraciaNumero === null || (acuraciaNumero >= 0 && acuraciaNumero <= 1)

  const publicar = useMutation({
    mutationFn: () => modelosRepo.publicar(cultura, ficheiro!, listaClasses, acuraciaNumero),
    onSuccess: (m) => {
      const integro = resumoLocal === m.sha256
      notificar(integro
        ? `Versão ${m.versao} publicada e verificada (SHA-256 igual). As apps instalam-na na próxima sincronização.`
        : `Versão ${m.versao} publicada, mas o SHA-256 não coincide — publique de novo.`, integro ? 'sucesso' : 'erro')
      setAPublicar(false)
      cliente.invalidateQueries({ queryKey: ['modelos', cultura] })
    },
    onError: (e: Error) => notificar(e.message, 'erro'),
  })

  return {
    eAdministrador, culturas: catalogo.culturas, nomeCultura: catalogo.nomeCultura, nomeClasse: catalogo.nomeClasse,
    cultura, setCultura,
    versoes: historico.data ?? [], actual, aCarregar: historico.isLoading, erro: historico.error as Error | null,
    aPublicar, abrirPublicacao, fecharPublicacao: () => setAPublicar(false),
    ficheiro, setFicheiro, resumoLocal, classes, setClasses, listaClasses, desconhecidas, acuracia, setAcuracia, acuraciaValida,
    podePublicar: Boolean(ficheiro && ficheiro.name.endsWith('.tflite') && listaClasses.length >= 2 && acuraciaValida && resumoLocal),
    publicar: () => publicar.mutate(), aEnviar: publicar.isPending,
  }
}
