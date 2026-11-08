import { CircleAlert, ClipboardList, MessageSquareText, Plus, Users, XCircle } from 'lucide-react'
import type { EstadoCampanha } from '@/model/tipos'
import { data, numero, percentagem, resumoSMS } from '@/nucleo/formatos'
import type { Tom } from '@/nucleo/rotulos'
import { Botao, CabecalhoPagina, Campo, Cartao, Esqueleto, Etiqueta, Gaveta, Segmentos, Seleccao, Separadores, Vazio } from '@/ui/componentes'
import { useCatalogo, useRegioes } from '@/viewmodels/referencias'
import type { Ambito } from '@/viewmodels/useAlertasViewModel'
import { useCampanhasViewModel } from '@/viewmodels/useCampanhasViewModel'

const ESTADO: Record<EstadoCampanha, { nome: string; tom: Tom }> = {
  AGENDADA: { nome: 'Agendada', tom: 'info' },
  ACTIVA: { nome: 'A decorrer', tom: 'bom' },
  TERMINADA: { nome: 'Terminada', tom: 'neutro' },
  CANCELADA: { nome: 'Cancelada', tom: 'neutro' },
}
const NOME_AMBITO: Record<Ambito, string> = { distrito: 'Distrito', provincia: 'Província', pais: 'Todo o país' }

/** Campanhas de vigilância activa (funcionalidade 12). */
export function CampanhasView() {
  const vm = useCampanhasViewModel()
  const catalogo = useCatalogo()
  const regioes = useRegioes()
  const r = vm.rascunho

  return (
    <>
      <CabecalhoPagina
        titulo="Campanhas de vigilância"
        descricao="Peça aos agricultores de uma zona que fotografem uma cultura durante alguns dias, mesmo que pareça saudável. Mostra quem respondeu e onde há (ou não há) pragas."
        accoes={vm.podeCriar && <Botao variante="primario" onClick={vm.abrir}><Plus size={16} />Nova campanha</Botao>}
      />
      <Cartao semMargem>
        <div style={{ padding: '12px 20px 0' }}>
          <Separadores valor={vm.antigas ? 'todas' : 'recentes'} aoMudar={(v) => vm.setAntigas(v === 'todas')}
            opcoes={[{ valor: 'recentes', nome: 'A decorrer e recentes' }, { valor: 'todas', nome: 'Todas (incl. canceladas)' }]} />
        </div>
        {vm.erro ? <div style={{ padding: 20 }}><div className="aviso-caixa critico"><CircleAlert size={16} />{vm.erro.message}</div></div>
          : vm.aCarregar ? <div style={{ padding: 20 }}><Esqueleto altura={160} /></div>
            : vm.campanhas.length === 0
              ? <Vazio titulo="Nenhuma campanha" texto="Crie uma campanha para saber, numa semana, como estão as plantas de uma zona." icone={<ClipboardList size={28} />} />
              : (
                <div className="tabela-envolvente"><table className="tabela">
                  <thead><tr><th>Campanha</th><th>Zona</th><th>Período</th><th>Estado</th><th>Responderam</th><th className="numero">Casos</th><th /></tr></thead>
                  <tbody>
                    {vm.campanhas.map((c) => (
                      <tr key={c.id} style={{ opacity: c.estado === 'CANCELADA' ? 0.55 : 1 }}>
                        <td className="celula-principal" style={{ maxWidth: 380 }}>
                          <strong>{c.titulo}</strong>
                          <span>{catalogo.nomeCultura(c.cultura_id)}{c.patologia_nome ? ` · procurar ${c.patologia_nome.toLowerCase()}` : ''} · por {c.autor_nome}</span>
                        </td>
                        <td>{c.zona}</td>
                        <td className="numeros secundario">{data(`${c.inicio}T12:00:00`)} – {data(`${c.fim}T12:00:00`)}</td>
                        <td><Etiqueta tom={ESTADO[c.estado].tom}>{ESTADO[c.estado].nome}</Etiqueta></td>
                        <td>
                          <span className="confianca">
                            <span className="trilho"><span className="enchimento" style={{ width: `${Math.round((c.taxa_resposta ?? 0) * 100)}%` }} /></span>
                            {numero(c.responderam)} / {numero(c.agricultores)} ({percentagem(c.taxa_resposta)})
                          </span>
                          {c.sms && <div className="suave pequeno"><MessageSquareText size={12} style={{ verticalAlign: -2 }} /> SMS: {resumoSMS(c.sms)}</div>}
                        </td>
                        <td className="numero">
                          {numero(c.casos_praga_doenca)} <span className="suave pequeno">de {numero(c.diagnosticos)}</span>
                          {c.casos_patologia !== null && <div className="suave pequeno">{numero(c.casos_patologia)} de {c.patologia_nome?.toLowerCase()}</div>}
                        </td>
                        <td style={{ width: 1 }}>
                          {vm.podeCriar && (c.estado === 'ACTIVA' || c.estado === 'AGENDADA') && (
                            <Botao variante="fantasma" pequeno onClick={() => vm.cancelar(c.id)} title="Cancelar (deixa de aparecer na app)">
                              <XCircle size={14} />Cancelar
                            </Botao>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table></div>
              )}
        <p className="suave pequeno" style={{ margin: 0, padding: '10px 20px 14px', borderTop: '1px solid var(--linha)' }}>
          Respondeu = enviou pelo menos um diagnóstico da cultura, na zona, durante a campanha (também conta «folha saudável»).
          Casos = diagnósticos de praga ou doença, como previstos pelo modelo.
        </p>
      </Cartao>

      <Gaveta
        aberta={vm.aCriar}
        titulo="Nova campanha"
        subtitulo="Os agricultores da zona vêem o pedido na app (e, se escolher, por SMS)."
        aoFechar={vm.fechar}
        rodape={
          <>
            <span className="secundario pequeno" style={{ marginRight: 'auto', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <Users size={14} />
              {vm.erroAlcance ? vm.erroAlcance.message : vm.alcance
                ? <>Vai chegar a <strong style={{ color: 'var(--tinta)' }}>{numero(vm.alcance.destinatarios)}</strong> agricultor(es) · {vm.alcance.zona}</>
                : vm.aCalcularAlcance ? 'A calcular destinatários…' : 'Escolha a zona'}
            </span>
            <Botao onClick={vm.fechar}>Cancelar</Botao>
            <Botao variante="primario" disabled={!vm.valido || vm.aGuardar || Boolean(vm.erroAlcance)} onClick={vm.criar}>
              {vm.aGuardar ? 'A criar…' : 'Criar campanha'}
            </Botao>
          </>
        }
      >
        <div className="formulario">
          <Campo rotulo="Título">
            <input className="entrada" maxLength={120} value={r.titulo} onChange={(e) => vm.alterar('titulo', e.target.value)}
              placeholder="Ex.: Semana de vigilância da lagarta-do-funil" />
          </Campo>
          <Campo rotulo="Pedido ao agricultor" ajuda={`${r.mensagem.length}/1000`}>
            <textarea className="entrada" rows={4} maxLength={1000} value={r.mensagem} onChange={(e) => vm.alterar('mensagem', e.target.value)} />
          </Campo>
          <div className="linha">
            <Campo rotulo="Cultura">
              <Seleccao value={r.cultura} onChange={(e) => vm.alterar('cultura', e.target.value)}
                opcoes={catalogo.culturas.map((c) => ({ valor: c.id, nome: c.nome }))} />
            </Campo>
            <Campo rotulo="Praga a procurar (opcional)">
              <Seleccao vazio="Nenhuma em particular" value={r.patologia} onChange={(e) => vm.alterar('patologia', e.target.value)}
                opcoes={catalogo.patologiasDe(r.cultura).filter((p) => p.tipo !== 'SAUDAVEL').map((p) => ({ valor: String(p.id), nome: p.nome_local }))} />
            </Campo>
          </div>
          <Campo rotulo="Zona">
            {vm.ambitos.length > 1
              ? <Segmentos rotulo="Zona" valor={r.ambito} aoMudar={(v) => vm.alterar('ambito', v)} opcoes={vm.ambitos.map((a) => ({ valor: a, nome: NOME_AMBITO[a] }))} />
              : <span className="secundario">O seu distrito de actuação</span>}
          </Campo>
          {r.ambito !== 'pais' && (
            <div className="linha">
              <Campo rotulo="Província">
                <Seleccao vazio="Escolha…" value={vm.tecnicoDistrito ? regioes.distrito(Number(vm.tecnicoDistrito))?.provincia_codigo ?? '' : r.provincia}
                  disabled={Boolean(vm.tecnicoDistrito || vm.tecnicoProvincia)}
                  onChange={(e) => vm.alterar('provincia', e.target.value)} opcoes={regioes.opcoesProvincias} />
              </Campo>
              {r.ambito === 'distrito' && (
                <Campo rotulo="Distrito">
                  <Seleccao vazio="Escolha…" value={r.distrito} disabled={Boolean(vm.tecnicoDistrito)}
                    onChange={(e) => vm.alterar('distrito', e.target.value)}
                    opcoes={regioes.distritosDe(vm.tecnicoProvincia || r.provincia).map((d) => ({ valor: String(d.id), nome: d.nome }))} />
                </Campo>
              )}
            </div>
          )}
          <div className="linha">
            <Campo rotulo="Início">
              <input className="entrada" type="date" value={r.inicio} onChange={(e) => vm.alterar('inicio', e.target.value)} />
            </Campo>
            <Campo rotulo="Fim" erro={vm.datasValidas ? undefined : 'O fim tem de ser depois do início'} ajuda="No máximo 60 dias.">
              <input className="entrada" type="date" value={r.fim} min={r.inicio} onChange={(e) => vm.alterar('fim', e.target.value)} />
            </Campo>
          </div>
          <label style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
            <input type="checkbox" checked={r.sms} onChange={(e) => vm.alterar('sms', e.target.checked)} style={{ marginTop: 3 }} />
            <span>
              Avisar também por SMS
              <span className="suave pequeno" style={{ display: 'block' }}>
                {vm.alcance?.sms_simulacao
                  ? 'Modo de simulação: os SMS ficam registados, mas não saem (o fornecedor ainda não está configurado).'
                  : 'Cada agricultor da zona recebe um SMS com o pedido; cada SMS tem custo.'}
              </span>
            </span>
          </label>
        </div>
      </Gaveta>
    </>
  )
}
