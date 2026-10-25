import { Link } from 'react-router-dom'
import { CircleAlert, Megaphone, MessageSquareReply, ShieldAlert, ShieldCheck, Siren, TriangleAlert } from 'lucide-react'
import { data, numero, percentagem } from '@/nucleo/formatos'
import { NIVEL } from '@/nucleo/rotulos'
import { Botao, CabecalhoPagina, Campo, Cartao, Esqueleto, Etiqueta, Segmentos, Seleccao, Vazio } from '@/ui/componentes'
import { BarrasHorizontais, MapaDistritos } from '@/ui/graficos'
import { useCatalogo } from '@/viewmodels/referencias'
import { useVigilanciaViewModel, type Sensibilidade } from '@/viewmodels/useVigilanciaViewModel'

export function VigilanciaView() {
  const vm = useVigilanciaViewModel()
  const catalogo = useCatalogo()

  return (
    <>
      <CabecalhoPagina
        titulo="Vigilância"
        descricao="Onde estão as pragas e doenças, e onde estão a subir acima do habitual. Um sinal de surto é uma sugestão: o técnico decide se envia alerta."
      />
      {vm.declaracoes.length > 0 && (
        <div className="aviso-caixa critico">
          <ShieldAlert size={16} style={{ flex: 'none', marginTop: 2 }} />
          <span><b>{vm.declaracoes.length === 1 ? '1 caso' : `${numero(vm.declaracoes.length)} casos`} de declaração obrigatória</b> nos
            últimos {vm.periodo} dias ({vm.confirmadas === 1 ? '1 confirmado' : `${numero(vm.confirmadas)} confirmados`} pelo
            técnico). <a href="#declaracoes">Ver a lista</a>.</span>
        </div>
      )}
      <Cartao
        titulo="Sinais de surto"
        subtitulo={`Casos nos últimos ${vm.janela} dias comparados com a média das 4 semanas anteriores (mínimo ${vm.parametros.min_casos} casos, subida de ${String(vm.parametros.factor).replace('.', ',')}×)`}
        accoes={
          <div className="accoes">
            <Segmentos rotulo="Janela" valor={vm.janela} aoMudar={vm.setJanela} opcoes={[{ valor: 7, nome: '7 dias' }, { valor: 14, nome: '14 dias' }]} />
            <Segmentos rotulo="Sensibilidade" valor={vm.sensibilidade} aoMudar={(v: Sensibilidade) => vm.setSensibilidade(v)}
              opcoes={[{ valor: 'alta', nome: 'Sensível' }, { valor: 'normal', nome: 'Normal' }, { valor: 'baixa', nome: 'Conservador' }]} />
          </div>
        }
        semMargem
      >
        {vm.aCarregarSurtos ? <div style={{ padding: 20 }}><Esqueleto altura={120} /></div>
          : vm.surtos.length === 0 ? <Vazio titulo="Nenhum sinal de surto" texto="Nenhuma praga ou doença subiu acima do habitual com estes parâmetros." icone={<Siren size={28} />} /> : (
            <div className="tabela-envolvente"><table className="tabela">
              <thead><tr><th>Praga ou doença</th><th>Distrito</th><th className="numero">Casos recentes</th><th className="numero">Média habitual</th><th className="numero">Subida</th><th>Nível</th><th /></tr></thead>
              <tbody>
                {vm.surtos.map((s) => (
                  <tr key={`${s.distrito_id}-${s.cultura_id}-${s.classe}`}>
                    <td className="celula-principal"><strong>{s.patologia_nome}</strong><span>{catalogo.nomeCultura(s.cultura_id)}</span></td>
                    <td>{s.distrito}</td>
                    <td className="numero">{numero(s.casos_recentes)}</td>
                    <td className="numero">{numero(s.media_anterior)}</td>
                    <td className="numero">{s.razao === null ? <span className="suave">sem histórico</span> : `${String(s.razao).replace('.', ',')}×`}</td>
                    <td><Etiqueta tom={NIVEL[s.nivel].tom} icone={<TriangleAlert size={12} />}>{NIVEL[s.nivel].nome}</Etiqueta></td>
                    <td style={{ width: 1 }}><Botao pequeno onClick={() => vm.criarAlerta(s)}><Megaphone size={14} />Criar alerta</Botao></td>
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
        <Campo rotulo="Período">
          <Seleccao value={String(vm.periodo)} onChange={(e) => vm.setPeriodo(Number(e.target.value))}
            opcoes={[{ valor: '7', nome: 'Últimos 7 dias' }, { valor: '30', nome: 'Últimos 30 dias' }, { valor: '90', nome: 'Últimos 90 dias' }, { valor: '365', nome: 'Último ano' }]} />
        </Campo>
      </div>
      <div className="grelha grelha-principal">
        <Cartao titulo="Mapa de ocorrências" subtitulo={`${numero(vm.totalOcorrencias)} diagnósticos com estes filtros`}>
          {vm.aCarregarMapa ? <Esqueleto altura={460} /> : <MapaDistritos valores={vm.mapa} rotuloValor="Diagnósticos" />}
        </Cartao>
        <Cartao titulo="Distritos com mais casos">
          {vm.ranking.length ? <BarrasHorizontais itens={vm.ranking} /> : <Vazio titulo="Sem ocorrências" />}
        </Cartao>
      </div>

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
                        <td style={{ width: 1 }}>{d.estado === 'SUSPEITA' && <Link to="/validacao" className="pequeno">Validar</Link>}</td>
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
    </>
  )
}
