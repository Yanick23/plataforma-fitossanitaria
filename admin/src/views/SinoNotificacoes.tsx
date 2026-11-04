import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bell, CheckCheck, ShieldAlert } from 'lucide-react'
import { relativo } from '@/nucleo/formatos'
import { Botao, Esqueleto } from '@/ui/componentes'
import { useNotificacoesViewModel } from '@/viewmodels/useNotificacoesViewModel'

/** Sino na barra de topo: avisos imediatos para a equipa (ex.: praga de declaração obrigatória confirmada). */
export function SinoNotificacoes() {
  const vm = useNotificacoesViewModel()
  const [aberto, setAberto] = useState(false)
  const caixa = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!aberto) return
    const fora = (e: MouseEvent) => { if (caixa.current && !caixa.current.contains(e.target as Node)) setAberto(false) }
    const tecla = (e: KeyboardEvent) => { if (e.key === 'Escape') setAberto(false) }
    document.addEventListener('mousedown', fora)
    document.addEventListener('keydown', tecla)
    return () => { document.removeEventListener('mousedown', fora); document.removeEventListener('keydown', tecla) }
  }, [aberto])

  if (!vm.disponivel) return null
  const rotulo = vm.naoLidas > 0 ? `Notificações: ${vm.naoLidas} por ler` : 'Notificações'

  return (
    <div className="sino" ref={caixa}>
      <Botao variante="fantasma" icone onClick={() => setAberto((a) => !a)} aria-label={rotulo} title={rotulo}
        aria-expanded={aberto} aria-haspopup="dialog">
        <Bell size={17} />
        {vm.naoLidas > 0 && <span className="sino-contador" aria-hidden>{vm.naoLidas > 9 ? '9+' : vm.naoLidas}</span>}
      </Botao>
      {aberto && (
        <div className="sino-painel" role="dialog" aria-label="Notificações">
          <div className="sino-cabecalho">
            <strong>Notificações</strong>
            {vm.naoLidas > 0 && (
              <Botao variante="fantasma" pequeno onClick={vm.marcarTodas}><CheckCheck size={14} />Marcar todas como lidas</Botao>
            )}
          </div>
          {vm.aCarregar ? <div style={{ padding: 16 }}><Esqueleto altura={48} /></div>
            : vm.itens.length === 0 ? (
              <p className="sino-vazio">Sem notificações. Quando um técnico confirmar um caso de praga de declaração obrigatória na sua zona, o aviso aparece aqui.</p>
            ) : (
              <ul className="sino-lista">
                {vm.itens.map((n) => (
                  <li key={n.id} className={n.lida_em ? 'lida' : undefined}>
                    <ShieldAlert size={16} className="sino-icone" aria-hidden />
                    <div>
                      <strong>{n.titulo}</strong>
                      <p>{n.mensagem}</p>
                      <div className="sino-accoes">
                        <span className="suave">{relativo(n.criado_em)}{n.lida_em ? ' · lida' : ''}</span>
                        <Link to="/vigilancia#declaracoes" onClick={() => { if (!n.lida_em) vm.marcarLida(n.id); setAberto(false) }}>Ver na Vigilância</Link>
                        {!n.lida_em && <button type="button" className="ligacao" onClick={() => vm.marcarLida(n.id)}>Marcar como lida</button>}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
        </div>
      )}
    </div>
  )
}
