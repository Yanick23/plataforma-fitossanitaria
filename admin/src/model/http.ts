import axios, { AxiosError } from 'axios'

/** Erro da API com uma mensagem pronta a mostrar (vem do campo `detail` do FastAPI). */
export class ErroApi extends Error {
  constructor(
    public readonly mensagem: string,
    public readonly estado?: number,
  ) {
    super(mensagem)
  }
}

export const URL_API: string = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000'

const CHAVE_TOKEN = 'painel.token'

/** O token vive em memória e, se o navegador deixar, no localStorage (sobrevive a recarregar). */
let token: string | null = (() => {
  try {
    return localStorage.getItem(CHAVE_TOKEN)
  } catch {
    return null
  }
})()

export function obterToken(): string | null {
  return token
}

export function definirToken(novo: string | null): void {
  token = novo
  try {
    if (novo) localStorage.setItem(CHAVE_TOKEN, novo)
    else localStorage.removeItem(CHAVE_TOKEN)
  } catch {
    /* sem armazenamento: a sessão dura até fechar o separador */
  }
}

type Ouvinte = () => void
const aoExpirar = new Set<Ouvinte>()
export function quandoSessaoExpirar(f: Ouvinte): () => void {
  aoExpirar.add(f)
  return () => aoExpirar.delete(f)
}

export const http = axios.create({ baseURL: URL_API, timeout: 20_000 })

http.interceptors.request.use((config) => {
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

function mensagemDe(erro: AxiosError<{ detail?: unknown }>): string {
  if (!erro.response) return `Sem ligação à API (${URL_API}). Confirme que o servidor está a correr.`
  const detalhe = erro.response.data?.detail
  if (typeof detalhe === 'string') return detalhe
  if (Array.isArray(detalhe) && detalhe.length) {
    const primeiro = detalhe[0] as { msg?: string; loc?: unknown[] }
    const campo = Array.isArray(primeiro.loc) ? primeiro.loc.slice(1).join('.') : ''
    return `Dados inválidos${campo ? ` em «${campo}»` : ''}: ${primeiro.msg ?? ''}`.trim()
  }
  return `Erro ${erro.response.status} do servidor`
}

http.interceptors.response.use(
  (r) => r,
  (erro: AxiosError<{ detail?: unknown }>) => {
    if (erro.response?.status === 401 && token) {
      definirToken(null)
      aoExpirar.forEach((f) => f())
    }
    return Promise.reject(new ErroApi(mensagemDe(erro), erro.response?.status))
  },
)

/** Descarrega um recurso protegido (imagem, ZIP) como URL local para usar em <img> ou num link. */
export async function urlProtegido(caminho: string): Promise<string> {
  const r = await http.get<Blob>(caminho, { responseType: 'blob' })
  return URL.createObjectURL(r.data)
}
