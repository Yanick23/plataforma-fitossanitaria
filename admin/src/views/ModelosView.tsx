import { Boxes, CircleAlert, FileUp, Lock, ShieldCheck, Upload } from 'lucide-react'
import { bytes, dataHora, percentagem } from '@/nucleo/formatos'
import { Botao, CabecalhoPagina, Campo, Cartao, Esqueleto, Etiqueta, Gaveta, Separadores, Vazio } from '@/ui/componentes'
import { useModelosViewModel } from '@/viewmodels/useModelosViewModel'

export function ModelosView() {
  const vm = useModelosViewModel()
  const a = vm.actual

  return (
    <>
      <CabecalhoPagina
        titulo="Modelos"
        descricao="Versões do modelo de classificação por cultura. A app usa a versão mais recente: descarrega-a na sincronização, confirma o SHA-256 e só então a activa."
        accoes={vm.eAdministrador && <Botao variante="primario" onClick={vm.abrirPublicacao} disabled={!vm.cultura}><Upload size={16} />Publicar nova versão</Botao>}
      />
      <Separadores valor={vm.cultura} aoMudar={vm.setCultura} opcoes={vm.culturas.map((c) => ({ valor: c.id, nome: c.nome }))} />
      {vm.erro && <div className="aviso-caixa critico"><CircleAlert size={16} />{vm.erro.message}</div>}
      {vm.aCarregar ? <Esqueleto altura={220} /> : !a ? (
        <Cartao><Vazio titulo="Ainda não há modelos para esta cultura" texto="Publique o primeiro ficheiro .tflite treinado para esta cultura." icone={<Boxes size={28} />} /></Cartao>
      ) : (
        <>
          <div className="grelha grelha-4">
            <div className="cartao indicador"><span className="rotulo">Versão em uso</span><span className="valor">v{a.versao}</span><span className="variacao">desde {dataHora(a.criado_em)}</span></div>
            <div className="cartao indicador"><span className="rotulo">Exactidão no teste</span><span className="valor">{percentagem(a.acuracia_teste, 1)}</span><span className="variacao">declarada na publicação</span></div>
            <div className="cartao indicador"><span className="rotulo">Tamanho</span><span className="valor">{bytes(a.tamanho_bytes)}</span><span className="variacao">TFLite, descarregado pela app</span></div>
            <div className="cartao indicador"><span className="rotulo">Classes</span><span className="valor">{a.classes.length}</span><span className="variacao">pela ordem das saídas do modelo</span></div>
          </div>
          <div className="grelha grelha-principal">
            <Cartao titulo="Histórico de versões" semMargem>
              <table className="tabela">
                <thead><tr><th>Versão</th><th>Publicada</th><th className="numero">Exactidão</th><th className="numero">Tamanho</th><th>SHA-256</th></tr></thead>
                <tbody>
                  {vm.versoes.map((m) => (
                    <tr key={m.versao}>
                      <td><strong>v{m.versao}</strong> {m.versao === a.versao && <Etiqueta tom="marca">Em uso</Etiqueta>}</td>
                      <td className="numeros secundario">{dataHora(m.criado_em)}</td>
                      <td className="numero">{percentagem(m.acuracia_teste, 1)}</td>
                      <td className="numero">{bytes(m.tamanho_bytes)}</td>
                      <td className="mono suave" title={m.sha256}>{m.sha256.slice(0, 12)}…</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Cartao>
            <Cartao titulo={`Classes da v${a.versao}`} subtitulo="Índice da saída → praga ou doença no catálogo" semMargem>
              <table className="tabela">
                <tbody>
                  {a.classes.map((c, i) => (
                    <tr key={c}>
                      <td className="numero suave" style={{ width: 1 }}>{i}</td>
                      <td className="celula-principal"><strong>{vm.nomeClasse(vm.cultura, c)}</strong><span className="mono">{c}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Cartao>
          </div>
        </>
      )}
      {!vm.eAdministrador && <div className="aviso-caixa info"><Lock size={16} style={{ flex: 'none', marginTop: 2 }} />Só o administrador pode publicar versões do modelo.</div>}

      <Gaveta
        aberta={vm.aPublicar}
        titulo={`Publicar modelo — ${vm.nomeCultura(vm.cultura)}`}
        subtitulo={`Fica como v${(a?.versao ?? 0) + 1}. As apps descarregam-no na próxima sincronização.`}
        aoFechar={vm.fecharPublicacao}
        rodape={
          <>
            <Botao onClick={vm.fecharPublicacao}>Cancelar</Botao>
            <Botao variante="primario" disabled={!vm.podePublicar || vm.aEnviar} onClick={vm.publicar}>
              <Upload size={15} />{vm.aEnviar ? 'A enviar…' : `Publicar v${(a?.versao ?? 0) + 1}`}
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
          <Campo rotulo="Classes, uma por linha, pela ordem das saídas"
            erro={vm.desconhecidas.length ? `Sem correspondência no catálogo: ${vm.desconhecidas.join(', ')}` : null}
            ajuda={`${vm.listaClasses.length} classes. Pré-preenchido com as da versão actual.`}>
            <textarea className="entrada mono" rows={9} value={vm.classes} onChange={(e) => vm.setClasses(e.target.value)} />
          </Campo>
          <Campo rotulo="Exactidão no conjunto de teste (%)" erro={vm.acuraciaValida ? null : 'Valor entre 0 e 100'} ajuda="Opcional. Ex.: 87,0">
            <input className="entrada" inputMode="decimal" value={vm.acuracia} onChange={(e) => vm.setAcuracia(e.target.value)} />
          </Campo>
        </div>
      </Gaveta>
    </>
  )
}
