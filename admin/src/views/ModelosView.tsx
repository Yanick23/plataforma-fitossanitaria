import { Activity, Boxes, CircleAlert, CircleCheck, FileUp, FlaskConical, Lock, ShieldCheck, TriangleAlert, Upload } from 'lucide-react'
import { bytes, dataHora, numero, percentagem } from '@/nucleo/formatos'
import { ESTADO_MODELO, LIMIAR_CONFIANCA } from '@/nucleo/rotulos'
import { Botao, CabecalhoPagina, Campo, Cartao, Esqueleto, Etiqueta, Gaveta, Segmentos, Separadores, Vazio } from '@/ui/componentes'
import { LinhasSemanais } from '@/ui/graficos'
import { useModelosViewModel, type Distribuicao } from '@/viewmodels/useModelosViewModel'
import { EscolhaDistritos } from './EscolhaDistritos'

const DISTRIBUICOES: { valor: Distribuicao; nome: string }[] = [
  { valor: 'piloto', nome: 'Piloto em alguns distritos' },
  { valor: 'todos', nome: 'Todos os agricultores' },
]

export function ModelosView() {
  const vm = useModelosViewModel()
  const u = vm.emUso
  const a = vm.aberta
  const proxima = (vm.ultima?.versao ?? 0) + 1
  const comDeriva = vm.sinais.filter((s) => s.deriva)

  return (
    <>
      <CabecalhoPagina
        titulo="Modelos"
        descricao="Versões do modelo de classificação por cultura. Uma versão nova pode começar em piloto em alguns distritos; só passa a todos depois de ser validada em campo pelos técnicos."
        accoes={vm.eAdministrador && <Botao variante="primario" onClick={vm.abrirPublicacao} disabled={!vm.cultura}><Upload size={16} />Publicar nova versão</Botao>}
      />
      <Separadores valor={vm.cultura} aoMudar={vm.setCultura} opcoes={vm.culturas.map((c) => ({ valor: c.id, nome: c.nome }))} />
      {vm.erro && <div className="aviso-caixa critico"><CircleAlert size={16} />{vm.erro.message}</div>}
      {vm.aCarregar ? <Esqueleto altura={220} /> : vm.versoes.length === 0 ? (
        <Cartao><Vazio titulo="Ainda não há modelos para esta cultura" texto="Publique o primeiro ficheiro .tflite treinado para esta cultura." icone={<Boxes size={28} />} /></Cartao>
      ) : (
        <>
          <div className="grelha grelha-4">
            <div className="cartao indicador">
              <span className="rotulo">Em uso por todos</span>
              <span className="valor">{u ? `v${u.versao}` : '—'}</span>
              <span className="variacao">{u ? `desde ${dataHora(u.criado_em)}` : 'nenhuma versão publicada'}</span>
            </div>
            <div className="cartao indicador">
              <span className="rotulo">Em piloto</span>
              <span className="valor">{vm.pilotos.length ? vm.pilotos.map((p) => `v${p.versao}`).join(', ') : '—'}</span>
              <span className="variacao">{vm.pilotos.length
                ? vm.nomesDistritos([...new Set(vm.pilotos.flatMap((p) => p.distritos_piloto))]).join(', ')
                : 'nenhuma versão em teste'}</span>
            </div>
            <div className="cartao indicador">
              <span className="rotulo">Exactidão no teste</span>
              <span className="valor">{percentagem(u?.acuracia_teste, 1)}</span>
              <span className="variacao">{u ? `v${u.versao}, declarada na publicação` : '—'}</span>
            </div>
            <div className="cartao indicador">
              <span className="rotulo">Sinais de deriva</span>
              <span className="valor">{numero(comDeriva.length)}</span>
              <span className="variacao">{comDeriva.length ? 'a confiança está a cair' : 'confiança estável'}</span>
            </div>
          </div>

          {comDeriva.map((s) => (
            <div key={s.versao} className="aviso-caixa aviso">
              <TriangleAlert size={16} style={{ flex: 'none', marginTop: 2 }} />
              <span><b>Possível deriva na v{s.versao}.</b> {s.explicacao}. As fotografias recentes podem ser diferentes das do treino
                (outra época, praga nova, outro telemóvel): reveja os diagnósticos de baixa confiança e considere retreinar com os validados.</span>
            </div>
          ))}

          <div className="grelha grelha-principal">
            <Cartao titulo="Versões" subtitulo="Clique numa versão para ver a validação em campo e mudar o estado" semMargem>
              <div className="tabela-envolvente">
                <table className="tabela">
                  <thead><tr><th>Versão</th><th>Estado</th><th>Publicada</th><th className="numero">Exactidão (teste)</th><th className="numero">Tamanho</th></tr></thead>
                  <tbody>
                    {vm.versoes.map((m) => (
                      <tr key={m.versao} className="clicavel" onClick={() => vm.abrir(m)}>
                        <td><strong>v{m.versao}</strong></td>
                        <td className="celula-principal">
                          <span style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                            <Etiqueta tom={ESTADO_MODELO[m.estado].tom}>{ESTADO_MODELO[m.estado].nome}</Etiqueta>
                            {m.versao === u?.versao && <span className="suave pequeno">em uso</span>}
                          </span>
                          {m.estado === 'PILOTO' && <span>{vm.nomesDistritos(m.distritos_piloto).join(', ')}</span>}
                        </td>
                        <td className="secundario">{dataHora(m.criado_em)}</td>
                        <td className="numero">{percentagem(m.acuracia_teste, 1)}</td>
                        <td className="numero">{bytes(m.tamanho_bytes)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Cartao>
            <Cartao titulo={`Confiança abaixo de ${percentagem(LIMIAR_CONFIANCA)}, por semana`}
              subtitulo="Proporção de diagnósticos em que a app pediu confirmação ao técnico; a subir é sinal de deriva">
              {vm.aCarregarMonitorizacao || !vm.grafico ? <Esqueleto altura={220} />
                : vm.grafico.semanas.length === 0 ? <Vazio titulo="Sem diagnósticos nas últimas 12 semanas" icone={<Activity size={24} />} />
                  : (
                    <>
                      <LinhasSemanais semanas={vm.grafico.semanas} series={vm.grafico.series} formatar={(n) => percentagem(n)}
                        rotulo="Proporção de diagnósticos com confiança baixa por semana e versão" />
                      <p className="suave pequeno" style={{ marginTop: 8 }}>{numero(vm.grafico.total)} diagnósticos nas últimas 12 semanas.
                        {vm.grafico.semanas.length < 4 && ' Com poucas semanas de dados a tendência ainda não é fiável.'}</p>
                    </>
                  )}
            </Cartao>
          </div>
        </>
      )}
      {!vm.eAdministrador && <div className="aviso-caixa info"><Lock size={16} style={{ flex: 'none', marginTop: 2 }} />Só o administrador publica, promove ou retira versões do modelo.</div>}

      {/* --- Uma versão --- */}
      <Gaveta
        aberta={Boolean(a)}
        larga
        titulo={a ? `Versão ${a.versao} — ${vm.nomeCultura(a.cultura_id)}` : ''}
        subtitulo={a ? `${ESTADO_MODELO[a.estado].nome} · publicada em ${dataHora(a.criado_em)}` : ''}
        aoFechar={vm.fechar}
        rodape={vm.eAdministrador && a && (
          <>
            {a.estado !== 'RETIRADO' && (
              <Botao variante="fantasma" style={{ marginRight: 'auto' }} disabled={vm.aActualizar} onClick={vm.retirar}>Retirar versão</Botao>
            )}
            <Botao onClick={vm.fechar}>Fechar</Botao>
            {a.estado === 'PILOTO' && (
              <Botao variante="primario" disabled={vm.aActualizar || vm.pilotoAlterado} onClick={() => vm.promover(false)}>
                <CircleCheck size={15} />Publicar para todos
              </Botao>
            )}
            {a.estado === 'RETIRADO' && (
              <Botao variante="primario" disabled={vm.aActualizar} onClick={() => vm.promover(false)}>Voltar a publicar</Botao>
            )}
          </>
        )}
      >
        {a && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {a.estado === 'PILOTO' && (
              <section className="caixa-seccao" style={{ borderTop: 0, paddingTop: 0 }}>
                <h3>Validação em campo (porta de qualidade)</h3>
                {vm.aCarregarPorta || !vm.porta ? <Esqueleto altura={80} /> : (
                  <>
                    <dl className="boletim-numeros" style={{ gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' }}>
                      <div className="boletim-numero"><dt>Diagnósticos validados</dt><dd>{numero(vm.porta.validados)}</dd><dd className="suave pequeno">mínimo 10</dd></div>
                      <div className="boletim-numero"><dt>Exactidão em campo</dt><dd>{percentagem(vm.porta.exactidao, 1)}</dd><dd className="suave pequeno">v{a.versao} (piloto)</dd></div>
                      <div className="boletim-numero"><dt>Versão publicada</dt><dd>{percentagem(vm.porta.referencia_exactidao, 1)}</dd>
                        <dd className="suave pequeno">{vm.porta.referencia_versao ? `v${vm.porta.referencia_versao}` : 'sem referência'}</dd></div>
                    </dl>
                    <div className={`aviso-caixa ${vm.porta.aprovado ? '' : 'aviso'}`} style={vm.porta.aprovado ? { background: 'var(--bom-suave)', color: 'var(--bom-texto)' } : undefined}>
                      {vm.porta.aprovado ? <CircleCheck size={16} style={{ flex: 'none', marginTop: 2 }} /> : <CircleAlert size={16} style={{ flex: 'none', marginTop: 2 }} />}
                      <span><b>{vm.porta.aprovado ? 'Pode passar a todos.' : 'Ainda não deve passar a todos.'}</b> {vm.porta.motivo}</span>
                    </div>
                  </>
                )}
                {vm.bloqueio && vm.eAdministrador && (
                  <div className="aviso-caixa critico" style={{ alignItems: 'flex-start' }}>
                    <CircleAlert size={16} style={{ flex: 'none', marginTop: 2 }} />
                    <div>
                      <b>A API recusou a publicação.</b> {vm.bloqueio}
                      <div style={{ marginTop: 8 }}>
                        <Botao variante="perigo" pequeno disabled={vm.aActualizar} onClick={() => vm.promover(true)}>Publicar mesmo assim</Botao>
                        <span className="pequeno" style={{ marginLeft: 8 }}>Fica registado na auditoria.</span>
                      </div>
                    </div>
                  </div>
                )}
              </section>
            )}

            {(a.estado === 'PILOTO' || a.distritos_piloto.length > 0) && (
              <section className="caixa-seccao">
                <h3><FlaskConical size={15} style={{ verticalAlign: -2, marginRight: 6 }} />Distritos do piloto</h3>
                <p className="secundario pequeno">Os agricultores destes distritos recebem a v{a.versao} na sincronização; os outros continuam na versão publicada.</p>
                <EscolhaDistritos valor={vm.distritosEdicao} aoMudar={vm.setDistritosEdicao} desactivado={!vm.eAdministrador || a.estado !== 'PILOTO'} />
              </section>
            )}

            <section className="caixa-seccao">
              <h3>Notas</h3>
              <textarea className="entrada" rows={3} value={vm.notasEdicao} disabled={!vm.eAdministrador} placeholder="ex.: retreino com 400 fotografias validadas em Boane"
                onChange={(e) => vm.setNotasEdicao(e.target.value)} />
              {vm.eAdministrador && (
                <div>
                  <Botao disabled={!vm.pilotoAlterado || vm.aActualizar || (a.estado === 'PILOTO' && vm.distritosEdicao.length === 0)} onClick={vm.guardarPiloto}>
                    Guardar alterações
                  </Botao>
                  {vm.pilotoAlterado && a.estado === 'PILOTO' && <span className="suave pequeno" style={{ marginLeft: 10 }}>Guarde antes de publicar para todos.</span>}
                </div>
              )}
            </section>

            <section className="caixa-seccao">
              <h3>Ficheiro</h3>
              <dl className="definicoes">
                <dt>Exactidão no teste</dt><dd>{percentagem(a.acuracia_teste, 1)}</dd>
                <dt>Tamanho</dt><dd>{bytes(a.tamanho_bytes)}</dd>
                <dt>SHA-256</dt><dd className="mono" style={{ wordBreak: 'break-all' }}>{a.sha256}</dd>
                <dt>Classes</dt><dd>{a.classes.map((c, i) => <div key={c}><span className="suave mono">{i}</span> {vm.nomeClasse(a.cultura_id, c)}</div>)}</dd>
              </dl>
            </section>
          </div>
        )}
      </Gaveta>

      {/* --- Publicar --- */}
      <Gaveta
        aberta={vm.aPublicar}
        larga
        titulo={`Publicar modelo — ${vm.nomeCultura(vm.cultura)}`}
        subtitulo={`Fica como v${proxima}.`}
        aoFechar={vm.fecharPublicacao}
        rodape={
          <>
            <Botao onClick={vm.fecharPublicacao}>Cancelar</Botao>
            <Botao variante="primario" disabled={!vm.podePublicar || vm.aEnviar} onClick={vm.publicar}>
              <Upload size={15} />{vm.aEnviar ? 'A enviar…' : vm.distribuicao === 'piloto' ? `Publicar v${proxima} em piloto` : `Publicar v${proxima} para todos`}
            </Botao>
          </>
        }
      >
        <div className="formulario">
          <Campo rotulo="Ficheiro .tflite" ajuda="Entrada float32 [1, 224, 224, 3]; saída float32 [1, n.º de classes]. A app recusa um modelo com outra interface.">
            <label className="entrada" style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', height: 'auto', padding: '10px 12px' }}>
              <FileUp size={16} />
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{vm.ficheiro ? `${vm.ficheiro.name} · ${bytes(vm.ficheiro.size)}` : 'Escolher ficheiro…'}</span>
              <input type="file" accept=".tflite" hidden onChange={(e) => vm.setFicheiro(e.target.files?.[0] ?? null)} />
            </label>
          </Campo>
          {vm.ficheiro && (
            <div className="aviso-caixa info" style={{ alignItems: 'flex-start' }}>
              <ShieldCheck size={16} style={{ flex: 'none', marginTop: 2 }} />
              <div>SHA-256 calculado neste computador:<div className="mono" style={{ wordBreak: 'break-all', marginTop: 4 }}>{vm.resumoLocal ?? 'a calcular…'}</div>
                Depois de publicar, é comparado com o que a API guardou.</div>
            </div>
          )}
          <div className="campo">
            <span>Quem recebe esta versão</span>
            <Segmentos rotulo="Quem recebe esta versão" valor={vm.distribuicao} opcoes={DISTRIBUICOES} aoMudar={vm.setDistribuicao} />
            <small>{vm.distribuicao === 'piloto'
              ? 'Só os agricultores dos distritos escolhidos. Depois de 10 diagnósticos validados pelos técnicos, pode passar a todos.'
              : vm.emUso ? `Substitui a v${vm.emUso.versao} para todos na próxima sincronização, sem validação em campo.` : 'Primeira versão desta cultura.'}</small>
          </div>
          {vm.distribuicao === 'piloto' && <EscolhaDistritos valor={vm.distritosPiloto} aoMudar={vm.setDistritosPiloto} />}
          <Campo rotulo="Classes, uma por linha, pela ordem das saídas"
            erro={vm.desconhecidas.length ? `Sem correspondência no catálogo: ${vm.desconhecidas.join(', ')}` : null}
            ajuda={`${vm.listaClasses.length} classes. Pré-preenchido com as da última versão.`}>
            <textarea className="entrada mono" rows={8} value={vm.classes} onChange={(e) => vm.setClasses(e.target.value)} />
          </Campo>
          <Campo rotulo="Exactidão no conjunto de teste (%)" erro={vm.acuraciaValida ? null : 'Valor entre 0 e 100'} ajuda="Opcional. Ex.: 87,0">
            <input className="entrada" inputMode="decimal" value={vm.acuracia} onChange={(e) => vm.setAcuracia(e.target.value)} />
          </Campo>
          <Campo rotulo="Notas (opcional)" ajuda="O que mudou nesta versão; fica no histórico.">
            <textarea className="entrada" rows={3} value={vm.notas} onChange={(e) => vm.setNotas(e.target.value)} />
          </Campo>
        </div>
      </Gaveta>
    </>
  )
}
