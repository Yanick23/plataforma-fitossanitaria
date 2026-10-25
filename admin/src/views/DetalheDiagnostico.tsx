import { useEffect, useState } from 'react'
import { CircleCheck, PenLine } from 'lucide-react'
import type { Diagnostico } from '@/model/tipos'
import { diagnosticosRepo } from '@/model/repositorios'
import { dataHora, numero } from '@/nucleo/formatos'
import { TIPO, VALIDACAO } from '@/nucleo/rotulos'
import { Botao, Campo, Confianca, Etiqueta, Gaveta, ImagemProtegida, Segmentos, Seleccao } from '@/ui/componentes'
import { useCatalogo } from '@/viewmodels/referencias'

/** Gaveta com a foto, o Grad-CAM e a validação de um diagnóstico (usada em Diagnósticos e Validação). */
export function DetalheDiagnostico({ diagnostico: d, aoFechar, aoValidar, aValidar }:
  { diagnostico: Diagnostico | null; aoFechar: () => void; aoValidar: (id: string, classe: string, nota: string) => void; aValidar: boolean }) {
  const catalogo = useCatalogo()
  const [vista, setVista] = useState<'foto' | 'gradcam'>('foto')
  const [classe, setClasse] = useState('')
  const [nota, setNota] = useState('')

  useEffect(() => {
    if (!d) return
    setVista('foto')
    setClasse(d.classe_confirmada ?? d.classe_prevista)
    setNota(d.nota_tecnico ?? '')
  }, [d])

  if (!d) return null
  const opcoes = catalogo.patologiasDe(d.cultura_id).map((p) => ({ valor: p.codigo, nome: p.nome_local }))
  const corrigir = classe !== d.classe_prevista

  return (
    <Gaveta
      aberta
      larga
      titulo={d.patologia_nome ?? d.classe_prevista}
      subtitulo={`${catalogo.nomeCultura(d.cultura_id)} · ${dataHora(d.data)}`}
      aoFechar={aoFechar}
      rodape={
        <>
          <Botao onClick={aoFechar}>Fechar</Botao>
          <Botao variante="primario" disabled={aValidar} onClick={() => aoValidar(d.id, classe, nota)}>
            {corrigir ? <PenLine size={15} /> : <CircleCheck size={15} />}
            {aValidar ? 'A guardar…' : corrigir ? 'Guardar correcção' : 'Confirmar diagnóstico'}
          </Botao>
        </>
      }
    >
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.1fr) minmax(0, 1fr)', gap: 20 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <Segmentos rotulo="Imagem" valor={vista} aoMudar={setVista}
            opcoes={[{ valor: 'foto', nome: 'Fotografia' }, { valor: 'gradcam', nome: 'Onde o modelo olhou' }]} />
          {d.tem_imagem ? (
            <ImagemProtegida
              key={vista}
              caminho={vista === 'foto' ? diagnosticosRepo.caminhoImagem(d.id) : diagnosticosRepo.caminhoGradcam(d.id)}
              alt={vista === 'foto' ? 'Fotografia da folha' : 'Mapa Grad-CAM'}
              altura={320}
              className="foto-diagnostico"
            />
          ) : (
            <div className="aviso-caixa">A fotografia ainda não foi enviada pela app.</div>
          )}
          {vista === 'gradcam' && <p className="suave pequeno">Zonas a vermelho: as que mais pesaram na decisão do modelo (Grad-CAM, calculado no servidor).</p>}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <dl className="definicoes">
            <dt>Previsão do modelo</dt>
            <dd>{d.patologia_nome ?? d.classe_prevista} {d.tipo && <Etiqueta tom={TIPO[d.tipo].tom}>{TIPO[d.tipo].nome}</Etiqueta>}</dd>
            <dt>Confiança</dt>
            <dd><Confianca valor={d.confianca} /></dd>
            <dt>Agricultor</dt>
            <dd>{d.utilizador_nome}<div className="suave pequeno mono">{d.utilizador_telefone}</div></dd>
            <dt>Distrito</dt>
            <dd>{d.distrito_nome ?? '—'}</dd>
            <dt>Modelo</dt>
            <dd>v{d.versao_modelo ?? '—'} · inferência {d.tempo_inferencia_ms ? `${numero(d.tempo_inferencia_ms)} ms` : '—'}</dd>
            <dt>Validação</dt>
            <dd>
              <Etiqueta tom={VALIDACAO[d.validacao].tom}>{VALIDACAO[d.validacao].nome}</Etiqueta>
              {d.tecnico_nome && <div className="suave pequeno">por {d.tecnico_nome}{d.validado_em ? ` · ${dataHora(d.validado_em)}` : ''}</div>}
            </dd>
          </dl>
          <div className="formulario" style={{ paddingTop: 14, borderTop: '1px solid var(--linha)' }}>
            <h3>Validação pelo técnico</h3>
            <Campo rotulo="Classe correcta" ajuda={corrigir ? 'Vai registar uma correcção ao modelo.' : 'Igual à previsão: confirma o diagnóstico.'}>
              <Seleccao value={classe} onChange={(e) => setClasse(e.target.value)} opcoes={opcoes} />
            </Campo>
            <Campo rotulo="Nota para o agricultor (opcional)" ajuda="Aparece no historial da app, junto ao diagnóstico.">
              <textarea className="entrada" value={nota} onChange={(e) => setNota(e.target.value)} maxLength={1000}
                placeholder="Ex.: Confirmado na visita. Retire as folhas mais afectadas." />
            </Campo>
          </div>
        </div>
      </div>
    </Gaveta>
  )
}
