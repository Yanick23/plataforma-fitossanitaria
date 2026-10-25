import { useState } from 'react'
import { CircleAlert, Lock, Plus, Search, Sprout, Trash2 } from 'lucide-react'
import type { TipoPatologia } from '@/model/tipos'
import { TIPO } from '@/nucleo/rotulos'
import { Botao, CabecalhoPagina, Campo, Cartao, Esqueleto, Etiqueta, Gaveta, Segmentos, Separadores, Vazio } from '@/ui/componentes'
import { useCatalogoViewModel } from '@/viewmodels/useCatalogoViewModel'

const AVISO_APP = 'Recomendação básica gerada automaticamente. Confirme o diagnóstico e o tratamento com um extensionista ou técnico agrário.'

export function CatalogoView() {
  const vm = useCatalogoViewModel()
  const e = vm.edicao
  const [confirmarApagar, setConfirmarApagar] = useState(false)

  return (
    <>
      <CabecalhoPagina
        titulo="Culturas e pragas"
        descricao="O que a app mostra a cada agricultor depois de um diagnóstico: nome local, nome científico e recomendação. As alterações chegam à app na sincronização."
        accoes={vm.eAdministrador && (
          <>
            <Botao onClick={vm.abrirNovaCultura}><Sprout size={16} />Nova cultura</Botao>
            <Botao variante="primario" onClick={vm.nova} disabled={!vm.cultura}><Plus size={16} />Nova praga ou doença</Botao>
          </>
        )}
      />
      {!vm.eAdministrador && (
        <div className="aviso-caixa info"><Lock size={16} style={{ flex: 'none', marginTop: 2 }} />Só o administrador pode alterar o catálogo. Se encontrar um erro numa recomendação, informe-o.</div>
      )}
      {vm.aCarregar ? <Esqueleto altura={300} /> : (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', gap: 16, flexWrap: 'wrap' }}>
            <Separadores valor={vm.cultura} aoMudar={vm.setCultura} opcoes={vm.culturas.map((c) => ({ valor: c.id, nome: c.nome }))} />
            <label className="campo largo" style={{ width: 280 }}>
              <span className="so-leitor">Pesquisar</span>
              <div style={{ position: 'relative' }}>
                <Search size={15} style={{ position: 'absolute', left: 10, top: 10, color: 'var(--tinta-3)' }} />
                <input className="entrada" style={{ paddingLeft: 32 }} placeholder="Pesquisar no catálogo" value={vm.pesquisa} onChange={(ev) => vm.setPesquisa(ev.target.value)} />
              </div>
            </label>
          </div>
          <Cartao semMargem>
            {vm.patologias.length === 0 ? <Vazio titulo="Sem pragas ou doenças nesta cultura" /> : (
              <table className="tabela">
                <thead><tr><th>Nome local</th><th>Tipo</th><th>Recomendação</th><th>Código do modelo</th></tr></thead>
                <tbody>
                  {vm.patologias.map((p) => (
                    <tr key={p.id} className="clicavel" onClick={() => vm.editar(p)}>
                      <td className="celula-principal"><strong>{p.nome_local}</strong><span><i>{p.nome_cientifico}</i></span></td>
                      <td><Etiqueta tom={TIPO[p.tipo].tom}>{TIPO[p.tipo].nome}</Etiqueta></td>
                      <td style={{ maxWidth: 520 }}>
                        {vm.recomendacaoEmFalta(p)
                          ? <Etiqueta tom="aviso" icone={<CircleAlert size={12} />}>Recomendação em falta</Etiqueta>
                          : <span className="secundario" style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{p.recomendacao}</span>}
                      </td>
                      <td className="mono suave">{p.codigo}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Cartao>
        </>
      )}

      <Gaveta
        aberta={Boolean(e)}
        larga
        titulo={e?.id === null ? 'Nova praga ou doença' : vm.eAdministrador ? 'Editar praga ou doença' : e?.nome_local ?? ''}
        subtitulo={e ? vm.nomeCultura(e.cultura_id) : ''}
        aoFechar={() => { setConfirmarApagar(false); vm.fecharEdicao() }}
        rodape={vm.eAdministrador && e && (
          <>
            {e.id !== null && (confirmarApagar
              ? <Botao variante="perigo" style={{ marginRight: 'auto' }} disabled={vm.aApagar} onClick={vm.apagar}><Trash2 size={15} />Confirmar: apagar</Botao>
              : <Botao variante="fantasma" style={{ marginRight: 'auto' }} onClick={() => setConfirmarApagar(true)}><Trash2 size={15} />Apagar</Botao>)}
            <Botao onClick={vm.fecharEdicao}>Cancelar</Botao>
            <Botao variante="primario" disabled={vm.aGuardar || !e.nome_local.trim() || (e.id === null && !/^[a-z_]+$/.test(e.codigo))} onClick={vm.guardar}>
              {vm.aGuardar ? 'A guardar…' : 'Guardar'}
            </Botao>
          </>
        )}
      >
        {e && (
          <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start', flexWrap: 'wrap' }}>
            <fieldset className="formulario" disabled={!vm.eAdministrador} style={{ flex: '1 1 340px', minWidth: 0, border: 0, padding: 0, margin: 0 }}>
              {e.id === null && (
                <>
                  <Campo rotulo="Código do modelo" ajuda="Tem de ser igual à classe que o modelo devolve (letras minúsculas e _). Sem um modelo treinado com esta classe, nunca será diagnosticada.">
                    <input className="entrada mono" value={e.codigo} onChange={(ev) => vm.alterar('codigo', ev.target.value.toLowerCase())} placeholder="ex.: ferrugem" />
                  </Campo>
                </>
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
              <Campo rotulo="Recomendação ao agricultor" ajuda={`${e.recomendacao.length} caracteres · frases curtas, acções concretas`}>
                <textarea className="entrada" rows={8} value={e.recomendacao} onChange={(ev) => vm.alterar('recomendacao', ev.target.value)} />
              </Campo>
            </fieldset>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center' }}>
              <span className="suave pequeno">Ecrã de resultado na app</span>
              <div className="telemovel">
                <div className="telemovel-ecra">
                  <span className="t-cultura">{vm.nomeCultura(e.cultura_id)}</span>
                  <h4>{e.nome_local || 'Nome local'}</h4>
                  <em>{e.nome_cientifico || 'Nome científico'}</em>
                  <div className="t-recomendacao">
                    <b>Recomendação</b>
                    {e.recomendacao || 'A recomendação aparece aqui.'}
                    <div style={{ marginTop: 8, fontSize: 11, color: '#6b7280' }}>{AVISO_APP}</div>
                  </div>
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
