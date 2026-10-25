const LOCAL = 'pt-MZ'

const fmtData = new Intl.DateTimeFormat(LOCAL, { day: '2-digit', month: 'short', year: 'numeric' })
const fmtDataHora = new Intl.DateTimeFormat(LOCAL, {
  day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
})
const fmtDiaCurto = new Intl.DateTimeFormat(LOCAL, { day: 'numeric', month: 'short' })
const fmtNumero = new Intl.NumberFormat(LOCAL)
const fmtCompacto = new Intl.NumberFormat(LOCAL, { notation: 'compact', maximumFractionDigits: 1 })
const fmtRelativo = new Intl.RelativeTimeFormat(LOCAL, { numeric: 'auto' })

export const data = (iso: string) => fmtData.format(new Date(iso)).replace('.', '')
export const dataHora = (iso: string) => fmtDataHora.format(new Date(iso)).replace('.', '')
export const diaCurto = (iso: string) => fmtDiaCurto.format(new Date(`${iso}T12:00:00`)).replace('.', '')
export const numero = (n: number) => fmtNumero.format(n)
export const compacto = (n: number) => (Math.abs(n) < 1000 ? fmtNumero.format(n) : fmtCompacto.format(n))
export const percentagem = (x: number | null | undefined, casas = 0) =>
  x === null || x === undefined ? '—' : `${(x * 100).toFixed(casas).replace('.', ',')}%`

export function relativo(iso: string): string {
  const segundos = (new Date(iso).getTime() - Date.now()) / 1000
  const passos: [number, Intl.RelativeTimeFormatUnit][] = [
    [60, 'second'], [60, 'minute'], [24, 'hour'], [7, 'day'], [4.35, 'week'], [12, 'month'], [Infinity, 'year'],
  ]
  let valor = segundos
  for (const [limite, unidade] of passos) {
    if (Math.abs(valor) < limite) return fmtRelativo.format(Math.round(valor), unidade)
    valor /= limite
  }
  return data(iso)
}

export function bytes(n: number): string {
  if (n < 1024) return `${n} B`
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(1).replace('.', ',')} KB`
  return `${(n / 1024 ** 2).toFixed(2).replace('.', ',')} MB`
}

/** Início do dia (hora local) N dias atrás, em ISO, para filtros por data. */
export function diasAtras(n: number): string {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  d.setDate(d.getDate() - n)
  return d.toISOString()
}
