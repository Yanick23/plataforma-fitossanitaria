import { Link } from 'react-router-dom'
import { CircleCheck, Clock, Minus, Volume2 } from 'lucide-react'
import { numero } from '@/nucleo/formatos'
import { TIPO } from '@/nucleo/rotulos'
import { CabecalhoPagina, Cartao, Esqueleto, Separadores, Vazio } from '@/ui/componentes'
import { BarrasHorizontais } from '@/ui/graficos'
import { useCoberturaAudio } from '@/viewmodels/useAudiosViewModel'

/** Funcionalidade 14: o que já está gravado em cada língua e que línguas os agricultores escolheram. */
export function AudioView() {
  const vm = useCoberturaAudio()
  const c = vm.cobertura

  return (
    <>
      <CabecalhoPagina
        titulo="Línguas e áudio"
        descricao="Recomendações gravadas em voz, nas línguas dos agricultores, para quem lê pouco. Grava-se na gaveta de cada praga, em Culturas e pragas; a app toca as gravações sem Internet."
      />
      {vm.aCarregar || !c ? <Esqueleto altura={300} /> : (
        <>
          <div className="grelha grelha-2">
            <Cartao titulo="Línguas escolhidas pelos agricultores"
              subtitulo={`Na sua zona: ${numero(vm.totalAgricultores)} agricultores, ${numero(c.agricultores_sem_lingua)} sem língua escolhida (lêem o texto em português)`}>
              {vm.preferencias.length === 0
                ? <Vazio titulo="Nenhum agricultor escolheu ainda" texto="Cada agricultor escolhe a língua no registo ou nas Definições da app." icone={<Volume2 size={28} />} />
                : <BarrasHorizontais itens={vm.preferencias.map((p) => ({
                    ...p, detalhe: `${vm.prontas(p.chave)} pragas e doenças já com gravação validada nesta língua`,
                  }))} />}
            </Cartao>
            <Cartao titulo="Estado das gravações">
              <dl className="lista-definicoes">
                <dt>Pragas e doenças no catálogo</dt><dd>{numero(c.patologias.length)}</dd>
                <dt>Com pelo menos uma gravação na app</dt>
                <dd>{numero(c.patologias.filter((p) => Object.values(p.audios).some((a) => a.validado)).length)}</dd>
                <dt>Gravações à espera de validação</dt><dd>{numero(c.por_validar)}</dd>
              </dl>
              <p className="suave pequeno" style={{ marginTop: 12 }}>
                Comece pelas línguas mais escolhidas e pelas pragas mais diagnosticadas. Quem grava não valida a sua própria gravação.
              </p>
            </Cartao>
          </div>

          <Cartao titulo="O que já está gravado" semMargem
            subtitulo="✓ na app · relógio: por validar · traço: em falta. As colunas são o português e as línguas escolhidas ou já gravadas."
            accoes={<Separadores valor={vm.cultura} aoMudar={vm.setCultura}
              opcoes={[{ valor: '', nome: 'Todas' }, ...vm.culturas.map((x) => ({ valor: x.id, nome: x.nome }))]} />}>
            <div className="tabela-envolvente">
              <table className="tabela cobertura">
                <thead>
                  <tr>
                    <th>Praga ou doença</th>
                    {vm.colunas.map((l) => (
                      <th key={l.codigo} className="celula-lingua" title={`${numero(c.agricultores_por_lingua[l.codigo] ?? 0)} agricultores na sua zona`}>{l.nome}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {vm.linhas.map((p) => (
                    <tr key={p.patologia_id}>
                      <td className="celula-principal"><strong>{p.nome}</strong><span>{vm.nomeCultura(p.cultura_id)} · {TIPO[p.tipo].nome}</span></td>
                      {vm.colunas.map((l) => {
                        const a = p.audios[l.codigo]
                        return (
                          <td key={l.codigo} className="celula-lingua">
                            {!a ? <Minus size={14} aria-label="em falta" style={{ color: 'var(--tinta-3)' }} />
                              : a.validado ? <CircleCheck size={16} aria-label="na app" style={{ color: 'var(--bom-texto)' }} />
                                : <Clock size={16} aria-label="por validar" style={{ color: 'var(--aviso-texto)' }} />}
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="suave pequeno" style={{ padding: '12px 20px' }}>
              Para gravar, abra a praga em <Link to="/catalogo">Culturas e pragas</Link>.
            </p>
          </Cartao>
        </>
      )}
    </>
  )
}
