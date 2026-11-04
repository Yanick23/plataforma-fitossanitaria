import { Link } from 'react-router-dom'
import { ArrowDownRight, ArrowUpRight, CircleAlert, Siren, TriangleAlert } from 'lucide-react'
import { compacto, numero, percentagem, relativo } from '@/nucleo/formatos'
import { NIVEL } from '@/nucleo/rotulos'
import { CabecalhoPagina, Cartao, Confianca, Esqueleto, Etiqueta, Indicador, Segmentos, Vazio } from '@/ui/componentes'
import { BarrasHorizontais, ColunasDiarias, MapaDistritos } from '@/ui/graficos'
import { useCatalogo } from '@/viewmodels/referencias'
import { usePainelViewModel, type Periodo } from '@/viewmodels/usePainelViewModel'

const PERIODOS: { valor: Periodo; nome: string }[] = [
  { valor: 7, nome: '7 dias' }, { valor: 30, nome: '30 dias' }, { valor: 90, nome: '90 dias' },
]

export function PainelView() {
  const vm = usePainelViewModel()
  const catalogo = useCatalogo()
  const r = vm.resumo
  const d = vm.derivados

  if (vm.erro) return <div className="aviso-caixa critico"><CircleAlert size={16} />{vm.erro.message}</div>

  return (
    <>
      <CabecalhoPagina
        titulo="Painel"
        descricao={r ? `Situação fitossanitária em ${r.zona}, nos últimos ${vm.periodo} dias.` : ' '}
        accoes={<Segmentos rotulo="Período" valor={vm.periodo} opcoes={PERIODOS} aoMudar={vm.setPeriodo} />}
      />

      <div className="grelha grelha-4">
        {r && d ? (
          <>
            <Indicador
              rotulo="Diagnósticos no período"
              valor={compacto(r.diagnosticos_30d)}
              variacao={d.variacao === null
                ? <span className="variacao">{numero(r.diagnosticos)} desde o início</span>
                : <span className={`variacao ${d.variacao >= 0 ? 'sobe-bom' : 'desce'}`}>
                  {d.variacao >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                  {percentagem(Math.abs(d.variacao))} face aos {vm.periodo} dias anteriores
                </span>}
            />
            <Indicador
              rotulo="Agricultores registados"
              valor={compacto(r.agricultores)}
              variacao={<span className="variacao">+{numero(r.agricultores_novos_30d)} no período · {numero(r.tecnicos)} técnicos</span>}
            />
            <Indicador
              rotulo="Distritos com pragas ou doenças"
              valor={numero(d.distritosComCasos)}
              variacao={<span className="variacao">{numero(vm.surtos.length)} sinais de surto activos</span>}
            />
            <Indicador
              rotulo="Confiança abaixo de 60%"
              valor={numero(r.confianca_baixa_30d)}
              variacao={<span className="variacao">{percentagem(d.taxaBaixa)} dos diagnósticos · {numero(vm.totalPorValidar)} por validar</span>}
            />
          </>
        ) : (
          [0, 1, 2, 3].map((i) => <div key={i} className="cartao indicador"><Esqueleto altura={14} largura="60%" /><Esqueleto altura={34} largura="40%" /></div>)
        )}
      </div>

      <div className="grelha grelha-principal">
        <Cartao titulo="Diagnósticos por dia" subtitulo="Folhas com doença ou praga, por data do diagnóstico">
          {r ? <ColunasDiarias dados={r.por_dia} /> : <Esqueleto altura={240} />}
        </Cartao>
        <Cartao titulo="Pragas e doenças mais frequentes" subtitulo={`Diagnósticos nos últimos ${vm.periodo} dias`}>
          {d ? (d.ranking.length ? <BarrasHorizontais itens={d.ranking} /> : <Vazio titulo="Sem casos no período" />) : <Esqueleto altura={240} />}
        </Cartao>
      </div>

      <div className="grelha grelha-principal">
        <Cartao titulo="Ocorrências por distrito" subtitulo="Diagnósticos de pragas e doenças no período; passe o rato para ver o detalhe">
          {d ? <MapaDistritos valores={d.mapa} rotuloValor="Pragas e doenças" /> : <Esqueleto altura={460} />}
        </Cartao>
        <div className="grelha" style={{ alignContent: 'start' }}>
          <Cartao titulo="Sinais de surto" subtitulo="Subidas acima do habitual nos últimos 7 dias" semMargem>
            {vm.surtos.length === 0 ? (
              <Vazio titulo="Nenhum sinal de surto" texto="Nenhuma praga ou doença subiu acima do habitual." icone={<Siren size={24} />} />
            ) : (
              <table className="tabela">
                <tbody>
                  {vm.surtos.slice(0, 5).map((s) => (
                    <tr key={`${s.distrito_id}-${s.cultura_id}-${s.classe}`}>
                      <td className="celula-principal">
                        <strong>{s.patologia_nome}</strong>
                        <span>{s.distrito} · {catalogo.nomeCultura(s.cultura_id)}</span>
                      </td>
                      <td className="numero">{numero(s.casos_recentes)} casos<div className="suave pequeno">média {numero(s.media_anterior)}</div></td>
                      <td style={{ width: 1 }}>
                        <Etiqueta tom={NIVEL[s.nivel].tom} icone={<TriangleAlert size={12} />}>{NIVEL[s.nivel].nome}</Etiqueta>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Cartao>
          <Cartao titulo="Menos certos, por validar" subtitulo="O técnico confirma ou corrige" semMargem
            accoes={<Link to="/diagnosticos" className="pequeno">Ver todos</Link>}>
            {vm.porValidar.length === 0 ? <Vazio titulo="Nada por validar" /> : (
              <table className="tabela">
                <tbody>
                  {vm.porValidar.map((x) => (
                    <tr key={x.id}>
                      <td className="celula-principal">
                        <strong>{x.patologia_nome ?? x.classe_prevista}</strong>
                        <span>{x.utilizador_nome} · {x.distrito_nome ?? 'sem distrito'} · {relativo(x.data)}</span>
                      </td>
                      <td className="numero"><Confianca valor={x.confianca} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Cartao>
        </div>
      </div>
    </>
  )
}
