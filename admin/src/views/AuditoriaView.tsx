import { CircleAlert, ScrollText } from 'lucide-react'
import { dataHora, relativo } from '@/nucleo/formatos'
import { ACCOES_AUDITORIA } from '@/nucleo/rotulos'
import { CabecalhoPagina, Campo, Cartao, Esqueleto, Gaveta, Paginacao, Seleccao, Vazio } from '@/ui/componentes'
import { diferencas, useAuditoriaViewModel } from '@/viewmodels/useAuditoriaViewModel'

const ENTIDADES = [
  { valor: 'alerta', nome: 'Alertas' }, { valor: 'patologia', nome: 'Pragas e doenças' }, { valor: 'cultura', nome: 'Culturas' },
  { valor: 'modelo', nome: 'Modelos' }, { valor: 'utilizador', nome: 'Contas' }, { valor: 'diagnostico', nome: 'Validações' },
  { valor: 'visita', nome: 'Visitas' },
]

export function AuditoriaView() {
  const vm = useAuditoriaViewModel()
  const r = vm.aberto

  return (
    <>
      <CabecalhoPagina titulo="Auditoria" descricao="Registo de todas as alterações feitas na plataforma: quem, o quê, quando, e os valores antes e depois." />
      <Cartao semMargem>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--linha)' }}>
          <div className="filtros">
            <Campo rotulo="Tipo de registo">
              <Seleccao vazio="Todos" value={vm.entidade} onChange={(e) => vm.setEntidade(e.target.value)} opcoes={ENTIDADES} />
            </Campo>
          </div>
        </div>
        {vm.erro ? <div style={{ padding: 20 }}><div className="aviso-caixa critico"><CircleAlert size={16} />{vm.erro.message}</div></div>
          : vm.aCarregar ? <div style={{ padding: 20 }}><Esqueleto altura={200} /></div>
            : !vm.pagina?.itens.length ? <Vazio titulo="Sem registos" icone={<ScrollText size={28} />} /> : (
              <>
                <table className="tabela">
                  <thead><tr><th>Quando</th><th>Quem</th><th>Acção</th><th>Registo</th><th>Alterações</th></tr></thead>
                  <tbody>
                    {vm.pagina.itens.map((x) => {
                      const d = diferencas(x)
                      return (
                        <tr key={x.id} className="clicavel" onClick={() => vm.abrir(x)}>
                          <td className="celula-principal"><strong style={{ fontWeight: 400 }}>{relativo(x.criado_em)}</strong><span>{dataHora(x.criado_em)}</span></td>
                          <td>{x.utilizador_nome ?? '—'}</td>
                          <td>{ACCOES_AUDITORIA[x.accao] ?? x.accao}</td>
                          <td className="mono suave">{x.entidade} {x.entidade_id ? `#${x.entidade_id.length > 12 ? `${x.entidade_id.slice(0, 8)}…` : x.entidade_id}` : ''}</td>
                          <td className="secundario">{d.length ? d.map((c) => c.campo).slice(0, 3).join(', ') + (d.length > 3 ? '…' : '') : '—'}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
                <Paginacao total={vm.pagina.total} limite={vm.limite} deslocamento={vm.deslocamento} aoMudar={vm.setDeslocamento} />
              </>
            )}
      </Cartao>
      <Gaveta aberta={Boolean(r)} titulo={r ? ACCOES_AUDITORIA[r.accao] ?? r.accao : ''} subtitulo={r ? `${r.utilizador_nome ?? '—'} · ${dataHora(r.criado_em)}` : ''} aoFechar={vm.fechar}>
        {r && (
          <>
            <dl className="definicoes"><dt>Registo</dt><dd className="mono">{r.entidade} {r.entidade_id}</dd><dt>Acção</dt><dd className="mono">{r.accao}</dd></dl>
            {diferencas(r).length === 0 ? <span className="suave">Sem detalhes registados.</span> : (
              <table className="tabela">
                <thead><tr><th>Campo</th><th>Antes</th><th>Depois</th></tr></thead>
                <tbody>
                  {diferencas(r).map((c) => (
                    <tr key={c.campo}>
                      <td className="mono">{c.campo}</td>
                      <td className="secundario" style={{ whiteSpace: 'pre-wrap', maxWidth: 220 }}>{c.antes}</td>
                      <td style={{ whiteSpace: 'pre-wrap', maxWidth: 220 }}>{c.depois}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </>
        )}
      </Gaveta>
    </>
  )
}
