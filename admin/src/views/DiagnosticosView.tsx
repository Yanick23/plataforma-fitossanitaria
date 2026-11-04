import { CircleAlert, ScanSearch } from 'lucide-react'
import { dataHora, numero } from '@/nucleo/formatos'
import { VALIDACAO } from '@/nucleo/rotulos'
import { Botao, CabecalhoPagina, Campo, Cartao, Confianca, Esqueleto, Etiqueta, Paginacao, Seleccao, Vazio } from '@/ui/componentes'
import { useDiagnosticosViewModel } from '@/viewmodels/useDiagnosticosViewModel'
import { useCatalogo, useRegioes } from '@/viewmodels/referencias'
import { DetalheDiagnostico } from './DetalheDiagnostico'

export function DiagnosticosView() {
  const vm = useDiagnosticosViewModel()
  const catalogo = useCatalogo()
  const regioes = useRegioes()
  const f = vm.filtros

  return (
    <>
      <CabecalhoPagina
        titulo="Diagnósticos"
        descricao="Todos os diagnósticos sincronizados na sua zona. Abra um para ver a fotografia, onde o modelo olhou e validar."
      />
      <Cartao semMargem>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--linha)' }}>
          <div className="filtros">
            <Campo rotulo="Cultura">
              <Seleccao vazio="Todas" value={f.cultura} onChange={(e) => vm.alterar('cultura', e.target.value)}
                opcoes={catalogo.culturas.map((c) => ({ valor: c.id, nome: c.nome }))} />
            </Campo>
            <Campo rotulo="Praga ou doença">
              <Seleccao vazio="Todas" value={f.classe} disabled={!f.cultura} onChange={(e) => vm.alterar('classe', e.target.value)}
                opcoes={catalogo.patologiasDe(f.cultura).map((p) => ({ valor: p.codigo, nome: p.nome_local }))} />
            </Campo>
            <Campo rotulo="Província">
              <Seleccao vazio="Todas" value={f.provincia} onChange={(e) => vm.alterar('provincia', e.target.value)} opcoes={regioes.opcoesProvincias} />
            </Campo>
            <Campo rotulo="Distrito">
              <Seleccao vazio="Todos" value={f.distrito} onChange={(e) => vm.alterar('distrito', e.target.value)}
                opcoes={regioes.distritosDe(f.provincia).map((d) => ({ valor: String(d.id), nome: d.nome }))} />
            </Campo>
            <Campo rotulo="Período">
              <Seleccao value={f.periodo} onChange={(e) => vm.alterar('periodo', e.target.value as typeof f.periodo)}
                opcoes={[{ valor: '', nome: 'Desde o início' }, { valor: '7', nome: 'Últimos 7 dias' }, { valor: '30', nome: 'Últimos 30 dias' }, { valor: '90', nome: 'Últimos 90 dias' }]} />
            </Campo>
            <Campo rotulo="Validação">
              <Seleccao vazio="Todos" value={f.validacao} onChange={(e) => vm.alterar('validacao', e.target.value as typeof f.validacao)}
                opcoes={Object.entries(VALIDACAO).map(([v, x]) => ({ valor: v, nome: x.nome }))} />
            </Campo>
            <Campo rotulo="Ordenar por">
              <Seleccao value={f.ordem} onChange={(e) => vm.alterar('ordem', e.target.value as typeof f.ordem)}
                opcoes={[{ valor: 'recentes', nome: 'Mais recentes' }, { valor: 'confianca', nome: 'Menos certos primeiro' }]} />
            </Campo>
            <label className="campo" style={{ width: 'auto', flexDirection: 'row', alignItems: 'center', gap: 8, height: 34 }}>
              <input type="checkbox" checked={f.soBaixa} onChange={(e) => vm.alterar('soBaixa', e.target.checked)} />
              <span style={{ fontSize: 13, color: 'var(--tinta-2)' }}>Só confiança abaixo de 60%</span>
            </label>
            {vm.activos > 0 && <Botao variante="fantasma" onClick={vm.limpar}>Limpar filtros ({vm.activos})</Botao>}
          </div>
        </div>
        {vm.erro ? (
          <div style={{ padding: 20 }}><div className="aviso-caixa critico"><CircleAlert size={16} />{vm.erro.message}</div></div>
        ) : vm.aCarregar ? (
          <div style={{ padding: 20, display: 'grid', gap: 12 }}>{[0, 1, 2, 3, 4].map((i) => <Esqueleto key={i} altura={36} />)}</div>
        ) : !vm.pagina?.itens.length ? (
          <Vazio titulo="Nenhum diagnóstico com estes filtros" icone={<ScanSearch size={28} />} />
        ) : (
          <>
            <div className="tabela-envolvente" style={{ opacity: vm.aActualizar ? 0.6 : 1 }}>
              <table className="tabela">
                <thead>
                  <tr>
                    <th>Previsão</th>
                    <th>Agricultor</th>
                    <th>Distrito</th>
                    <th>Data</th>
                    <th className="numero">Confiança</th>
                    <th>Validação</th>
                  </tr>
                </thead>
                <tbody>
                  {vm.pagina.itens.map((d) => (
                    <tr key={d.id} className="clicavel" onClick={() => vm.abrir(d)}>
                      <td className="celula-principal">
                        <strong>{d.patologia_nome ?? d.classe_prevista}</strong>
                        <span>{catalogo.nomeCultura(d.cultura_id)}{d.classe_confirmada && d.classe_confirmada !== d.classe_prevista
                          ? ` · corrigido para ${catalogo.nomeClasse(d.cultura_id, d.classe_confirmada)}` : ''}</span>
                      </td>
                      <td className="celula-principal"><strong>{d.utilizador_nome}</strong><span className="mono">{d.utilizador_telefone}</span></td>
                      <td>{d.distrito_nome ?? '—'}</td>
                      <td className="numeros secundario">{dataHora(d.data)}</td>
                      <td className="numero"><Confianca valor={d.confianca} /></td>
                      <td><Etiqueta tom={VALIDACAO[d.validacao].tom}>{VALIDACAO[d.validacao].nome}</Etiqueta></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Paginacao total={vm.pagina.total} limite={vm.limite} deslocamento={vm.deslocamento} aoMudar={vm.setDeslocamento} />
            {vm.pagina.total <= vm.limite && (
              <div className="paginacao"><span className="numeros">{numero(vm.pagina.total)} diagnósticos</span></div>
            )}
          </>
        )}
      </Cartao>
      <DetalheDiagnostico diagnostico={vm.aberto} aoFechar={vm.fechar} aoValidar={vm.validar} aValidar={vm.aValidar} />
    </>
  )
}
