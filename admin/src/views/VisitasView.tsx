import { CalendarCheck, CalendarClock, CircleAlert, CircleCheck, Phone, XCircle } from 'lucide-react'
import { dataHora, relativo } from '@/nucleo/formatos'
import { VISITA } from '@/nucleo/rotulos'
import { Botao, CabecalhoPagina, Campo, Cartao, Esqueleto, Etiqueta, Gaveta, Separadores, Vazio } from '@/ui/componentes'
import { useCatalogo } from '@/viewmodels/referencias'
import { useVisitasViewModel, type Separador } from '@/viewmodels/useVisitasViewModel'

export function VisitasView() {
  const vm = useVisitasViewModel()
  const catalogo = useCatalogo()
  const v = vm.aberta
  const fechada = v ? v.estado === 'RESOLVIDA' || v.estado === 'CANCELADA' : false

  const separadores: { valor: Separador; nome: string }[] = [
    { valor: 'PENDENTE', nome: `Pendentes (${vm.porEstado('PENDENTE')})` },
    { valor: 'AGENDADA', nome: `Agendadas (${vm.porEstado('AGENDADA')})` },
    { valor: 'RESOLVIDA', nome: 'Resolvidas' },
    { valor: 'TODAS', nome: 'Todas' },
  ]

  return (
    <>
      <CabecalhoPagina titulo="Visitas" descricao="Pedidos de ajuda feitos pelos agricultores a partir de um diagnóstico. Agende a visita, registe o que encontrou e feche o caso." />
      <Separadores valor={vm.separador} aoMudar={vm.setSeparador} opcoes={separadores} />
      <Cartao semMargem>
        {vm.erro ? <div style={{ padding: 20 }}><div className="aviso-caixa critico"><CircleAlert size={16} />{vm.erro.message}</div></div>
          : vm.aCarregar ? <div style={{ padding: 20 }}><Esqueleto altura={160} /></div>
            : vm.visitas.length === 0 ? <Vazio titulo="Sem pedidos neste estado" icone={<CalendarCheck size={28} />} /> : (
              <table className="tabela">
                <thead><tr><th>Agricultor</th><th>Problema</th><th>Distrito</th><th>Pedido</th><th>Visita</th><th>Estado</th></tr></thead>
                <tbody>
                  {vm.visitas.map((x) => (
                    <tr key={x.id} className="clicavel" onClick={() => vm.abrir(x)}>
                      <td className="celula-principal"><strong>{x.agricultor_nome}</strong><span className="mono">{x.agricultor_telefone}</span></td>
                      <td className="celula-principal"><strong style={{ fontWeight: 400 }}>{x.patologia_nome ?? x.classe_prevista}</strong>
                        <span style={{ maxWidth: 320, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{x.mensagem ?? catalogo.nomeCultura(x.cultura_id)}</span></td>
                      <td>{x.distrito_nome ?? '—'}</td>
                      <td className="secundario">{relativo(x.criado_em)}</td>
                      <td className="numeros">{x.data_agendada ? dataHora(x.data_agendada) : <span className="suave">—</span>}</td>
                      <td><Etiqueta tom={VISITA[x.estado].tom}>{VISITA[x.estado].nome}</Etiqueta></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
      </Cartao>

      <Gaveta
        aberta={Boolean(v)}
        titulo={v ? `Visita a ${v.agricultor_nome}` : ''}
        subtitulo={v ? `${v.patologia_nome ?? v.classe_prevista} · ${v.distrito_nome ?? 'sem distrito'} · pedido ${relativo(v.criado_em)}` : ''}
        aoFechar={vm.fechar}
        rodape={v && !fechada && (
          <>
            <Botao variante="fantasma" style={{ marginRight: 'auto' }} disabled={vm.aGuardar} onClick={vm.cancelar}><XCircle size={15} />Cancelar pedido</Botao>
            <Botao disabled={vm.aGuardar || !vm.quando} onClick={vm.agendar}><CalendarClock size={15} />{v.estado === 'AGENDADA' ? 'Reagendar' : 'Agendar'}</Botao>
            <Botao variante="primario" disabled={vm.aGuardar} onClick={vm.resolver}><CircleCheck size={15} />Marcar como resolvida</Botao>
          </>
        )}
      >
        {v && (
          <div className="formulario">
            <dl className="definicoes">
              <dt>Estado</dt><dd><Etiqueta tom={VISITA[v.estado].tom}>{VISITA[v.estado].nome}</Etiqueta>{v.tecnico_nome && <span className="suave pequeno"> · {v.tecnico_nome}</span>}</dd>
              <dt>Contacto</dt><dd><a href={`tel:${v.agricultor_telefone}`} className="mono"><Phone size={13} style={{ verticalAlign: -2 }} /> {v.agricultor_telefone}</a></dd>
              <dt>Diagnóstico</dt><dd>{v.patologia_nome ?? v.classe_prevista} ({catalogo.nomeCultura(v.cultura_id)})</dd>
              <dt>Mensagem</dt><dd>{v.mensagem ?? <span className="suave">sem mensagem</span>}</dd>
            </dl>
            {!fechada && (
              <Campo rotulo="Data e hora da visita" ajuda="O agricultor vê a data na app.">
                <input className="entrada" type="datetime-local" value={vm.quando} onChange={(e) => vm.setQuando(e.target.value)} />
              </Campo>
            )}
            <Campo rotulo="Notas do técnico" ajuda="O que observou e o que recomendou (o agricultor vê estas notas).">
              <textarea className="entrada" rows={5} value={vm.notas} disabled={fechada} onChange={(e) => vm.setNotas(e.target.value)} />
            </Campo>
            {fechada && v.notas_tecnico === null && <span className="suave pequeno">Caso fechado sem notas.</span>}
          </div>
        )}
      </Gaveta>
    </>
  )
}
