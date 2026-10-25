import { Download, ListChecks } from 'lucide-react'
import { numero, percentagem, relativo } from '@/nucleo/formatos'
import { BarrasHorizontais } from '@/ui/graficos'
import { Botao, CabecalhoPagina, Cartao, Confianca, Esqueleto, Indicador, Seleccao, Vazio } from '@/ui/componentes'
import { useCatalogo } from '@/viewmodels/referencias'
import { useValidacaoViewModel } from '@/viewmodels/useValidacaoViewModel'
import { DetalheDiagnostico } from './DetalheDiagnostico'

export function ValidacaoView() {
  const vm = useValidacaoViewModel()
  const catalogo = useCatalogo()
  const e = vm.exactidao

  return (
    <>
      <CabecalhoPagina
        titulo="Validação"
        descricao="O técnico confirma ou corrige o que o modelo previu. Cada validação mede a exactidão real do modelo no terreno e junta imagens rotuladas para o retreinar."
        accoes={
          <>
            <Seleccao vazio="Todas as culturas" value={vm.cultura} onChange={(ev) => vm.setCultura(ev.target.value)}
              opcoes={catalogo.culturas.map((c) => ({ valor: c.id, nome: c.nome }))} style={{ width: 200 }} />
            {vm.eAdministrador && (
              <Botao onClick={vm.exportar} disabled={vm.aExportar || !e?.validados}>
                <Download size={16} />{vm.aExportar ? 'A preparar…' : 'Exportar para retreino'}
              </Botao>
            )}
          </>
        }
      />
      <div className="grelha grelha-4">
        <Indicador rotulo="Exactidão em campo" valor={percentagem(e?.exactidao, 1)}
          variacao={<span className="variacao">concordância modelo × técnico</span>} />
        <Indicador rotulo="Diagnósticos validados" valor={numero(e?.validados ?? 0)}
          variacao={<span className="variacao">{numero(e?.correctos ?? 0)} confirmados · {numero(vm.correccoes)} corrigidos</span>} />
        <Indicador rotulo="Por validar" valor={numero(e?.pendentes ?? 0)}
          variacao={<span className="variacao">na sua zona</span>} />
        <Indicador rotulo="Pares mais confundidos" valor={numero(e?.confusoes.length ?? 0)}
          variacao={<span className="variacao">tipos de erro diferentes</span>} />
      </div>
      <div className="grelha grelha-principal">
        <Cartao titulo="Fila de validação" subtitulo="Menos certos primeiro; depois de validar, abre o seguinte" semMargem>
          {vm.aCarregarFila ? <div style={{ padding: 20 }}><Esqueleto altura={200} /></div>
            : vm.fila.length === 0 ? <Vazio titulo="Fila vazia" texto="Todos os diagnósticos da sua zona estão validados." icone={<ListChecks size={28} />} /> : (
              <table className="tabela">
                <thead><tr><th>Previsão</th><th>Agricultor e distrito</th><th className="numero">Confiança</th></tr></thead>
                <tbody>
                  {vm.fila.map((d) => (
                    <tr key={d.id} className="clicavel" onClick={() => vm.abrir(d)}>
                      <td className="celula-principal"><strong>{d.patologia_nome ?? d.classe_prevista}</strong><span>{catalogo.nomeCultura(d.cultura_id)} · {relativo(d.data)}</span></td>
                      <td className="celula-principal"><strong style={{ fontWeight: 400 }}>{d.utilizador_nome}</strong><span>{d.distrito_nome ?? '—'}</span></td>
                      <td className="numero"><Confianca valor={d.confianca} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          {vm.totalFila > vm.fila.length && <div className="paginacao"><span>A mostrar {vm.fila.length} de {numero(vm.totalFila)} por validar</span></div>}
        </Cartao>
        <div className="grelha" style={{ alignContent: 'start' }}>
          <Cartao titulo="Exactidão por praga ou doença" subtitulo="Pela classe confirmada pelo técnico (sensibilidade)">
            {vm.aCarregarExactidao ? <Esqueleto altura={160} /> : !e?.por_classe.length
              ? <Vazio titulo="Ainda sem validações" texto="Valide diagnósticos para medir a exactidão em campo." />
              : <BarrasHorizontais maximo={1} formatar={(x) => percentagem(x)}
                  itens={e.por_classe.map((c) => ({ chave: c.classe, nome: `${c.nome} (${c.correctos}/${c.validados})`, valor: c.exactidao ?? 0 }))} />}
          </Cartao>
          {e && e.confusoes.length > 0 && (
            <Cartao titulo="O modelo confunde" subtitulo="Previsto → confirmado pelo técnico" semMargem>
              <table className="tabela">
                <tbody>
                  {e.confusoes.slice(0, 6).map((c) => (
                    <tr key={`${c.cultura_id}-${c.prevista}-${c.confirmada}`}>
                      <td>{catalogo.nomeClasse(c.cultura_id, c.prevista)} <span className="suave">→</span> <strong style={{ fontWeight: 500 }}>{catalogo.nomeClasse(c.cultura_id, c.confirmada)}</strong></td>
                      <td className="numero">{numero(c.total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Cartao>
          )}
          {e && e.por_versao.length > 0 && (
            <Cartao titulo="Por versão do modelo" semMargem>
              <table className="tabela">
                <thead><tr><th>Modelo</th><th className="numero">Validados</th><th className="numero">Exactidão</th></tr></thead>
                <tbody>
                  {e.por_versao.map((v) => (
                    <tr key={`${v.cultura_id}-${v.versao_modelo}`}>
                      <td>{catalogo.nomeCultura(v.cultura_id)} v{v.versao_modelo ?? '—'}</td>
                      <td className="numero">{numero(v.validados)}</td>
                      <td className="numero">{percentagem(v.exactidao, 1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Cartao>
          )}
        </div>
      </div>
      <DetalheDiagnostico diagnostico={vm.aberto} aoFechar={vm.fechar} aoValidar={vm.validar} aValidar={vm.aValidar} />
    </>
  )
}
