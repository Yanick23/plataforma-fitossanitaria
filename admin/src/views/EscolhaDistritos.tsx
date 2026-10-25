import { useState } from 'react'
import { X } from 'lucide-react'
import { Campo, Seleccao } from '@/ui/componentes'
import { useRegioes } from '@/viewmodels/referencias'

/** Escolha de vários distritos: província → caixas dos seus distritos; os escolhidos ficam em etiquetas. */
export function EscolhaDistritos({ valor, aoMudar, desactivado }: { valor: number[]; aoMudar: (ids: number[]) => void; desactivado?: boolean }) {
  const regioes = useRegioes()
  const primeiro = regioes.distrito(valor[0])
  const [provincia, setProvincia] = useState(primeiro?.provincia_codigo ?? 'MZ-L')
  const escolhidos = new Set(valor)
  const alternar = (id: number) => aoMudar(escolhidos.has(id) ? valor.filter((x) => x !== id) : [...valor, id])

  return (
    <div className="escolha-distritos">
      {valor.length > 0 && (
        <div className="escolhidos" aria-label="Distritos escolhidos">
          {valor.map((id) => {
            const d = regioes.distrito(id)
            return (
              <span key={id} className="etiqueta marca">
                {d?.nome ?? `#${id}`}
                {!desactivado && <button type="button" aria-label={`Tirar ${d?.nome ?? id}`} onClick={() => alternar(id)}><X size={12} /></button>}
              </span>
            )
          })}
        </div>
      )}
      {!desactivado && (
        <>
          <Campo rotulo="Província">
            <Seleccao value={provincia} onChange={(e) => setProvincia(e.target.value)} opcoes={regioes.opcoesProvincias} />
          </Campo>
          <div className="lista-distritos" role="group" aria-label="Distritos da província">
            {regioes.distritosDe(provincia).map((d) => (
              <label key={d.id}>
                <input type="checkbox" checked={escolhidos.has(d.id)} onChange={() => alternar(d.id)} />
                {d.nome}
              </label>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
