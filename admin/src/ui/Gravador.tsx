import { useEffect, useRef, useState } from 'react'
import { Mic, RotateCcw, Square, Upload, X } from 'lucide-react'
import { Botao } from './componentes'

/** Uma gravação ainda só no browser (por enviar). */
export interface AudioGravado {
  blob: Blob
  duracao_s: number | null
  url: string // object URL para ouvir antes de guardar
}

const MAX_S = 120
const MAX_BYTES = 4 * 1024 * 1024

const minutos = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`

/** Duração de um ficheiro escolhido (alguns WebM não a trazem: fica desconhecida). */
function duracaoDe(url: string): Promise<number | null> {
  return new Promise((resolver) => {
    const a = new Audio()
    a.preload = 'metadata'
    a.onloadedmetadata = () => resolver(Number.isFinite(a.duration) && a.duration > 0 ? a.duration : null)
    a.onerror = () => resolver(null)
    a.src = url
  })
}

/**
 * Grava pelo microfone do browser (MediaRecorder: WebM/Opus no Chrome, Ogg/Opus no Firefox) ou aceita um
 * ficheiro gravado noutro sítio (ex.: no telemóvel). Pára sozinho aos 2 minutos. Antes de guardar, ouve-se.
 */
export function Gravador({ valor, aoMudar, desactivado }:
  { valor: AudioGravado | null; aoMudar: (g: AudioGravado | null) => void; desactivado?: boolean }) {
  const [aGravar, setAGravar] = useState(false)
  const [segundos, setSegundos] = useState(0)
  const [erro, setErro] = useState<string | null>(null)
  const gravador = useRef<MediaRecorder | null>(null)
  const inicio = useRef(0)
  const ficheiro = useRef<HTMLInputElement>(null)

  const parar = () => {
    if (gravador.current?.state === 'recording') gravador.current.stop()
  }

  // Liberta o object URL quando a gravação muda ou o componente sai.
  useEffect(() => () => { if (valor) URL.revokeObjectURL(valor.url) }, [valor])
  // Se o componente sair a meio, desliga o microfone.
  useEffect(() => () => parar(), [])
  useEffect(() => {
    if (!aGravar) return
    const relogio = setInterval(() => {
      const s = (Date.now() - inicio.current) / 1000
      setSegundos(s)
      if (s >= MAX_S) parar()
    }, 250)
    return () => clearInterval(relogio)
  }, [aGravar])

  const comecar = async () => {
    setErro(null)
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setErro('Este browser não grava áudio. Carregue um ficheiro gravado noutro sítio.')
      return
    }
    try {
      const fluxo = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } })
      const tipo = ['audio/webm;codecs=opus', 'audio/ogg;codecs=opus', 'audio/webm', 'audio/mp4'].find((t) => MediaRecorder.isTypeSupported(t))
      const rec = new MediaRecorder(fluxo, { ...(tipo ? { mimeType: tipo } : {}), audioBitsPerSecond: 32_000 })
      const partes: Blob[] = []
      rec.ondataavailable = (e) => { if (e.data.size) partes.push(e.data) }
      rec.onstop = () => {
        fluxo.getTracks().forEach((t) => t.stop())
        setAGravar(false)
        if (!partes.length) return
        const blob = new Blob(partes, { type: (rec.mimeType || 'audio/webm').split(';')[0] })
        aoMudar({ blob, duracao_s: Math.min((Date.now() - inicio.current) / 1000, MAX_S), url: URL.createObjectURL(blob) })
      }
      gravador.current = rec
      inicio.current = Date.now()
      setSegundos(0)
      rec.start(1000)
      setAGravar(true)
    } catch {
      setErro('Sem acesso ao microfone. Autorize o microfone neste site, ou carregue um ficheiro.')
    }
  }

  const escolherFicheiro = async (f: File | undefined) => {
    if (!f) return
    setErro(null)
    if (!f.type.startsWith('audio/')) { setErro('O ficheiro não é de áudio.'); return }
    if (f.size > MAX_BYTES) { setErro('Ficheiro maior que 4 MB. Grave uma mensagem mais curta.'); return }
    const url = URL.createObjectURL(f)
    const duracao = await duracaoDe(url)
    if (duracao !== null && duracao > MAX_S + 5) { URL.revokeObjectURL(url); setErro('A gravação tem de durar até 2 minutos.'); return }
    aoMudar({ blob: f, duracao_s: duracao, url })
  }

  if (aGravar) {
    return (
      <div className="gravador a-gravar" role="status">
        <span className="gravador-ponto" aria-hidden />
        <span>A gravar… <b className="mono">{minutos(segundos)}</b> <span className="suave">/ {minutos(MAX_S)}</span></span>
        <Botao variante="primario" pequeno onClick={parar}><Square size={13} />Parar</Botao>
      </div>
    )
  }
  if (valor) {
    return (
      <div className="gravador">
        <audio controls src={valor.url} preload="metadata" />
        <span className="suave pequeno">{valor.duracao_s ? minutos(valor.duracao_s) : ''} · {Math.max(1, Math.round(valor.blob.size / 1024))} KB</span>
        <Botao pequeno onClick={() => { aoMudar(null); comecar() }} disabled={desactivado}><RotateCcw size={13} />Gravar de novo</Botao>
        <Botao variante="fantasma" pequeno onClick={() => aoMudar(null)} disabled={desactivado}><X size={13} />Descartar</Botao>
      </div>
    )
  }
  return (
    <div>
      <div className="gravador">
        <Botao variante="primario" pequeno onClick={comecar} disabled={desactivado}><Mic size={14} />Gravar</Botao>
        <Botao pequeno onClick={() => ficheiro.current?.click()} disabled={desactivado}><Upload size={14} />Carregar ficheiro</Botao>
        <input ref={ficheiro} type="file" accept="audio/*" hidden onChange={(e) => { escolherFicheiro(e.target.files?.[0]); e.target.value = '' }} />
        <span className="suave pequeno">Até 2 minutos. Fale devagar, num sítio sem barulho.</span>
      </div>
      {erro && <p className="pequeno" style={{ color: 'var(--critico-texto)', margin: '6px 0 0' }}>{erro}</p>}
    </div>
  )
}
