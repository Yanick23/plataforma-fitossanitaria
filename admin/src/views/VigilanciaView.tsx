import { Link } from 'react-router-dom'
import { useState } from 'react'
import { CircleAlert, CircleCheck, CircleSlash, Megaphone, MessageSquareReply, ShieldAlert, ShieldCheck, Siren, TriangleAlert } from 'lucide-react'
import { data, dataHora, numero, percentagem } from '@/nucleo/formatos'
import { NIVEL } from '@/nucleo/rotulos'
import { Botao, CabecalhoPagina, Campo, Cartao, Esqueleto, Etiqueta, Gaveta, Segmentos, Seleccao, Vazio } from '@/ui/componentes'
import { BarrasHorizontais, LinhasSemanais, MapaDistritos } from '@/ui/graficos'
import { useCatalogo } from '@/viewmodels/referencias'
import { useVigilanciaViewModel, type Sensibilidade } from '@/viewmodels/useVigilanciaViewModel'
import { CartaoRiscoMeteo } from './CartaoRiscoMeteo'

export function VigilanciaView() {
  const vm = useVigilanciaViewModel()
  const catalogo = useCatalogo()
  const [notaDescarte, setNotaDescarte] = useState('')

  return (
    <>
      <CabecalhoPagina
        titulo="Vigilância"
        descricao="Onde estão as pragas e doenças, onde estão a subir acima do habitual e onde o tempo as vai favorecer. Cada sinal é uma sugestão: o técnico decide se envia alerta."
      />
      {vm.declaracoes.length > 0 && (
        <div className="aviso-caixa critico">
          <ShieldAlert size={16} style={{ flex: 'none', marginTop: 2 }} />
          <span><b>{vm.declaracoes.length === 1 ? '1 caso' : `${numero(vm.declaracoes.length)} casos`} de declaração obrigatória</b> nos
            últimos {vm.periodo} dias ({vm.confirmadas === 1 ? '1 confirmado' : `${numero(vm.confirmadas)} confirmados`} pelo
            técnico). <a href="#declaracoes">Ver a lista</a>.</span>
        </div>
      )}
      <CartaoRiscoMeteo risco={vm.risco} aCarregar={vm.aCarregarRisco} erro={vm.erroRisco} podeOperar={vm.podeOperar}
        aoCriarAlerta={vm.criarAlertaRisco} />
      <Cartao
        titulo="Sinais de surto"
        subtitulo={`Casos nos últimos ${vm.janela} dias comparados com a média das 4 semanas anteriores (mínimo ${vm.parametros.min_casos} casos, subida de ${String(vm.parametros.factor).replace('.', ',')}×)`}
        accoes={
          <div className="accoes">
            <Segmentos rotulo="Janela" valor={vm.janela} aoMudar={vm.setJanela} opcoes={[{ valor: 7, nome: '7 dias' }, { valor: 14, nome: '14 dias' }]} />
            <Segmentos rotulo="Sensibilidade" valor={vm.sensibilidade} aoMudar={(v: Sensibilidade) => vm.setSensibilidade(v)}
              opcoes={[{ valor: 'alta', nome: 'Sensível' }, { valor: 'normal', nome: 'Normal' }, { valor: 'baixa', nome: 'Conservador' }]} />
            {vm.descartados > 0 && (
              <label className="pequeno" style={{ display: 'inline-flex', gap: 6, alignItems: 'center' }}>
                <input type="checkbox" checked={vm.mostrarDescartados} onChange={(e) => vm.setMostrarDescartados(e.target.checked)} />
                Mostrar descartados ({numero(vm.descartados)})
              </label>
            )}
          </div>
        }
        semMargem
      >
        {vm.aCarregarSurtos ? <div style={{ padding: 20 }}><Esqueleto altura={120} /></div>
          : vm.surtos.length === 0 ? <Vazio titulo="Nenhum sinal de surto" texto="Nenhuma praga ou doença subiu acima do habitual com estes parâmetros." icone={<Siren size={28} />} /> : (
            <div className="tabela-envolvente"><table className="tabela">
              <thead><tr><th>Praga ou doença</th><th>Distrito</th><th className="numero">Casos recentes</th><th className="numero">Média habitual</th><th className="numero">Subida</th><th>Nível</th><th>Decisão</th><th /></tr></thead>
              <tbody>
                {vm.surtos.map((s) => (
                  <tr key={`${s.distrito_id}-${s.cultura_id}-${s.classe}`} style={{ opacity: s.decisao === 'DESCARTADO' ? 0.55 : 1 }}>
                    <td className="celula-principal"><strong>{s.patologia_nome}</strong><span>{catalogo.nomeCultura(s.cultura_id)}</span></td>
                    <td>{s.distrito}</td>
                    <td className="numero">{numero(s.casos_recentes)}</td>
                    <td className="numero">{numero(s.media_anterior)}</td>
                    <td className="numero">{s.razao === null ? <span className="suave">sem histórico</span> : `${String(s.razao).replace('.', ',')}×`}</td>
                    <td><Etiqueta tom={NIVEL[s.nivel].tom} icone={<TriangleAlert size={12} />}>{NIVEL[s.nivel].nome}</Etiqueta></td>
                    <td className="celula-principal" title={s.decisao_nota ?? undefined}>
                      {s.decisao === null ? <span className="suave">Por decidir</span> : (
                        <>
                          <Etiqueta tom={s.decisao === 'CONFIRMADO' ? 'aviso' : 'neutro'}
                            icone={s.decisao === 'CONFIRMADO' ? <CircleCheck size={12} /> : <CircleSlash size={12} />}>
                            {s.decisao === 'CONFIRMADO' ? 'Confirmado' : 'Descartado'}
                          </Etiqueta>
                          <span>{s.decidido_por}{s.decidido_em ? ` · ${dataHora(s.decidido_em)}` : ''}</span>
                          {s.decisao_nota && <span>«{s.decisao_nota}»</span>}
                        </>
                      )}
                    </td>
                    <td style={{ width: 1, whiteSpace: 'nowrap' }}>
                      {vm.podeOperar && (s.decisao === null ? (
                        <div style={{ display: 'flex', gap: 6 }}>
                          <Botao pequeno variante="primario" disabled={vm.aDecidir} onClick={() => vm.confirmar(s)}
                            title="Confirmar o surto e preparar um alerta para o distrito"><Megaphone size={14} />Confirmar</Botao>
                          <Botao pequeno disabled={vm.aDecidir} onClick={() => { setNotaDescarte(''); vm.abrirDescarte(s) }}
                            title="Falso alarme (ex.: fotografias repetidas)"><CircleSlash size={14} />Descartar</Botao>
                        </div>
                      ) : s.decisao === 'CONFIRMADO' && <Botao pequeno onClick={() => vm.criarAlerta(s)}><Megaphone size={14} />Criar alerta</Botao>)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table></div>
          )}
      </Cartao>

      <div className="filtros">
        <Campo rotulo="Cultura">
          <Seleccao vazio="Todas" value={vm.cultura} onChange={(e) => vm.setCultura(e.target.value)} opcoes={catalogo.culturas.map((c) => ({ valor: c.id, nome: c.nome }))} />
        </Campo>
        <Campo rotulo="Praga ou doença">
          <Seleccao vazio="Todas" value={vm.classe} disabled={!vm.cultura} onChange={(e) => vm.setClasse(e.target.value)}
            opcoes={catalogo.patologiasDe(vm.cultura).map((p) => ({ valor: p.codigo, nome: p.nome_local }))} />
        </Campo>
        <Campo rotulo="Confiança do modelo">
          <Seleccao vazio="Todas" value={vm.confianca} onChange={(e) => vm.setConfianca(e.target.value as '' | 'alta' | 'baixa')}
            opcoes={[{ valor: 'alta', nome: '60% ou mais' }, { valor: 'baixa', nome: 'Abaixo de 60%' }]} />
        </Campo>
        <Campo rotulo="Período">
          <Seleccao value={String(vm.periodo)} onChange={(e) => vm.setPeriodo(Number(e.target.value))}
            opcoes={[{ valor: '7', nome: 'Últimos 7 dias' }, { valor: '30', nome: 'Últimos 30 dias' }, { valor: '90', nome: 'Últimos 90 dias' }, { valor: '365', nome: 'Último ano' }]} />
        </Campo>
      </div>
      <div className="grelha grelha-principal">
        <Cartao titulo="Mapa de ocorrências" subtitulo={`${numero(vm.totalOcorrencias)} diagnósticos com estes filtros`}>
          {vm.aCarregarMapa ? <Esqueleto altura={460} /> : <MapaDistritos valores={vm.mapa} rotuloValor="Diagnósticos" />}
        </Cartao>
        <Cartao titulo="Distritos com mais casos" subtitulo="▲ / ▼: diferença entre os últimos 7 dias e os 7 anteriores">
          {vm.ranking.length ? <BarrasHorizontais itens={vm.ranking} /> : <Vazio titulo="Sem ocorrências" />}
        </Cartao>
      </div>

      <Cartao titulo="Tendência semana a semana" subtitulo="Diagnósticos por semana (segunda a domingo) nas últimas 8 semanas, com a cultura, a praga e a confiança escolhidas">
        {vm.aCarregarTendencia ? <Esqueleto altura={220} /> : (
          <LinhasSemanais semanas={vm.tendencia.semanas} series={vm.tendencia.series} formatar={numero}
            rotulo="Diagnósticos por semana nas últimas 8 semanas" />
        )}
      </Cartao>

      <div id="declaracoes">
        <Cartao titulo="Pragas e doenças de declaração obrigatória"
          subtitulo={`Últimos ${vm.periodo} dias. Confirmado: validado pelo técnico. Suspeita: só identificado pela app, precisa de verificação no campo.`} semMargem>
          {vm.aCarregarDeclaracoes ? <div style={{ padding: 20 }}><Esqueleto altura={100} /></div>
            : vm.declaracoes.length === 0 ? <Vazio titulo="Nenhum caso" texto="As pragas marcadas como de declaração obrigatória no catálogo aparecem aqui quando forem diagnosticadas." icone={<ShieldCheck size={28} />} /> : (
              <div className="tabela-envolvente">
                <table className="tabela">
                  <thead><tr><th>Data</th><th>Praga ou doença</th><th>Distrito</th><th>Estado</th><th className="numero">Confiança</th><th>Agricultor</th><th /></tr></thead>
                  <tbody>
                    {vm.declaracoes.map((d) => (
                      <tr key={d.diagnostico_id}>
                        <td className="secundario">{data(d.data)}</td>
                        <td className="celula-principal"><strong>{d.patologia_nome}</strong><span>{catalogo.nomeCultura(d.cultura_id)}</span></td>
                        <td>{d.distrito_nome ?? '—'}</td>
                        <td>{d.estado === 'CONFIRMADO'
                          ? <Etiqueta tom="critico" icone={<ShieldAlert size={12} />}>Confirmado</Etiqueta>
                          : <Etiqueta tom="aviso" icone={<CircleAlert size={12} />}>Suspeita</Etiqueta>}</td>
                        <td className="numero">{percentagem(d.confianca)}</td>
                        <td className="celula-principal"><strong style={{ fontWeight: 400 }}>{d.agricultor_nome}</strong><span className="mono">{d.agricultor_telefone}</span></td>
                        <td style={{ width: 1 }}>{d.estado === 'SUSPEITA' && vm.podeOperar && <Link to="/validacao" className="pequeno">Validar</Link>}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
        </Cartao>
      </div>

      <Cartao titulo="Eficácia das recomendações"
        subtitulo={`Respostas dos agricultores dias depois do diagnóstico (últimos ${vm.periodo} dias). Eficácia = melhoraram ÷ seguiram a recomendação, total ou parcialmente.`} semMargem>
        {vm.aCarregarEficacia ? <div style={{ padding: 20 }}><Esqueleto altura={100} /></div>
          : vm.eficacia.length === 0 ? <Vazio titulo="Ainda sem respostas" texto="A app pergunta ao agricultor, alguns dias depois, se seguiu a recomendação e se a planta melhorou." icone={<MessageSquareReply size={28} />} /> : (
            <div className="tabela-envolvente">
              <table className="tabela">
                <thead><tr><th>Praga ou doença</th><th className="numero">Respostas</th><th className="numero">Seguiram</th><th className="numero">Melhoraram</th><th style={{ width: '30%' }}>Eficácia</th></tr></thead>
                <tbody>
                  {vm.eficacia.map((e) => (
                    <tr key={`${e.cultura_id}-${e.classe}`}>
                      <td className="celula-principal"><strong>{e.nome}</strong><span>{catalogo.nomeCultura(e.cultura_id)}</span></td>
                      <td className="numero">{numero(e.respostas)}</td>
                      <td className="numero">{numero(e.seguiram)}</td>
                      <td className="numero">{numero(e.melhoraram)}</td>
                      <td>
                        {e.eficacia === null ? <span className="suave">ninguém seguiu</span> : (
                          <div className="barra-item">
                            <span className="nome">{e.seguiram < 5 ? 'poucas respostas' : ''}</span>
                            <span className="valor">{percentagem(e.eficacia)}</span>
                            <div className="trilho"><div className="enchimento" style={{ width: `${e.eficacia * 100}%` }} /></div>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </Cartao>
      <Gaveta
        aberta={Boolean(vm.aDescartar)}
        titulo="Descartar sinal de surto"
        subtitulo={vm.aDescartar ? `${vm.aDescartar.patologia_nome} em ${vm.aDescartar.distrito}` : undefined}
        aoFechar={vm.fecharDescarte}
        rodape={
          <>
            <Botao onClick={vm.fecharDescarte}>Cancelar</Botao>
            <Botao variante="primario" disabled={vm.aDecidir} onClick={() => vm.descartar(notaDescarte)}>
              <CircleSlash size={15} />{vm.aDecidir ? 'A guardar…' : 'Descartar'}
            </Botao>
          </>
        }
      >
        <div className="formulario">
          <p className="secundario" style={{ margin: 0 }}>
            O sinal deixa de aparecer nesta janela e a decisão fica na auditoria. Se os casos continuarem a subir, aparece um sinal novo.
          </p>
          <Campo rotulo="Porquê? (opcional)">
            <textarea className="entrada" rows={3} maxLength={500} value={notaDescarte} onChange={(e) => setNotaDescarte(e.target.value)}
              placeholder="Ex.: fotografias repetidas da mesma planta; confirmado no terreno que não há praga." />
          </Campo>
        </div>
      </Gaveta>
    </>
  )
}
