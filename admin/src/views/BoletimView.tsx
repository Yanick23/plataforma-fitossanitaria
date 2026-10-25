import type { ReactNode } from 'react'
import { CircleAlert, Download, Printer, ShieldAlert, TriangleAlert } from 'lucide-react'
import { data, dataHora, numero, percentagem } from '@/nucleo/formatos'
import { LIMIAR_CONFIANCA, NIVEL } from '@/nucleo/rotulos'
import { useSessao } from '@/nucleo/sessao'
import { Botao, Campo, Esqueleto, Etiqueta, Segmentos } from '@/ui/componentes'
import { BarrasHorizontais } from '@/ui/graficos'
import { useCatalogo } from '@/viewmodels/referencias'
import { useBoletimViewModel, type Predefinido } from '@/viewmodels/useBoletimViewModel'

const PREDEFINIDOS: { valor: Predefinido; nome: string }[] = [
  { valor: '7', nome: '7 dias' }, { valor: '30', nome: '30 dias' }, { valor: '90', nome: '90 dias' },
  { valor: 'mes', nome: 'Mês anterior' }, { valor: 'outro', nome: 'Outro' },
]

function Seccao({ numero: n, titulo, nota, children }: { numero: number; titulo: string; nota?: string; children: ReactNode }) {
  return (
    <section className="boletim-seccao">
      <h2><span className="boletim-n">{n}</span>{titulo}</h2>
      {nota && <p className="suave pequeno boletim-nota">{nota}</p>}
      {children}
    </section>
  )
}

/** A API devolve o período em UTC (fim às 23:59:59); mostra-se o dia pedido, sem conversão de fuso. */
const dia = (iso: string) => data(`${iso.slice(0, 10)}T12:00:00`)

const SemRegistos = ({ texto = 'Sem registos no período.' }: { texto?: string }) => <p className="suave">{texto}</p>

function Numero({ rotulo, valor, detalhe }: { rotulo: string; valor: ReactNode; detalhe?: ReactNode }) {
  return (
    <div className="boletim-numero">
      <dt>{rotulo}</dt>
      <dd>{valor}</dd>
      {detalhe && <dd className="suave pequeno">{detalhe}</dd>}
    </div>
  )
}

export function BoletimView() {
  const vm = useBoletimViewModel()
  const { utilizador } = useSessao()
  const catalogo = useCatalogo()
  const b = vm.boletim

  return (
    <>
      <div className="cabecalho-pagina nao-imprimir">
        <div>
          <h1>Boletim fitossanitário</h1>
          <p>Resumo da situação das pragas e doenças na sua zona, pronto a imprimir ou guardar em PDF.</p>
        </div>
        <div className="accoes">
          <Botao onClick={vm.descarregarCsv} disabled={vm.invalido || vm.aDescarregar}><Download size={16} />{vm.aDescarregar ? 'A preparar…' : 'CSV'}</Botao>
          <Botao variante="primario" onClick={vm.imprimir} disabled={!b || vm.invalido}><Printer size={16} />Imprimir ou PDF</Botao>
        </div>
      </div>

      <div className="cartao nao-imprimir" style={{ padding: '16px 20px' }}>
        <div className="filtros" style={{ alignItems: 'flex-end' }}>
          <div className="campo" style={{ width: 'auto' }}>
            <span>Período</span>
            <Segmentos rotulo="Período" valor={vm.predefinido} opcoes={PREDEFINIDOS} aoMudar={vm.escolher} />
          </div>
          <Campo rotulo="De">
            <input className="entrada" type="date" value={vm.periodo.inicio} max={vm.periodo.fim} onChange={(e) => vm.mudarData('inicio', e.target.value)} />
          </Campo>
          <Campo rotulo="Até" erro={vm.invalido ? 'A data final é anterior à inicial' : null}>
            <input className="entrada" type="date" value={vm.periodo.fim} min={vm.periodo.inicio} onChange={(e) => vm.mudarData('fim', e.target.value)} />
          </Campo>
          {vm.aActualizar && b && <span className="suave pequeno" style={{ paddingBottom: 10 }}>A actualizar…</span>}
        </div>
      </div>

      {vm.erro ? <div className="aviso-caixa critico"><CircleAlert size={16} />{vm.erro.message}</div>
        : !b ? <div className="cartao" style={{ padding: 32 }}><Esqueleto altura={28} largura="45%" /><br /><Esqueleto altura={320} /></div> : (
          <article className="boletim cartao" aria-label="Boletim fitossanitário">
            <header className="boletim-cabecalho">
              <div className="boletim-marca">
                <img src="/marca.svg" alt="" width={28} height={28} />
                <span>Plataforma de Vigilância Fitossanitária · Milho e mandioca</span>
              </div>
              <h1>Boletim fitossanitário</h1>
              <p className="boletim-zona">{b.zona}</p>
              <dl className="boletim-meta">
                <div><dt>Período</dt><dd>{dia(b.inicio)} a {dia(b.fim)}</dd></div>
                <div><dt>Gerado em</dt><dd>{dataHora(b.gerado_em)}</dd></div>
                {utilizador && <div><dt>Preparado por</dt><dd>{utilizador.nome}</dd></div>}
              </dl>
            </header>

            <Seccao numero={1} titulo="Síntese">
              {vm.paragrafos.map((p) => <p key={p} className="boletim-texto">{p}</p>)}
            </Seccao>

            <Seccao numero={2} titulo="Indicadores do período">
              <dl className="boletim-numeros">
                <Numero rotulo="Diagnósticos" valor={numero(b.diagnosticos)} detalhe={`${numero(b.diagnosticos_pragas_doencas)} com praga ou doença`} />
                <Numero rotulo="Agricultores activos" valor={numero(b.agricultores_activos)} detalhe={`${numero(b.agricultores_novos)} registados no período`} />
                <Numero rotulo={`Confiança abaixo de ${percentagem(LIMIAR_CONFIANCA)}`} valor={percentagem(b.taxa_confianca_baixa)} detalhe="dos diagnósticos" />
                <Numero rotulo="Exactidão em campo" valor={percentagem(b.exactidao_campo)} detalhe={b.validados === 1 ? '1 validado pelo técnico' : `${numero(b.validados)} validados pelo técnico`} />
                <Numero rotulo="Alertas emitidos" valor={numero(b.alertas_enviados)} />
                <Numero rotulo="Sinais de surto" valor={numero(b.surtos.length)} />
                <Numero rotulo="Visitas técnicas" valor={`${numero(b.visitas_resolvidas)} de ${numero(b.visitas_pedidas)}`} detalhe="resolvidas" />
                <Numero rotulo="Tempo até resolver" valor={b.dias_medios_resolucao === null ? '—' : `${numero(b.dias_medios_resolucao)} dias`} detalhe="média das visitas resolvidas" />
              </dl>
            </Seccao>

            <div className="boletim-duas">
              <Seccao numero={3} titulo="Principais pragas e doenças" nota="Número de diagnósticos; conta a classe corrigida pelo técnico quando existe.">
                {b.principais_pragas.length
                  ? <BarrasHorizontais itens={b.principais_pragas.map((l) => ({ chave: l.nome, nome: l.nome, valor: l.valor }))} />
                  : <SemRegistos />}
              </Seccao>
              <Seccao numero={4} titulo="Distritos mais afectados" nota="Diagnósticos de pragas e doenças por distrito do agricultor.">
                {b.distritos_mais_afectados.length
                  ? <BarrasHorizontais itens={b.distritos_mais_afectados.map((l) => ({ chave: l.nome, nome: l.nome, valor: l.valor }))} />
                  : <SemRegistos />}
              </Seccao>
            </div>

            <Seccao numero={5} titulo="Sinais de surto" nota="Casos dos últimos 7 dias do período contra a média semanal das 4 semanas anteriores.">
              {b.surtos.length === 0 ? <SemRegistos texto="Nenhuma praga ou doença subiu acima do habitual." /> : (
                <div className="tabela-envolvente"><table className="tabela">
                  <thead><tr><th>Praga ou doença</th><th>Distrito</th><th className="numero">Casos (7 dias)</th><th className="numero">Média anterior</th><th className="numero">Subida</th><th>Nível</th></tr></thead>
                  <tbody>
                    {b.surtos.map((s) => (
                      <tr key={`${s.distrito_id}-${s.cultura_id}-${s.classe}`}>
                        <td className="celula-principal"><strong>{s.patologia_nome}</strong><span>{catalogo.nomeCultura(s.cultura_id)}</span></td>
                        <td>{s.distrito}</td>
                        <td className="numero">{numero(s.casos_recentes)}</td>
                        <td className="numero">{numero(s.media_anterior)}</td>
                        <td className="numero">{s.razao === null ? 'novo' : `${numero(s.razao)}×`}</td>
                        <td><Etiqueta tom={NIVEL[s.nivel].tom} icone={<TriangleAlert size={12} />}>{NIVEL[s.nivel].nome}</Etiqueta></td>
                      </tr>
                    ))}
                  </tbody>
                </table></div>
              )}
            </Seccao>

            <Seccao numero={6} titulo="Pragas e doenças de declaração obrigatória"
              nota="Confirmado: validado pelo técnico. Suspeita: só identificado pela app; precisa de verificação no campo.">
              {b.declaracoes.length === 0 ? <SemRegistos texto="Nenhum caso de declaração obrigatória no período." /> : (
                <div className="tabela-envolvente"><table className="tabela">
                  <thead><tr><th>Data</th><th>Praga ou doença</th><th>Distrito</th><th>Estado</th><th className="numero">Confiança</th><th>Agricultor</th></tr></thead>
                  <tbody>
                    {b.declaracoes.map((d) => (
                      <tr key={d.diagnostico_id}>
                        <td>{data(d.data)}</td>
                        <td className="celula-principal"><strong>{d.patologia_nome}</strong><span>{catalogo.nomeCultura(d.cultura_id)}</span></td>
                        <td>{d.distrito_nome ?? '—'}</td>
                        <td>{d.estado === 'CONFIRMADO'
                          ? <Etiqueta tom="critico" icone={<ShieldAlert size={12} />}>Confirmado</Etiqueta>
                          : <Etiqueta tom="aviso" icone={<CircleAlert size={12} />}>Suspeita</Etiqueta>}</td>
                        <td className="numero">{percentagem(d.confianca)}</td>
                        {/* O telefone fica só no ecrã: um boletim impresso circula. */}
                        <td className="celula-principal"><strong style={{ fontWeight: 400 }}>{d.agricultor_nome}</strong><span className="so-ecra mono">{d.agricultor_telefone}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table></div>
              )}
            </Seccao>

            <Seccao numero={7} titulo="Alertas emitidos">
              {b.alertas.length === 0 ? <SemRegistos texto="Nenhum alerta emitido no período." /> : (
                <div className="tabela-envolvente"><table className="tabela">
                  <thead><tr><th>Data</th><th>Alerta</th><th>Destino</th><th>Nível</th><th className="numero">Lido por</th></tr></thead>
                  <tbody>
                    {b.alertas.map((a) => (
                      <tr key={a.id}>
                        <td>{data(a.criado_em)}</td>
                        <td className="celula-principal"><strong>{a.titulo}</strong>{a.patologia_nome && <span>{a.patologia_nome}</span>}</td>
                        <td>{a.zona}</td>
                        <td><Etiqueta tom={NIVEL[a.nivel].tom}>{NIVEL[a.nivel].nome}</Etiqueta></td>
                        <td className="numero">{numero(a.lidos)} de {numero(a.destinatarios)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table></div>
              )}
            </Seccao>

            <Seccao numero={8} titulo="Eficácia das recomendações"
              nota="Resposta dos agricultores dias depois do diagnóstico. Eficácia = melhoraram ÷ seguiram (total ou parcialmente) a recomendação.">
              {b.eficacia.length === 0 ? <SemRegistos texto="Ainda não há respostas dos agricultores neste período." /> : (
                <div className="tabela-envolvente"><table className="tabela">
                  <thead><tr><th>Praga ou doença</th><th className="numero">Respostas</th><th className="numero">Seguiram</th><th className="numero">Melhoraram</th><th className="numero">Eficácia</th></tr></thead>
                  <tbody>
                    {b.eficacia.map((e) => (
                      <tr key={`${e.cultura_id}-${e.classe}`}>
                        <td className="celula-principal"><strong>{e.nome}</strong><span>{catalogo.nomeCultura(e.cultura_id)}</span></td>
                        <td className="numero">{numero(e.respostas)}</td>
                        <td className="numero">{numero(e.seguiram)}</td>
                        <td className="numero">{numero(e.melhoraram)}</td>
                        <td className="numero">{percentagem(e.eficacia)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table></div>
              )}
            </Seccao>

            <footer className="boletim-rodape">
              <h2>Notas sobre os dados</h2>
              <ul>
                <li>Os dados vêm dos diagnósticos feitos pelos agricultores na aplicação móvel e sincronizados com o servidor; diagnósticos ainda não sincronizados não entram.</li>
                <li>Cada diagnóstico conta no distrito em que o agricultor estava registado quando o sincronizou.</li>
                <li>Quando um técnico corrigiu o diagnóstico, conta a classe corrigida.</li>
                <li>Exactidão em campo: proporção dos diagnósticos validados em que o técnico confirmou a classe prevista pela app.</li>
                <li>Um sinal de surto exige pelo menos 3 casos em 7 dias e o dobro da média anterior; é urgente a partir de 4 vezes a média.</li>
              </ul>
            </footer>
          </article>
        )}
    </>
  )
}
