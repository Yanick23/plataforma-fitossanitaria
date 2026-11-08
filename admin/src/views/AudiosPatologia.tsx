import { CircleCheck, Clock, Save, Trash2 } from 'lucide-react'
import type { Patologia } from '@/model/tipos'
import { data } from '@/nucleo/formatos'
import { Botao, Campo, Etiqueta, Seleccao } from '@/ui/componentes'
import { Gravador } from '@/ui/Gravador'
import { urlAudio, useAudiosPatologia } from '@/viewmodels/useAudiosViewModel'

const duracao = (s: number | null) => (s ? `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, '0')}` : '')

/** Secção da gaveta do catálogo: a recomendação lida em voz alta, numa ou várias línguas locais. */
export function AudiosPatologia({ patologia }: { patologia: Patologia }) {
  const vm = useAudiosPatologia(patologia.id)

  return (
    <section className="caixa-seccao">
      <h3>Áudio em línguas locais</h3>
      <p className="secundario pequeno">
        Para quem lê pouco: alguém da equipa lê a recomendação em voz alta, na língua dos agricultores. A app toca-a sem
        Internet. Outra pessoa da equipa confirma que diz o mesmo que o texto; só então chega à app.
      </p>
      {vm.aCarregar ? <p className="suave">A carregar…</p> : vm.audios.length === 0 ? <p className="suave">Ainda sem gravações.</p> : (
        <ul className="lista-audios">
          {vm.audios.map((a) => (
            <li key={a.id}>
              <span>
                <b>{a.lingua_nome}</b>
                <span className="suave pequeno" style={{ display: 'block' }}>{duracao(a.duracao_s)}{a.reproducoes ? ` · ouvida ${a.reproducoes}×` : ''}</span>
              </span>
              <span style={{ minWidth: 0 }}>
                <audio controls preload="none" src={urlAudio(a)} />
                <span className="suave pequeno" style={{ display: 'block' }}>
                  Gravada por {a.autor_nome} em {data(a.criado_em)}
                  {a.validado_em ? ` · validada por ${a.validado_por_nome}` : ''}
                </span>
              </span>
              <span style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                {a.validado_em
                  ? <Etiqueta tom="bom" icone={<CircleCheck size={12} />}>Na app</Etiqueta>
                  : vm.podeValidar(a)
                    ? <Botao variante="primario" pequeno onClick={() => vm.validar(a.id)} disabled={vm.aValidar}
                        title="Ouvi a gravação e diz o mesmo que o texto"><CircleCheck size={13} />Validar</Botao>
                    : <Etiqueta tom="aviso" icone={<Clock size={12} />}>Por validar</Etiqueta>}
                {vm.podeGravar && (
                  <Botao variante="fantasma" pequeno icone aria-label={`Apagar a gravação em ${a.lingua_nome}`} title="Apagar"
                    onClick={() => { if (window.confirm(`Apagar a gravação em ${a.lingua_nome}?`)) vm.apagar(a.id) }}><Trash2 size={14} /></Botao>
                )}
              </span>
            </li>
          ))}
        </ul>
      )}
      {vm.podeGravar && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 4 }}>
          <Campo rotulo="Nova gravação: língua">
            <Seleccao value={vm.lingua} onChange={(e) => vm.setLingua(e.target.value)} vazio="Escolha a língua"
              opcoes={vm.linguas.map((l) => ({ valor: l.codigo, nome: vm.audios.some((a) => a.lingua === l.codigo) ? `${l.nome} (substitui)` : l.nome }))} />
          </Campo>
          {vm.lingua && (
            <>
              <Gravador valor={vm.gravacao} aoMudar={vm.setGravacao} desactivado={vm.aGuardar} />
              {vm.substitui && <span className="suave pequeno">Ao guardar, substitui a gravação actual em {vm.substitui.lingua_nome} e volta a precisar de validação.</span>}
              {vm.gravacao && (
                <div>
                  <Botao variante="primario" onClick={vm.guardar} disabled={vm.aGuardar}><Save size={15} />{vm.aGuardar ? 'A enviar…' : 'Guardar gravação'}</Botao>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </section>
  )
}
