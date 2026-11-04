import { CircleAlert, KeyRound, Search, UserPlus, Users } from 'lucide-react'
import type { Perfil } from '@/model/tipos'
import { data, numero } from '@/nucleo/formatos'
import { PERFIL } from '@/nucleo/rotulos'
import { Botao, CabecalhoPagina, Campo, Cartao, Esqueleto, Etiqueta, Gaveta, Paginacao, Segmentos, Seleccao, Vazio } from '@/ui/componentes'
import { semZona, useUtilizadoresViewModel } from '@/viewmodels/useUtilizadoresViewModel'
import { useRegioes } from '@/viewmodels/referencias'

const DESCRICAO_PERFIL: Record<Perfil, string> = {
  AGRICULTOR: 'Usa a app: diagnostica, recebe alertas e pede visitas.',
  TECNICO: 'Valida diagnósticos, envia alertas e agenda visitas no seu distrito (ou província, sem distrito).',
  COORDENADOR: 'O que o técnico faz, em toda a província, mais gerir as contas de técnicos e agricultores. Recebe os avisos de declaração obrigatória.',
  INVESTIGADOR: 'Só leitura, no país todo: indicadores, vigilância, boletim e exportação, sem nomes nem telefones dos agricultores.',
  ADMINISTRADOR: 'Tudo, no país todo: catálogo, modelos, contas e auditoria.',
}

export function UtilizadoresView() {
  const vm = useUtilizadoresViewModel()
  const regioes = useRegioes()
  const f = vm.form
  const proprio = f?.id === vm.euId

  return (
    <>
      <CabecalhoPagina
        titulo="Utilizadores"
        descricao={vm.eAdministrador
          ? 'Todas as contas. O perfil e a zona de cada conta decidem o que vê, o que pode alterar e para onde pode enviar alertas.'
          : vm.eCoordenador
            ? 'Os agricultores e técnicos da sua província. Pode criar contas de técnico, mudar a zona e desactivar contas.'
            : 'Os agricultores registados na sua zona de actuação.'}
        accoes={vm.eGestor && <Botao variante="primario" onClick={vm.nova}><UserPlus size={16} />Nova conta</Botao>}
      />
      <Cartao semMargem>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--linha)' }}>
          <div className="filtros">
            <label className="campo largo">
              <span>Pesquisar</span>
              <div style={{ position: 'relative' }}>
                <Search size={15} style={{ position: 'absolute', left: 10, top: 10, color: 'var(--tinta-3)' }} />
                <input className="entrada" style={{ paddingLeft: 32 }} placeholder="Nome ou telefone" value={vm.pesquisa} onChange={(e) => vm.setPesquisa(e.target.value)} />
              </div>
            </label>
            {vm.eGestor && (
              <Campo rotulo="Perfil">
                <Seleccao vazio="Todos" value={vm.filtros.perfil} onChange={(e) => vm.alterarFiltro('perfil', e.target.value as Perfil | '')}
                  opcoes={vm.perfisAtribuiveis.map((p) => ({ valor: p, nome: PERFIL[p].nome }))} />
              </Campo>
            )}
            {!vm.eCoordenador && (
              <Campo rotulo="Província">
                <Seleccao vazio="Todas" value={vm.filtros.provincia} onChange={(e) => vm.alterarFiltro('provincia', e.target.value)} opcoes={regioes.opcoesProvincias} />
              </Campo>
            )}
            <Campo rotulo="Distrito">
              <Seleccao vazio="Todos" value={vm.filtros.distrito} onChange={(e) => vm.alterarFiltro('distrito', e.target.value)}
                opcoes={regioes.distritosDe(vm.eCoordenador ? vm.provinciaFixa : vm.filtros.provincia).map((d) => ({ valor: String(d.id), nome: d.nome }))} />
            </Campo>
            <Campo rotulo="Estado">
              <Seleccao vazio="Todos" value={vm.filtros.estado} onChange={(e) => vm.alterarFiltro('estado', e.target.value as '' | 'activo' | 'inactivo')}
                opcoes={[{ valor: 'activo', nome: 'Activas' }, { valor: 'inactivo', nome: 'Desactivadas' }]} />
            </Campo>
          </div>
        </div>
        {vm.erro ? <div style={{ padding: 20 }}><div className="aviso-caixa critico"><CircleAlert size={16} />{vm.erro.message}</div></div>
          : vm.aCarregar ? <div style={{ padding: 20, display: 'grid', gap: 12 }}>{[0, 1, 2, 3].map((i) => <Esqueleto key={i} altura={36} />)}</div>
            : !vm.pagina?.itens.length ? <Vazio titulo="Nenhuma conta encontrada" icone={<Users size={28} />} /> : (
              <>
                <div className="tabela-envolvente">
                  <table className="tabela">
                    <thead><tr><th>Nome</th><th>Perfil</th><th>Zona</th><th className="numero">Diagnósticos</th><th>Registo</th><th>Estado</th></tr></thead>
                    <tbody>
                      {vm.pagina.itens.map((u) => (
                        <tr key={u.id} className={vm.eGestor ? 'clicavel' : undefined} onClick={() => vm.eGestor && vm.abrir(u)}>
                          <td className="celula-principal"><strong>{u.nome}</strong><span className="mono">{u.telefone}</span></td>
                          <td><Etiqueta tom={PERFIL[u.perfil].tom}>{PERFIL[u.perfil].nome}</Etiqueta></td>
                          <td className="celula-principal">
                            <strong style={{ fontWeight: 400 }}>{semZona(u.perfil) ? 'Todo o país' : u.perfil === 'COORDENADOR' && u.provincia_nome ? `Província de ${u.provincia_nome}` : u.distrito_nome ?? (u.provincia_nome ? `Província de ${u.provincia_nome}` : '—')}</strong>
                            {u.distrito_nome && <span>{u.provincia_nome}</span>}
                          </td>
                          <td className="numero">{numero(u.diagnosticos)}</td>
                          <td className="numeros secundario">{data(u.criado_em)}</td>
                          <td>{u.activo ? <Etiqueta tom="bom">Activa</Etiqueta> : <Etiqueta tom="critico">Desactivada</Etiqueta>}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <Paginacao total={vm.pagina.total} limite={vm.limite} deslocamento={vm.deslocamento} aoMudar={vm.setDeslocamento} />
              </>
            )}
      </Cartao>

      <Gaveta
        aberta={Boolean(f)}
        titulo={f?.id === null ? 'Nova conta' : f?.nome ?? ''}
        subtitulo={f?.id === null
          ? vm.eCoordenador ? 'A conta fica na sua província.' : 'As contas da equipa (técnico, coordenador, investigador, administrador) só se criam aqui.'
          : f?.telefone}
        aoFechar={vm.fechar}
        rodape={
          <>
            <Botao onClick={vm.fechar}>Cancelar</Botao>
            <Botao variante="primario" disabled={!vm.valido || vm.aGuardar} onClick={vm.guardar}>{vm.aGuardar ? 'A guardar…' : f?.id === null ? 'Criar conta' : 'Guardar'}</Botao>
          </>
        }
      >
        {f && (
          <div className="formulario">
            <Campo rotulo="Nome"><input className="entrada" value={f.nome} onChange={(e) => vm.alterar('nome', e.target.value)} /></Campo>
            {f.id === null && (
              <div className="linha">
                <Campo rotulo="Telefone"><input className="entrada" inputMode="tel" value={f.telefone} onChange={(e) => vm.alterar('telefone', e.target.value)} placeholder="84 000 0000" /></Campo>
                <Campo rotulo="Palavra-passe inicial" ajuda="Mínimo 6 caracteres"><input className="entrada" type="text" value={f.palavra_passe} onChange={(e) => vm.alterar('palavra_passe', e.target.value)} /></Campo>
              </div>
            )}
            <Campo rotulo="Perfil" ajuda={proprio ? 'Não pode alterar o perfil da sua própria conta.' : DESCRICAO_PERFIL[f.perfil]}>
              {proprio
                ? <div><Etiqueta tom={PERFIL[f.perfil].tom}>{PERFIL[f.perfil].nome}</Etiqueta></div>
                : vm.perfisAtribuiveis.length <= 3
                  ? <Segmentos rotulo="Perfil" valor={f.perfil} aoMudar={(v: Perfil) => vm.alterar('perfil', v)}
                      opcoes={vm.perfisAtribuiveis.map((p) => ({ valor: p, nome: PERFIL[p].nome }))} />
                  : <Seleccao value={f.perfil} onChange={(e) => vm.alterar('perfil', e.target.value as Perfil)}
                      opcoes={vm.perfisAtribuiveis.map((p) => ({ valor: p, nome: PERFIL[p].nome }))} />}
            </Campo>
            {!semZona(f.perfil) && (
              <div className="linha">
                <Campo rotulo="Província" ajuda={vm.eCoordenador ? 'A sua província.' : f.perfil === 'COORDENADOR' && !f.provincia ? 'Obrigatória para o coordenador.' : undefined}>
                  <Seleccao vazio="—" value={f.provincia} disabled={vm.eCoordenador} onChange={(e) => vm.alterar('provincia', e.target.value)} opcoes={regioes.opcoesProvincias} />
                </Campo>
                {f.perfil !== 'COORDENADOR' && (
                  <Campo rotulo="Distrito" ajuda={f.perfil === 'TECNICO' && !f.distrito && f.provincia ? 'Sem distrito: técnico provincial (toda a província).' : undefined}>
                    <Seleccao vazio="—" value={f.distrito} onChange={(e) => vm.alterar('distrito', e.target.value)}
                      opcoes={regioes.distritosDe(f.provincia).map((d) => ({ valor: String(d.id), nome: d.nome }))} />
                  </Campo>
                )}
              </div>
            )}
            {f.id !== null && (
              <>
                <label style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <input type="checkbox" checked={f.activo} disabled={proprio} onChange={(e) => vm.alterar('activo', e.target.checked)} />
                  Conta activa {!f.activo && <span className="suave pequeno">— o utilizador não consegue entrar nem sincronizar</span>}
                </label>
                <div className="formulario" style={{ paddingTop: 16, borderTop: '1px solid var(--linha)' }}>
                  <h3>Repor palavra-passe</h3>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
                    <Campo rotulo="Nova palavra-passe"><input className="entrada" value={vm.novaPalavraPasse} onChange={(e) => vm.setNovaPalavraPasse(e.target.value)} /></Campo>
                    <Botao disabled={vm.novaPalavraPasse.length < 6 || vm.aRepor} onClick={vm.repor}><KeyRound size={15} />Repor</Botao>
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </Gaveta>
    </>
  )
}
