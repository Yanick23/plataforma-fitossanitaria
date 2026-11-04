import { useState } from 'react'
import { BookOpen, CircleAlert, CloudRain, Info, Megaphone } from 'lucide-react'
import type { NivelRisco, RiscoDistrito, RiscoMeteorologico } from '@/model/tipos'
import { dataHora, diaCurto, numero } from '@/nucleo/formatos'
import type { Tom } from '@/nucleo/rotulos'
import { Botao, Cartao, Esqueleto, Etiqueta, Segmentos, Vazio } from '@/ui/componentes'
import { useCatalogo } from '@/viewmodels/referencias'

const NIVEL_RISCO: Record<NivelRisco, { nome: string; tom: Tom }> = {
  ALTO: { nome: 'Risco alto', tom: 'aviso' },
  MEDIO: { nome: 'Risco médio', tom: 'info' },
}

/** Risco meteorológico (9): condições do tempo favoráveis nos próximos 7 dias, por distrito. */
export function CartaoRiscoMeteo({ risco, aCarregar, erro, podeOperar, aoCriarAlerta }: {
  risco: RiscoMeteorologico | undefined
  aCarregar: boolean
  erro: Error | null
  podeOperar: boolean
  aoCriarAlerta: (r: RiscoDistrito) => void
}) {
  const catalogo = useCatalogo()
  const [filtro, setFiltro] = useState<'todos' | 'ALTO'>('todos')
  const [verRegras, setVerRegras] = useState(false)
  const itens = (risco?.itens ?? []).filter((i) => filtro === 'todos' || i.nivel === filtro)
  const periodo = risco?.itens[0] ? `${diaCurto(risco.itens[0].de)} a ${diaCurto(risco.itens[0].ate)}` : 'próximos 7 dias'

  return (
    <Cartao
      titulo="Risco meteorológico"
      subtitulo={`Condições do tempo favoráveis a pragas e doenças, ${periodo}, nos distritos com agricultores`}
      accoes={
        <div className="accoes">
          <Segmentos rotulo="Nível" valor={filtro} aoMudar={setFiltro}
            opcoes={[{ valor: 'todos', nome: 'Todos' }, { valor: 'ALTO', nome: 'Só risco alto' }]} />
          <Botao pequeno variante="fantasma" onClick={() => setVerRegras((v) => !v)} aria-expanded={verRegras}>
            <BookOpen size={14} />{verRegras ? 'Esconder regras' : 'Regras e fontes'}
          </Botao>
        </div>
      }
      semMargem
    >
      {risco?.erro && (
        <div style={{ padding: '12px 20px 0' }}>
          <div className="aviso-caixa aviso"><CircleAlert size={16} style={{ flex: 'none', marginTop: 2 }} />{risco.erro}</div>
        </div>
      )}
      {verRegras && risco && (
        <div className="regras-risco">
          <p className="suave pequeno" style={{ margin: 0 }}><Info size={13} style={{ verticalAlign: -2 }} /> {risco.aviso}</p>
          {risco.regras.map((g) => (
            <div key={`${g.cultura_id}-${g.classe}`}>
              <strong>{g.patologia_nome}</strong> <span className="suave">({catalogo.nomeCultura(g.cultura_id).toLowerCase()})</span>
              {g.evidencia === 'fraca' && <> <Etiqueta tom="neutro">Evidência fraca</Etiqueta></>}
              <p>{g.condicao}</p>
              <ul>{g.fontes.map((f) => <li key={f}>{f.startsWith('http') ? <a href={f} target="_blank" rel="noreferrer">{f}</a> : f}</li>)}</ul>
              {g.limiares_de_projecto.length > 0 && (
                <p className="suave pequeno">Limiares de projecto, a calibrar com os técnicos: {g.limiares_de_projecto.join('; ')}.</p>
              )}
            </div>
          ))}
        </div>
      )}
      {erro ? <div style={{ padding: 20 }}><div className="aviso-caixa critico"><CircleAlert size={16} />{erro.message}</div></div>
        : aCarregar ? <div style={{ padding: 20 }}><Esqueleto altura={120} /></div>
          : !risco || risco.distritos_com_agricultores === 0
            ? <Vazio titulo="Sem distritos para avaliar" texto="O risco calcula-se para os distritos da sua zona com agricultores registados." icone={<CloudRain size={28} />} />
            : itens.length === 0
              ? <Vazio titulo="Sem condições de risco" texto={`Nenhuma praga ou doença com tempo favorável em ${numero(risco.distritos_avaliados)} distrito(s) avaliado(s).`} icone={<CloudRain size={28} />} />
              : (
                <div className="tabela-envolvente"><table className="tabela">
                  <thead><tr><th>Praga ou doença</th><th>Distrito</th><th>Porquê</th><th>Nível</th><th /></tr></thead>
                  <tbody>
                    {itens.map((r) => (
                      <tr key={`${r.distrito_id}-${r.cultura_id}-${r.classe}`}>
                        <td className="celula-principal"><strong>{r.patologia_nome}</strong>
                          <span>{catalogo.nomeCultura(r.cultura_id)}{r.evidencia === 'fraca' ? ' · regra de evidência fraca' : ''}</span></td>
                        <td>{r.distrito}</td>
                        <td className="secundario" style={{ maxWidth: 360 }}>{r.motivo}</td>
                        <td><Etiqueta tom={NIVEL_RISCO[r.nivel].tom} icone={<CloudRain size={12} />}>{NIVEL_RISCO[r.nivel].nome}</Etiqueta></td>
                        <td style={{ width: 1 }}>{podeOperar && <Botao pequeno onClick={() => aoCriarAlerta(r)}><Megaphone size={14} />Criar alerta</Botao>}</td>
                      </tr>
                    ))}
                  </tbody>
                </table></div>
              )}
      {risco && risco.distritos_com_agricultores > 0 && (
        <p className="suave pequeno" style={{ margin: 0, padding: '10px 20px 14px', borderTop: '1px solid var(--linha)' }}>
          {risco.fonte} {risco.previsao_mais_antiga ? `Previsão obtida em ${dataHora(risco.previsao_mais_antiga)}.` : ''}{' '}
          {numero(risco.distritos_avaliados)} de {numero(risco.distritos_com_agricultores)} distrito(s) avaliado(s).
          Um sinal para decidir, não uma previsão da doença.
        </p>
      )}
    </Cartao>
  )
}
