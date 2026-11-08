import { CalendarDays, CircleAlert, Info, Sprout } from 'lucide-react'
import { CabecalhoPagina, Cartao, Esqueleto, Etiqueta, Seleccao } from '@/ui/componentes'
import { useCalendarioViewModel } from '@/viewmodels/useCalendarioViewModel'
import { useCatalogo } from '@/viewmodels/referencias'

const MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro',
  'Novembro', 'Dezembro']

/** Calendário agrícola por província (funcionalidade 10): o que a app mostra em «Nesta altura…». */
export function CalendarioView() {
  const vm = useCalendarioViewModel()
  const catalogo = useCatalogo()
  const c = vm.calendario
  const numeroFonte = (id: string) => (c ? c.fontes.findIndex((f) => f.id === id) + 1 : 0)

  return (
    <>
      <CabecalhoPagina
        titulo="Calendário agrícola"
        descricao="Actividades do ano típico, época de sementeira e o que vigiar em cada mês. A app mostra ao agricultor o mês actual da sua província («Nesta altura…»), mesmo sem Internet."
        accoes={<Seleccao value={vm.provincia} onChange={(e) => vm.setProvincia(e.target.value)} opcoes={vm.opcoesProvincias} style={{ width: 220 }} />}
      />
      {vm.erro ? <div className="aviso-caixa critico"><CircleAlert size={16} />{vm.erro.message}</div>
        : vm.aCarregar || !c ? <Esqueleto altura={400} /> : (
          <>
            <div className="aviso-caixa info"><Info size={16} style={{ flex: 'none', marginTop: 2 }} />{c.aviso}</div>
            <Cartao
              titulo={`${c.provincia} · região ${c.regiao}`}
              subtitulo={c.sementeira ? `Sementeira habitual: ${c.sementeira} [${numeroFonte('MASA2018')}]` : undefined}
              semMargem
            >
              <div className="tabela-envolvente"><table className="tabela calendario">
                <thead><tr><th>Mês</th><th>Actividades [{numeroFonte('FEWS2013')}]</th><th>O que vigiar</th></tr></thead>
                <tbody>
                  {c.meses.map((m) => (
                    <tr key={m.mes} className={m.mes === vm.mesActual ? 'mes-actual' : undefined}>
                      <td style={{ whiteSpace: 'nowrap' }}>
                        <strong>{MESES[m.mes - 1]}</strong>
                        {m.mes === vm.mesActual && <div><Etiqueta tom="marca" icone={<CalendarDays size={12} />}>Este mês</Etiqueta></div>}
                      </td>
                      <td className="secundario">{m.actividades.join(' · ')}</td>
                      <td>
                        {m.avisos.length === 0 ? <span className="suave">—</span> : (
                          <ul className="avisos-mes">
                            {m.avisos.map((a, i) => (
                              <li key={i}>
                                <Sprout size={13} style={{ flex: 'none', marginTop: 3 }} />
                                <span>
                                  <b>{catalogo.nomeCultura(a.cultura_id)}{a.patologia_nome ? ` · ${a.patologia_nome}` : ''}:</b> {a.texto}{' '}
                                  <span className="suave pequeno">[{a.fontes.map(numeroFonte).join(', ')}] · confiança {a.confianca === 'alta' ? 'alta' : 'média'}</span>
                                </span>
                              </li>
                            ))}
                          </ul>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table></div>
            </Cartao>
            <Cartao titulo="Fontes">
              <ol className="fontes-calendario">
                {c.fontes.map((f) => (
                  <li key={f.id}>{f.referencia}{f.url && <> <a href={f.url} target="_blank" rel="noreferrer">{f.url}</a></>}</li>
                ))}
              </ol>
            </Cartao>
          </>
        )}
    </>
  )
}
