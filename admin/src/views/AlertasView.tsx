import { useLocation } from 'react-router-dom'
import { Archive, BellRing, CircleAlert, Info, Megaphone, Send, TriangleAlert, Users } from 'lucide-react'
import type { NivelAlerta } from '@/model/tipos'
import { data, numero, percentagem, relativo } from '@/nucleo/formatos'
import { NIVEL } from '@/nucleo/rotulos'
import { Botao, CabecalhoPagina, Campo, Cartao, Esqueleto, Etiqueta, Gaveta, Segmentos, Seleccao, Separadores, Vazio } from '@/ui/componentes'
import { useAlertasViewModel, type Ambito, type Preenchimento } from '@/viewmodels/useAlertasViewModel'
import { useCatalogo, useRegioes } from '@/viewmodels/referencias'

const ICONE_NIVEL: Record<NivelAlerta, typeof Info> = { INFORMACAO: Info, AVISO: TriangleAlert, URGENTE: CircleAlert }
const NOME_AMBITO: Record<Ambito, string> = { distrito: 'Distrito', provincia: 'Província', pais: 'Todo o país' }

export function AlertasView() {
  const local = useLocation()
  const vm = useAlertasViewModel((local.state as { preencher?: Preenchimento } | null)?.preencher)
  const catalogo = useCatalogo()
  const regioes = useRegioes()
  const r = vm.rascunho
  const patologia = r.patologia ? catalogo.patologias.find((p) => String(p.id) === r.patologia) : undefined

  return (
    <>
      <CabecalhoPagina
        titulo="Alertas"
        descricao="Avisos enviados aos agricultores de um distrito, de uma província ou do país. Chegam à aplicação na sincronização seguinte."
        accoes={<Botao variante="primario" onClick={vm.abrirComposicao}><Megaphone size={16} />Novo alerta</Botao>}
      />
      <Separadores valor={vm.arquivados ? 'arquivados' : 'activos'} aoMudar={(v) => vm.setArquivados(v === 'arquivados')}
        opcoes={[{ valor: 'activos', nome: 'Activos' }, { valor: 'arquivados', nome: 'Todos (incl. arquivados)' }]} />
      <Cartao semMargem>
        {vm.erro ? (
          <div style={{ padding: 20 }}><div className="aviso-caixa critico"><CircleAlert size={16} />{vm.erro.message}</div></div>
        ) : vm.aCarregar ? (
          <div style={{ padding: 20, display: 'grid', gap: 12 }}>{[0, 1, 2].map((i) => <Esqueleto key={i} altura={44} />)}</div>
        ) : vm.alertas.length === 0 ? (
          <Vazio titulo="Nenhum alerta" texto="Envie o primeiro alerta para os agricultores da sua zona." icone={<BellRing size={28} />} />
        ) : (
          <div className="tabela-envolvente">
            <table className="tabela">
              <thead>
                <tr><th>Alerta</th><th>Nível</th><th>Zona</th><th>Enviado</th><th className="numero">Lido por</th><th /></tr>
              </thead>
              <tbody>
                {vm.alertas.map((a) => {
                  const Icone = ICONE_NIVEL[a.nivel]
                  const taxa = a.destinatarios ? a.lidos / a.destinatarios : null
                  return (
                    <tr key={a.id} style={{ opacity: a.arquivado ? 0.55 : 1 }}>
                      <td className="celula-principal" style={{ maxWidth: 420 }}>
                        <strong>{a.titulo}</strong>
                        <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {a.patologia_nome ? `${a.patologia_nome} · ` : ''}{a.mensagem}
                        </span>
                      </td>
                      <td><Etiqueta tom={NIVEL[a.nivel].tom} icone={<Icone size={12} />}>{NIVEL[a.nivel].nome}</Etiqueta></td>
                      <td>{a.zona}</td>
                      <td className="celula-principal"><strong style={{ fontWeight: 400 }}>{relativo(a.criado_em)}</strong><span>por {a.autor_nome}{a.expira_em ? ` · até ${data(a.expira_em)}` : ''}</span></td>
                      <td className="numero">
                        {numero(a.lidos)} / {numero(a.destinatarios)}
                        <div className="suave pequeno">{percentagem(taxa)}</div>
                      </td>
                      <td style={{ width: 1 }}>
                        {!a.arquivado && (
                          <Botao variante="fantasma" pequeno onClick={() => vm.arquivar(a.id)} title="Arquivar (deixa de aparecer na app)">
                            <Archive size={14} />Arquivar
                          </Botao>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Cartao>

      <Gaveta
        aberta={vm.aCompor}
        larga
        titulo="Novo alerta"
        subtitulo="Escreva como falaria com o agricultor: o que se passa e o que deve fazer."
        aoFechar={vm.fecharComposicao}
        rodape={
          <>
            <span className="secundario pequeno" style={{ marginRight: 'auto', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <Users size={14} />
              {vm.erroAlcance ? vm.erroAlcance.message : vm.alcance
                ? <>Vai chegar a <strong style={{ color: 'var(--tinta)' }}>{numero(vm.alcance.destinatarios)}</strong> agricultor(es) · {vm.alcance.zona}</>
                : vm.aCalcularAlcance ? 'A calcular destinatários…' : 'Escolha a zona de destino'}
            </span>
            <Botao onClick={vm.fecharComposicao}>Cancelar</Botao>
            <Botao variante="primario" disabled={!vm.valido || vm.aEnviar || Boolean(vm.erroAlcance)} onClick={vm.enviar}>
              <Send size={15} />{vm.aEnviar ? 'A enviar…' : 'Enviar alerta'}
            </Botao>
          </>
        }
      >
        <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start', flexWrap: 'wrap' }}>
          <div className="formulario" style={{ flex: '1 1 340px', minWidth: 0 }}>
            <Campo rotulo="Título">
              <input className="entrada" maxLength={120} value={r.titulo} onChange={(e) => vm.alterar('titulo', e.target.value)}
                placeholder="Ex.: Lagarta-do-funil em Marracuene" />
            </Campo>
            <Campo rotulo="Mensagem" ajuda={`${r.mensagem.length}/2000`}>
              <textarea className="entrada" maxLength={2000} rows={6} value={r.mensagem} onChange={(e) => vm.alterar('mensagem', e.target.value)}
                placeholder="O que foi observado, onde, e o que o agricultor deve fazer agora." />
            </Campo>
            <Campo rotulo="Nível">
              <Segmentos rotulo="Nível" valor={r.nivel} aoMudar={(v) => vm.alterar('nivel', v)}
                opcoes={(['INFORMACAO', 'AVISO', 'URGENTE'] as NivelAlerta[]).map((n) => ({ valor: n, nome: NIVEL[n].nome }))} />
            </Campo>
            <Campo rotulo="Praga ou doença (opcional)">
              <select className="entrada" value={r.patologia} onChange={(e) => vm.alterar('patologia', e.target.value)}>
                <option value="">Nenhuma em particular</option>
                {catalogo.culturas.map((c) => (
                  <optgroup key={c.id} label={c.nome}>
                    {catalogo.patologiasDe(c.id).filter((p) => p.tipo !== 'SAUDAVEL').map((p) => (
                      <option key={p.id} value={p.id}>{p.nome_local}</option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </Campo>
            <Campo rotulo="Destino">
              {vm.ambitos.length > 1
                ? <Segmentos rotulo="Destino" valor={r.ambito} aoMudar={(v) => vm.alterar('ambito', v)} opcoes={vm.ambitos.map((a) => ({ valor: a, nome: NOME_AMBITO[a] }))} />
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
            <Campo rotulo="Válido até" ajuda="Depois desta data deixa de aparecer na app. Vazio = até ser arquivado.">
              <input className="entrada" type="date" value={r.validade} min={new Date().toISOString().slice(0, 10)}
                onChange={(e) => vm.alterar('validade', e.target.value)} />
            </Campo>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center' }}>
            <span className="suave pequeno">Como o agricultor vai ver</span>
            <div className="telemovel">
              <div className="telemovel-ecra">
                <span className="t-cultura" style={{
                  color: r.nivel === 'URGENTE' ? '#b91c1c' : r.nivel === 'AVISO' ? '#92400e' : '#1d4ed8',
                  background: r.nivel === 'URGENTE' ? '#fde8e8' : r.nivel === 'AVISO' ? '#fdf1d5' : '#e3eefb',
                }}>
                  {NIVEL[r.nivel].nome}{patologia ? ` · ${catalogo.nomeCultura(patologia.cultura_id)}` : ''}
                </span>
                <h4>{r.titulo || 'Título do alerta'}</h4>
                {patologia && <em>{patologia.nome_local} — {patologia.nome_cientifico}</em>}
                <div className="t-recomendacao">
                  <b>Mensagem</b>
                  {r.mensagem || 'A mensagem aparece aqui.'}
                </div>
                <span style={{ fontSize: 11, color: '#6b7280', marginTop: 'auto' }}>
                  {vm.alcance?.zona ?? '—'}{r.validade ? ` · válido até ${data(`${r.validade}T12:00:00`)}` : ''}
                </span>
              </div>
            </div>
          </div>
        </div>
      </Gaveta>
    </>
  )
}
