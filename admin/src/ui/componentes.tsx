import { useEffect, useState, type ButtonHTMLAttributes, type ReactNode, type SelectHTMLAttributes } from 'react'
import { ImageOff, Inbox, X } from 'lucide-react'
import { urlProtegido } from '@/model/http'
import { LIMIAR_CONFIANCA, type Tom } from '@/nucleo/rotulos'
import { percentagem } from '@/nucleo/formatos'

type Variante = 'primario' | 'secundario' | 'fantasma' | 'perigo'

export function Botao({ variante = 'secundario', pequeno, icone, className = '', children, ...resto }:
  ButtonHTMLAttributes<HTMLButtonElement> & { variante?: Variante; pequeno?: boolean; icone?: boolean }) {
  const classes = ['botao', variante, pequeno && 'pequeno', icone && 'icone', className].filter(Boolean).join(' ')
  return <button type="button" className={classes} {...resto}>{children}</button>
}

export function Campo({ rotulo, ajuda, erro, largo, children }:
  { rotulo: string; ajuda?: ReactNode; erro?: string | null; largo?: boolean; children: ReactNode }) {
  return (
    <label className={`campo${largo ? ' largo' : ''}`}>
      <span>{rotulo}</span>
      {children}
      {erro ? <small className="erro">{erro}</small> : ajuda ? <small>{ajuda}</small> : null}
    </label>
  )
}

export function Seleccao({ opcoes, vazio, ...resto }:
  SelectHTMLAttributes<HTMLSelectElement> & { opcoes: { valor: string; nome: string }[]; vazio?: string }) {
  return (
    <select className="entrada" {...resto}>
      {vazio !== undefined && <option value="">{vazio}</option>}
      {opcoes.map((o) => <option key={o.valor} value={o.valor}>{o.nome}</option>)}
    </select>
  )
}

export function Etiqueta({ tom = 'neutro', icone, children }: { tom?: Tom; icone?: ReactNode; children: ReactNode }) {
  return <span className={`etiqueta ${tom}`}>{icone}{children}</span>
}

export function Cartao({ titulo, subtitulo, accoes, semMargem, children, className = '' }:
  { titulo?: ReactNode; subtitulo?: ReactNode; accoes?: ReactNode; semMargem?: boolean; children: ReactNode; className?: string }) {
  return (
    <section className={`cartao ${className}`}>
      {(titulo || accoes) && (
        <header className="cartao-cabecalho">
          <div>
            {titulo && <h2>{titulo}</h2>}
            {subtitulo && <p>{subtitulo}</p>}
          </div>
          {accoes}
        </header>
      )}
      <div className={`cartao-corpo${semMargem ? ' sem-margem' : ''}`}>{children}</div>
    </section>
  )
}

export function CabecalhoPagina({ titulo, descricao, accoes }: { titulo: string; descricao?: ReactNode; accoes?: ReactNode }) {
  return (
    <div className="cabecalho-pagina">
      <div>
        <h1>{titulo}</h1>
        {descricao && <p>{descricao}</p>}
      </div>
      {accoes && <div className="accoes">{accoes}</div>}
    </div>
  )
}

export function Indicador({ rotulo, valor, variacao }: { rotulo: string; valor: ReactNode; variacao?: ReactNode }) {
  return (
    <div className="cartao indicador">
      <span className="rotulo">{rotulo}</span>
      <span className="valor">{valor}</span>
      {variacao}
    </div>
  )
}

export function Segmentos<T extends string | number>({ valor, opcoes, aoMudar, rotulo }:
  { valor: T; opcoes: { valor: T; nome: string }[]; aoMudar: (v: T) => void; rotulo: string }) {
  return (
    <div className="segmentos" role="group" aria-label={rotulo}>
      {opcoes.map((o) => (
        <button key={String(o.valor)} type="button" aria-pressed={o.valor === valor} onClick={() => aoMudar(o.valor)}>
          {o.nome}
        </button>
      ))}
    </div>
  )
}

export function Separadores<T extends string>({ valor, opcoes, aoMudar }:
  { valor: T; opcoes: { valor: T; nome: string }[]; aoMudar: (v: T) => void }) {
  return (
    <div className="separadores" role="tablist">
      {opcoes.map((o) => (
        <button key={o.valor} role="tab" aria-selected={o.valor === valor} onClick={() => aoMudar(o.valor)}>{o.nome}</button>
      ))}
    </div>
  )
}

export function Gaveta({ aberta, titulo, subtitulo, aoFechar, rodape, larga, children }:
  { aberta: boolean; titulo: ReactNode; subtitulo?: ReactNode; aoFechar: () => void; rodape?: ReactNode; larga?: boolean; children: ReactNode }) {
  useEffect(() => {
    if (!aberta) return
    const tecla = (e: KeyboardEvent) => e.key === 'Escape' && aoFechar()
    window.addEventListener('keydown', tecla)
    return () => window.removeEventListener('keydown', tecla)
  }, [aberta, aoFechar])
  if (!aberta) return null
  return (
    <>
      <div className="veu" onClick={aoFechar} />
      <aside className={`gaveta${larga ? ' larga' : ''}`} role="dialog" aria-modal="true">
        <header className="gaveta-cabecalho">
          <div>
            <h2>{titulo}</h2>
            {subtitulo && <p>{subtitulo}</p>}
          </div>
          <Botao variante="fantasma" icone onClick={aoFechar} aria-label="Fechar"><X size={18} /></Botao>
        </header>
        <div className="gaveta-corpo">{children}</div>
        {rodape && <footer className="gaveta-rodape">{rodape}</footer>}
      </aside>
    </>
  )
}

export function Vazio({ titulo, texto, icone }: { titulo: string; texto?: ReactNode; icone?: ReactNode }) {
  return (
    <div className="vazio">
      {icone ?? <Inbox size={28} />}
      <strong>{titulo}</strong>
      {texto && <span className="pequeno">{texto}</span>}
    </div>
  )
}

export function Esqueleto({ altura = 16, largura = '100%' }: { altura?: number; largura?: number | string }) {
  return <div className="esqueleto" style={{ height: altura, width: largura }} />
}

export function Paginacao({ total, limite, deslocamento, aoMudar }:
  { total: number; limite: number; deslocamento: number; aoMudar: (d: number) => void }) {
  if (total <= limite) return null
  const fim = Math.min(deslocamento + limite, total)
  return (
    <div className="paginacao">
      <span className="numeros">{deslocamento + 1}–{fim} de {total}</span>
      <div className="accoes">
        <Botao pequeno disabled={deslocamento === 0} onClick={() => aoMudar(Math.max(0, deslocamento - limite))}>Anterior</Botao>
        <Botao pequeno disabled={fim >= total} onClick={() => aoMudar(deslocamento + limite)}>Seguinte</Botao>
      </div>
    </div>
  )
}

export function Confianca({ valor }: { valor: number }) {
  const baixa = valor < LIMIAR_CONFIANCA
  return (
    <span className={`confianca${baixa ? ' baixa' : ''}`} title={baixa ? 'Abaixo de 60%: a app mostrou aviso' : undefined}>
      <span className="trilho"><span className="enchimento" style={{ width: `${Math.round(valor * 100)}%` }} /></span>
      {percentagem(valor)}
    </span>
  )
}

/** Imagem de uma rota protegida (a API exige o token, por isso não serve um <img src> directo). */
export function ImagemProtegida({ caminho, alt, className, altura }:
  { caminho: string | null; alt: string; className?: string; altura?: number }) {
  const [url, setUrl] = useState<string | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  useEffect(() => {
    if (!caminho) return
    let activo = true
    let criado: string | null = null
    setUrl(null)
    setErro(null)
    urlProtegido(caminho)
      .then((u) => { criado = u; if (activo) setUrl(u) })
      .catch((e: Error) => activo && setErro(e.message))
    return () => { activo = false; if (criado) URL.revokeObjectURL(criado) }
  }, [caminho])
  if (!caminho || erro) {
    return (
      <div className={`vazio ${className ?? ''}`} style={{ minHeight: altura }}>
        <ImageOff size={22} />
        <span className="pequeno">{erro ?? 'Sem imagem'}</span>
      </div>
    )
  }
  if (!url) return <div className={`esqueleto ${className ?? ''}`} style={{ height: altura ?? 200 }} />
  return <img src={url} alt={alt} className={className} />
}
