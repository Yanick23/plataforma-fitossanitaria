import { useRef, useState } from 'react'
import { CircleAlert, CircleCheck, ImagePlus, Lock, Plus, Search, ShieldAlert, Sprout, Trash2, X } from 'lucide-react'
import type { TipoPatologia } from '@/model/tipos'
import { data } from '@/nucleo/formatos'
import { TIPO } from '@/nucleo/rotulos'
import { Botao, CabecalhoPagina, Campo, Cartao, Esqueleto, Etiqueta, Gaveta, Segmentos, Separadores, Vazio } from '@/ui/componentes'
import { conteudoValidado, useCatalogoViewModel, type FiltroRevisao } from '@/viewmodels/useCatalogoViewModel'

const AVISO_APP = 'Recomendação básica gerada automaticamente. Confirme o diagnóstico e o tratamento com um extensionista ou técnico agrário.'

export function CatalogoView() {
  const vm = useCatalogoViewModel()
  const e = vm.edicao
  const g = vm.guardada
  const [confirmarApagar, setConfirmarApagar] = useState(false)
  const [legenda, setLegenda] = useState('')
  const ficheiro = useRef<HTMLInputElement>(null)

  const filtros: { valor: FiltroRevisao; nome: string }[] = [
    { valor: '', nome: `Todas (${vm.total})` },
    { valor: 'por_validar', nome: `Por validar (${vm.porValidar})` },
    { valor: 'declaracao', nome: 'Declaração obrigatória' },
  ]

  return (
    <>
      <CabecalhoPagina
        titulo="Culturas e pragas"
        descricao="O que a app mostra a cada agricultor depois de um diagnóstico: sintomas, recomendação, prevenção e fotografias de referência. As alterações chegam à app na sincronização."
        accoes={vm.eAdministrador && (
          <>
            <Botao onClick={vm.abrirNovaCultura}><Sprout size={16} />Nova cultura</Botao>
            <Botao variante="primario" onClick={vm.nova} disabled={!vm.cultura}><Plus size={16} />Nova praga ou doença</Botao>
          </>
        )}
      />
      {!vm.eAdministrador && (
        <div className="aviso-caixa info"><Lock size={16} style={{ flex: 'none', marginTop: 2 }} />
          Só o administrador altera o catálogo. Como técnico, pode rever e validar o texto que os agricultores lêem.</div>
      )}
      {vm.aCarregar ? <Esqueleto altura={300} /> : (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', gap: 16, flexWrap: 'wrap' }}>
            <Separadores valor={vm.cultura} aoMudar={vm.setCultura} opcoes={vm.culturas.map((c) => ({ valor: c.id, nome: c.nome }))} />
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
              <Segmentos rotulo="Filtrar" valor={vm.filtro} opcoes={filtros} aoMudar={vm.setFiltro} />
              <label className="campo largo" style={{ width: 240 }}>
                <span className="so-leitor">Pesquisar</span>
                <div style={{ position: 'relative' }}>
                  <Search size={15} style={{ position: 'absolute', left: 10, top: 10, color: 'var(--tinta-3)' }} />
                  <input className="entrada" style={{ paddingLeft: 32 }} placeholder="Pesquisar no catálogo" value={vm.pesquisa} onChange={(ev) => vm.setPesquisa(ev.target.value)} />
                </div>
              </label>
            </div>
          </div>
          <Cartao semMargem>
            {vm.patologias.length === 0 ? <Vazio titulo="Nada a mostrar" texto="Nenhuma praga ou doença corresponde ao filtro." /> : (
              <div className="tabela-envolvente">
                <table className="tabela">
                  <thead><tr><th>Nome local</th><th>Tipo</th><th>Informação para o agricultor</th><th>Revisão</th><th className="numero">Fotos</th><th>Código do modelo</th></tr></thead>
                  <tbody>
                    {vm.patologias.map((p) => {
                      const falta = vm.emFalta(p)
                      return (
                        <tr key={p.id} className="clicavel" onClick={() => vm.editar(p)}>
                          <td className="celula-principal">
                            <strong>{p.nome_local}</strong>
                            <span><i>{p.nome_cientifico}</i></span>
                            {p.declaracao_obrigatoria && <span style={{ marginTop: 4 }}><Etiqueta tom="critico" icone={<ShieldAlert size={12} />}>Declaração obrigatória</Etiqueta></span>}
                          </td>
                          <td><Etiqueta tom={TIPO[p.tipo].tom}>{TIPO[p.tipo].nome}</Etiqueta></td>
                          <td>
                            {falta.length
                              ? <Etiqueta tom="aviso" icone={<CircleAlert size={12} />}>Falta: {falta.join(', ')}</Etiqueta>
                              : <span className="secundario">Completa</span>}
                          </td>
                          <td className="celula-principal">
                            {conteudoValidado(p)
                              ? <Etiqueta tom="bom" icone={<CircleCheck size={12} />}>Validado</Etiqueta>
                              : <Etiqueta tom="neutro" icone={<CircleAlert size={12} />}>Por validar</Etiqueta>}
                            <span>versão {p.versao_conteudo}</span>
                          </td>
                          <td className="numero">{p.fotos.length}</td>
                          <td className="mono suave">{p.codigo}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </Cartao>
        </>
      )}

      <Gaveta
        aberta={Boolean(e)}
        larga
        titulo={e?.id === null ? 'Nova praga ou doença' : vm.eAdministrador ? 'Editar praga ou doença' : e?.nome_local ?? ''}
        subtitulo={e ? `${vm.nomeCultura(e.cultura_id)}${g ? ` · versão ${g.versao_conteudo} do texto` : ''}` : ''}
        aoFechar={() => { setConfirmarApagar(false); vm.fecharEdicao() }}
        rodape={vm.eAdministrador && e && (
          <>
            {e.id !== null && (confirmarApagar
              ? <Botao variante="perigo" style={{ marginRight: 'auto' }} disabled={vm.aApagar} onClick={vm.apagar}><Trash2 size={15} />Confirmar: apagar</Botao>
              : <Botao variante="fantasma" style={{ marginRight: 'auto' }} onClick={() => setConfirmarApagar(true)}><Trash2 size={15} />Apagar</Botao>)}
            <Botao onClick={vm.fecharEdicao}>Fechar</Botao>
            <Botao variante="primario" disabled={vm.aGuardar || !e.nome_local.trim() || (e.id === null ? !/^[a-z_]+$/.test(e.codigo) : !vm.porGuardar)} onClick={vm.guardar}>
              {vm.aGuardar ? 'A guardar…' : e.id === null ? 'Criar' : 'Guardar alterações'}
            </Botao>
          </>
        )}
      >
        {e && (
          <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start', flexWrap: 'wrap' }}>
            <div style={{ flex: '1 1 360px', minWidth: 0, display: 'flex', flexDirection: 'column', gap: 20 }}>
              <fieldset className="formulario" disabled={!vm.eAdministrador} style={{ border: 0, padding: 0, margin: 0 }}>
                {e.id === null && (
                  <Campo rotulo="Código do modelo" ajuda="Tem de ser igual à classe que o modelo devolve (letras minúsculas e _). Sem um modelo treinado com esta classe, nunca será diagnosticada.">
                    <input className="entrada mono" value={e.codigo} onChange={(ev) => vm.alterar('codigo', ev.target.value.toLowerCase())} placeholder="ex.: ferrugem" />
                  </Campo>
                )}
                <Campo rotulo="Nome local">
                  <input className="entrada" value={e.nome_local} onChange={(ev) => vm.alterar('nome_local', ev.target.value)} />
                </Campo>
                <Campo rotulo="Nome científico">
                  <input className="entrada" value={e.nome_cientifico} onChange={(ev) => vm.alterar('nome_cientifico', ev.target.value)} />
                </Campo>
                <Campo rotulo="Tipo">
                  <Segmentos rotulo="Tipo" valor={e.tipo} aoMudar={(v: TipoPatologia) => vm.alterar('tipo', v)}
                    opcoes={(['DOENCA', 'PRAGA', 'SAUDAVEL'] as TipoPatologia[]).map((t) => ({ valor: t, nome: TIPO[t].nome }))} />
                </Campo>
                <label className="campo" style={{ flexDirection: 'row', alignItems: 'flex-start', gap: 8 }}>
                  <input type="checkbox" checked={e.declaracao_obrigatoria} onChange={(ev) => vm.alterar('declaracao_obrigatoria', ev.target.checked)} style={{ marginTop: 3 }} />
                  <span style={{ color: 'var(--tinta)' }}>
                    Praga ou doença de declaração obrigatória
                    <small style={{ display: 'block', color: 'var(--tinta-3)', fontWeight: 400 }}>Os casos aparecem em Vigilância e no boletim, como suspeita ou confirmados, para serem comunicados.</small>
                  </span>
                </label>
                <Campo rotulo="Sintomas" ajuda="Como o agricultor a reconhece na planta.">
                  <textarea className="entrada" rows={4} value={e.sintomas} onChange={(ev) => vm.alterar('sintomas', ev.target.value)} />
                </Campo>
                <Campo rotulo="Recomendação ao agricultor" ajuda={`${e.recomendacao.length} caracteres · frases curtas, acções concretas`}>
                  <textarea className="entrada" rows={6} value={e.recomendacao} onChange={(ev) => vm.alterar('recomendacao', ev.target.value)} />
                </Campo>
                <Campo rotulo="Prevenção" ajuda="O que fazer na próxima campanha para não voltar a acontecer.">
                  <textarea className="entrada" rows={4} value={e.prevencao} onChange={(ev) => vm.alterar('prevencao', ev.target.value)} />
                </Campo>
              </fieldset>

              {g && (
                <section className="caixa-seccao">
                  <h3>Revisão do texto</h3>
                  {conteudoValidado(g) ? (
                    <div className="aviso-caixa" style={{ background: 'var(--bom-suave)', color: 'var(--bom-texto)' }}>
                      <CircleCheck size={16} style={{ flex: 'none', marginTop: 2 }} />
                      <span>Validado por <b>{g.validado_por_nome}</b>{g.validado_em ? ` em ${data(g.validado_em)}` : ''} (versão {g.versao_conteudo}).</span>
                    </div>
                  ) : (
                    <p className="secundario">Versão {g.versao_conteudo}, ainda <b>por validar</b>. Um técnico confirma que os sintomas, a recomendação e a prevenção estão correctos antes de os agricultores dependerem deles.</p>
                  )}
                  {vm.textoAlterado && conteudoValidado(g) && (
                    <div className="aviso-caixa aviso"><CircleAlert size={16} style={{ flex: 'none', marginTop: 2 }} />Ao guardar, o texto passa à versão {g.versao_conteudo + 1} e deixa de estar validado.</div>
                  )}
                  {!conteudoValidado(g) && (
                    <div>
                      <Botao variante="primario" onClick={vm.validar} disabled={vm.aValidar || vm.porGuardar}>
                        <CircleCheck size={16} />{vm.aValidar ? 'A validar…' : 'Validar este texto'}
                      </Botao>
                      {vm.porGuardar && <span className="suave pequeno" style={{ marginLeft: 10 }}>Guarde primeiro as alterações.</span>}
                    </div>
                  )}
                </section>
              )}

              {g && (
                <section className="caixa-seccao">
                  <h3>Fotografias de referência</h3>
                  <p className="secundario pequeno">Exemplos reais para o agricultor comparar com a sua planta. JPEG ou PNG, até 5 MB.</p>
                  {g.fotos.length === 0 ? <p className="suave">Ainda sem fotografias.</p> : (
                    <div className="fotos-grelha">
                      {g.fotos.map((f) => (
                        <figure key={f.id}>
                          <img src={vm.urlFoto(f)} alt={f.legenda ?? g.nome_local} loading="lazy" />
                          {f.legenda && <figcaption>{f.legenda}</figcaption>}
                          {vm.eAdministrador && (
                            <button type="button" className="foto-remover" aria-label="Remover fotografia" title="Remover fotografia" onClick={() => vm.apagarFoto(f.id)}>
                              <X size={14} />
                            </button>
                          )}
                        </figure>
                      ))}
                    </div>
                  )}
                  {vm.eAdministrador && (
                    <div className="filtros" style={{ marginTop: 4 }}>
                      <Campo rotulo="Legenda (opcional)" largo>
                        <input className="entrada" value={legenda} maxLength={200} onChange={(ev) => setLegenda(ev.target.value)} placeholder="ex.: folha com pústulas no início" />
                      </Campo>
                      <input ref={ficheiro} type="file" accept="image/jpeg,image/png" hidden onChange={(ev) => {
                        const f = ev.target.files?.[0]
                        if (f) { vm.enviarFoto(f, legenda); setLegenda('') }
                        ev.target.value = ''
                      }} />
                      <Botao onClick={() => ficheiro.current?.click()} disabled={vm.aEnviarFoto}>
                        <ImagePlus size={16} />{vm.aEnviarFoto ? 'A enviar…' : 'Acrescentar fotografia'}
                      </Botao>
                    </div>
                  )}
                </section>
              )}
              {e.id === null && <p className="suave pequeno">Depois de criar, pode juntar fotografias e pedir a validação do texto.</p>}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center', position: 'sticky', top: 0 }}>
              <span className="suave pequeno">Ecrã de resultado na app</span>
              <div className="telemovel">
                <div className="telemovel-ecra">
                  <span className="t-cultura">{vm.nomeCultura(e.cultura_id)}</span>
                  {g?.fotos[0] && <img className="t-foto" src={vm.urlFoto(g.fotos[0])} alt="" />}
                  <h4>{e.nome_local || 'Nome local'}</h4>
                  <em>{e.nome_cientifico || 'Nome científico'}</em>
                  {e.sintomas.trim() && <div className="t-bloco"><b>Sintomas</b>{e.sintomas}</div>}
                  <div className="t-recomendacao">
                    <b>Recomendação</b>
                    {e.recomendacao || 'A recomendação aparece aqui.'}
                    <div style={{ marginTop: 8, fontSize: 11, color: '#6b7280' }}>{AVISO_APP}</div>
                  </div>
                  {e.prevencao.trim() && <div className="t-bloco"><b>Prevenção</b>{e.prevencao}</div>}
                </div>
              </div>
            </div>
          </div>
        )}
      </Gaveta>

      <Gaveta
        aberta={Boolean(vm.novaCultura)}
        titulo="Nova cultura"
        subtitulo="A cultura fica no catálogo. A app só a mostra quando houver um modelo treinado para ela."
        aoFechar={vm.fecharNovaCultura}
        rodape={
          <>
            <Botao onClick={vm.fecharNovaCultura}>Cancelar</Botao>
            <Botao variante="primario" onClick={vm.guardarCultura}
              disabled={vm.aGuardarCultura || !vm.novaCultura?.nome.trim() || !/^[a-z_]+$/.test(vm.novaCultura?.id ?? '')}>Criar cultura</Botao>
          </>
        }
      >
        {vm.novaCultura && (
          <div className="formulario">
            <Campo rotulo="Identificador" ajuda="Letras minúsculas e _ (ex.: feijao_nhemba).">
              <input className="entrada mono" value={vm.novaCultura.id} onChange={(ev) => vm.alterarCultura('id', ev.target.value.toLowerCase())} />
            </Campo>
            <Campo rotulo="Nome">
              <input className="entrada" value={vm.novaCultura.nome} onChange={(ev) => vm.alterarCultura('nome', ev.target.value)} placeholder="Feijão-nhemba" />
            </Campo>
            <Campo rotulo="Nome científico">
              <input className="entrada" value={vm.novaCultura.nome_cientifico} onChange={(ev) => vm.alterarCultura('nome_cientifico', ev.target.value)} placeholder="Vigna unguiculata" />
            </Campo>
          </div>
        )}
      </Gaveta>
    </>
  )
}
