import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { geoMercator, geoPath } from 'd3-geo'
import type { Feature, FeatureCollection, MultiPolygon } from 'geojson'
import { compacto, diaCurto, numero } from '@/nucleo/formatos'

/** Largura do contentor, actualizada quando a janela muda. */
function useLargura<T extends HTMLElement>() {
  const ref = useRef<T>(null)
  const [largura, setLargura] = useState(0)
  useEffect(() => {
    if (!ref.current) return
    const o = new ResizeObserver(([e]) => setLargura(e.contentRect.width))
    o.observe(ref.current)
    return () => o.disconnect()
  }, [])
  return [ref, largura] as const
}

function passoLimpo(maximo: number, marcas = 4): number {
  const bruto = Math.max(maximo, 1) / marcas
  const ordem = 10 ** Math.floor(Math.log10(bruto))
  return ([1, 2, 5, 10].find((m) => m * ordem >= bruto) ?? 10) * ordem
}

function Dica({ x, y, titulo, linhas }: { x: number; y: number; titulo: string; linhas: { cor?: string; nome: string; valor: ReactNode }[] }) {
  return (
    <div className="dica" style={{ left: x, top: y }}>
      <strong>{titulo}</strong>
      {linhas.map((l) => (
        <div key={l.nome} className="linha-dica">
          {l.cor && <span className="amostra" style={{ background: l.cor }} />}
          {l.nome}
          <b>{l.valor}</b>
        </div>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------------------------------------
// Colunas empilhadas por dia (doenças + pragas). As folhas saudáveis vão só na dica.

export interface SerieDia {
  dia: string
  total: number
  doencas: number
  pragas: number
}

export function ColunasDiarias({ dados, altura = 220 }: { dados: SerieDia[]; altura?: number }) {
  const [ref, largura] = useLargura<HTMLDivElement>()
  const [foco, setFoco] = useState<number | null>(null)
  const margem = { cima: 8, baixo: 24, esquerda: 32, direita: 4 }
  const maximo = Math.max(...dados.map((d) => d.doencas + d.pragas), 1)
  const passo = passoLimpo(maximo)
  const topo = Math.ceil(maximo / passo) * passo
  const internoL = Math.max(largura - margem.esquerda - margem.direita, 0)
  const internoA = altura - margem.cima - margem.baixo
  const banda = dados.length ? internoL / dados.length : 0
  const larguraBarra = Math.min(24, Math.max(banda - 4, 2))
  const y = (v: number) => margem.cima + internoA - (v / topo) * internoA
  const marcas = Array.from({ length: Math.round(topo / passo) + 1 }, (_, i) => i * passo)
  const cadaRotulo = Math.max(1, Math.ceil(dados.length / 6))

  return (
    <div className="grafico" ref={ref}>
      <div className="legenda" style={{ marginBottom: 8 }}>
        <span><i className="amostra" style={{ background: 'var(--serie-1)' }} />Doenças</span>
        <span><i className="amostra" style={{ background: 'var(--serie-2)' }} />Pragas</span>
      </div>
      {largura > 0 && (
        <svg height={altura} role="img" aria-label="Diagnósticos de doenças e pragas por dia">
          {marcas.map((m) => (
            <g key={m}>
              <line className={m === 0 ? 'base' : 'grelha-linha'} x1={margem.esquerda} x2={largura - margem.direita} y1={y(m)} y2={y(m)} />
              <text className="eixo-texto" x={margem.esquerda - 8} y={y(m)} dy="0.32em" textAnchor="end">{compacto(m)}</text>
            </g>
          ))}
          {dados.map((d, i) => {
            const cx = margem.esquerda + banda * i + banda / 2
            const x = cx - larguraBarra / 2
            const hD = y(0) - y(d.doencas)
            const hP = y(0) - y(d.pragas)
            const gap = d.doencas > 0 && d.pragas > 0 ? 2 : 0
            return (
              <g key={d.dia} onMouseEnter={() => setFoco(i)} onMouseLeave={() => setFoco(null)}>
                <rect x={margem.esquerda + banda * i} y={margem.cima} width={banda} height={internoA} fill="transparent" />
                {foco === i && <rect x={margem.esquerda + banda * i} y={margem.cima} width={banda} height={internoA} fill="var(--superficie-2)" />}
                {d.doencas > 0 && (
                  <path d={coluna(x, y(0), larguraBarra, hD, d.pragas === 0)} fill="var(--serie-1)" />
                )}
                {d.pragas > 0 && (
                  <path d={coluna(x, y(0) - hD - gap, larguraBarra, hP, true)} fill="var(--serie-2)" />
                )}
                {i % cadaRotulo === 0 && (
                  <text className="eixo-texto" x={cx} y={altura - 6} textAnchor="middle">{diaCurto(d.dia)}</text>
                )}
              </g>
            )
          })}
        </svg>
      )}
      {foco !== null && dados[foco] && (
        <Dica
          x={margem.esquerda + banda * foco + banda / 2}
          y={y(dados[foco].doencas + dados[foco].pragas)}
          titulo={diaCurto(dados[foco].dia)}
          linhas={[
            { cor: 'var(--serie-1)', nome: 'Doenças', valor: numero(dados[foco].doencas) },
            { cor: 'var(--serie-2)', nome: 'Pragas', valor: numero(dados[foco].pragas) },
            { nome: 'Folhas saudáveis', valor: numero(dados[foco].total - dados[foco].doencas - dados[foco].pragas) },
          ]}
        />
      )}
    </div>
  )
}

/** Coluna a crescer de `base` para cima, com 4 px arredondados só na ponta (se `pontaRedonda`). */
function coluna(x: number, base: number, w: number, h: number, pontaRedonda: boolean): string {
  if (h <= 0) return ''
  const r = pontaRedonda ? Math.min(4, w / 2, h) : 0
  const t = base - h
  return `M${x},${base}V${t + r}Q${x},${t} ${x + r},${t}H${x + w - r}Q${x + w},${t} ${x + w},${t + r}V${base}Z`
}

// ---------------------------------------------------------------------------------------------
// Barras horizontais (uma série): ranking.

export function BarrasHorizontais({ itens, maximo, formatar = numero }:
  { itens: { chave: string; nome: string; valor: number; detalhe?: string }[]; maximo?: number; formatar?: (n: number) => string }) {
  const topo = maximo ?? Math.max(...itens.map((i) => i.valor), 1)
  return (
    <div className="barras-lista">
      {itens.map((i) => (
        <div key={i.chave} className="barra-item" title={i.detalhe}>
          <span className="nome">{i.nome}</span>
          <span className="valor">{formatar(i.valor)}</span>
          <div className="trilho"><div className="enchimento" style={{ width: `${(i.valor / topo) * 100}%` }} /></div>
        </div>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------------------------------------
// Mapa de Moçambique por distrito (escala sequencial azul, 5 degraus + zero).

type PropsDistrito = { distrito: string; provincia: string }
type MapaGeo = FeatureCollection<MultiPolygon, PropsDistrito>

let mapaEmCache: Promise<MapaGeo> | null = null
const carregarMapa = () => (mapaEmCache ??= fetch('/mapa_mocambique.json').then((r) => r.json() as Promise<MapaGeo>))

const DEGRAUS = ['var(--seq-1)', 'var(--seq-2)', 'var(--seq-3)', 'var(--seq-4)', 'var(--seq-5)']

/** Silhueta decorativa dos distritos (ecrã de entrada). */
export function SilhuetaMocambique({ altura }: { altura: number }) {
  const [ref, largura] = useLargura<HTMLDivElement>()
  const [mapa, setMapa] = useState<MapaGeo | null>(null)
  useEffect(() => { carregarMapa().then(setMapa).catch(() => setMapa(null)) }, [])
  const caminho = mapa && largura > 0 ? geoPath(geoMercator().fitSize([largura, altura], mapa)) : null
  return (
    <div ref={ref} style={{ width: '100%', height: altura }}>
      {caminho && mapa && (
        <svg width={largura} height={altura} aria-hidden="true">
          {mapa.features.map((f) => (
            <path key={`${f.properties.provincia}|${f.properties.distrito}`} d={caminho(f) ?? ''}
              fill="rgba(229,240,233,0.07)" stroke="rgba(229,240,233,0.28)" strokeWidth={0.6} />
          ))}
        </svg>
      )}
    </div>
  )
}

export interface ValorDistrito {
  distrito: string
  provincia_codigo: string
  valor: number
  detalhe?: { nome: string; valor: string }[]
}

export function MapaDistritos({ valores, altura = 460, rotuloValor = 'Diagnósticos', aoEscolher, seleccionado }:
  { valores: ValorDistrito[]; altura?: number; rotuloValor?: string; aoEscolher?: (v: ValorDistrito | null, distrito: string, provincia: string) => void; seleccionado?: string | null }) {
  const [ref, largura] = useLargura<HTMLDivElement>()
  const [mapa, setMapa] = useState<MapaGeo | null>(null)
  const [foco, setFoco] = useState<{ x: number; y: number; f: Feature<MultiPolygon, PropsDistrito> } | null>(null)
  useEffect(() => { carregarMapa().then(setMapa).catch(() => setMapa(null)) }, [])

  const porChave = useMemo(() => new Map(valores.map((v) => [`${v.provincia_codigo}|${v.distrito}`, v])), [valores])
  const maximo = Math.max(...valores.map((v) => v.valor), 0)
  const limites = useMemo(() => {
    if (maximo <= 0) return [] as number[]
    const p = Math.max(1, Math.ceil(maximo / 5))
    return [1, 2, 3, 4].map((k) => k * p)
  }, [maximo])
  const cor = (v: number) => (v <= 0 ? 'var(--seq-0)' : DEGRAUS[limites.filter((l) => v > l).length])

  const caminho = useMemo(() => {
    if (!mapa || largura <= 0) return null
    const projeccao = geoMercator().fitSize([largura, altura], mapa)
    return geoPath(projeccao)
  }, [mapa, largura, altura])

  return (
    <div className="grafico mapa" ref={ref} style={{ minHeight: altura }}>
      {!mapa && <div className="esqueleto" style={{ height: altura }} />}
      {caminho && mapa && (
        <svg height={altura} role="img" aria-label={`${rotuloValor} por distrito`}>
          {mapa.features.map((f) => {
            const chave = `${f.properties.provincia}|${f.properties.distrito}`
            const v = porChave.get(chave)
            return (
              <path
                key={chave}
                className={`distrito${seleccionado === chave ? ' realce' : ''}${seleccionado && seleccionado !== chave ? ' fora' : ''}`}
                d={caminho(f) ?? ''}
                fill={cor(v?.valor ?? 0)}
                onMouseMove={(e) => {
                  const caixa = ref.current?.getBoundingClientRect()
                  if (caixa) setFoco({ x: e.clientX - caixa.left, y: e.clientY - caixa.top, f })
                }}
                onMouseLeave={() => setFoco(null)}
                onClick={() => aoEscolher?.(v ?? null, f.properties.distrito, f.properties.provincia)}
              />
            )
          })}
        </svg>
      )}
      {foco && (() => {
        const v = porChave.get(`${foco.f.properties.provincia}|${foco.f.properties.distrito}`)
        return (
          <Dica x={foco.x} y={foco.y} titulo={foco.f.properties.distrito}
            linhas={[{ nome: rotuloValor, valor: numero(v?.valor ?? 0) }, ...(v?.detalhe ?? [])]} />
        )
      })()}
      <div className="escala" style={{ marginTop: 8 }}>
        <span>{rotuloValor}:</span>
        <span className="degraus">
          <span style={{ background: 'var(--seq-0)', boxShadow: 'inset 0 0 0 1px var(--linha)' }} title="0" />
          {DEGRAUS.map((d) => <span key={d} style={{ background: d }} />)}
        </span>
        <span className="numeros">0 → {numero(maximo)}</span>
      </div>
    </div>
  )
}
