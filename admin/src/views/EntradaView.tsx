import { useState, type FormEvent } from 'react'
import { CircleAlert } from 'lucide-react'
import { useSessao } from '@/nucleo/sessao'
import { Botao, Campo } from '@/ui/componentes'
import { SilhuetaMocambique } from '@/ui/graficos'

/** ViewModel do ecrã de entrada (simples: fica junto da View). */
function useEntradaViewModel() {
  const { entrar } = useSessao()
  const [telefone, setTelefone] = useState('')
  const [palavraPasse, setPalavraPasse] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [aEntrar, setAEntrar] = useState(false)
  const submeter = async (e: FormEvent) => {
    e.preventDefault()
    setErro(null)
    setAEntrar(true)
    try {
      await entrar(telefone, palavraPasse)
    } catch (err) {
      setErro((err as Error).message)
    } finally {
      setAEntrar(false)
    }
  }
  return { telefone, setTelefone, palavraPasse, setPalavraPasse, erro, aEntrar, submeter }
}

export function EntradaView() {
  const vm = useEntradaViewModel()
  return (
    <div className="entrada-pagina">
      <section className="entrada-painel">
        <div className="marca" style={{ padding: 0 }}>
          <img src="/marca.svg" alt="" />
          <div>
            <strong>Vigilância Fitossanitária</strong>
            <span>Painel de técnicos e administradores</span>
          </div>
        </div>
        <div>
          <h1>Entrar</h1>
          <p className="secundario" style={{ marginTop: 6 }}>Use o número de telefone e a palavra-passe da sua conta.</p>
        </div>
        <form className="formulario" onSubmit={vm.submeter}>
          <Campo rotulo="Telefone">
            <input className="entrada" inputMode="tel" autoComplete="username" placeholder="84 000 0000"
              value={vm.telefone} onChange={(e) => vm.setTelefone(e.target.value)} required />
          </Campo>
          <Campo rotulo="Palavra-passe">
            <input className="entrada" type="password" autoComplete="current-password"
              value={vm.palavraPasse} onChange={(e) => vm.setPalavraPasse(e.target.value)} required />
          </Campo>
          {vm.erro && <div className="aviso-caixa critico"><CircleAlert size={16} style={{ flex: 'none', marginTop: 2 }} />{vm.erro}</div>}
          <Botao type="submit" variante="primario" disabled={vm.aEntrar} style={{ height: 38 }}>
            {vm.aEntrar ? 'A entrar…' : 'Entrar'}
          </Botao>
        </form>
        <p className="suave pequeno">Os agricultores usam a aplicação móvel. As contas de técnico são criadas pelo administrador.</p>
      </section>
      <section className="entrada-ilustracao" aria-hidden="true">
        <div style={{ position: 'absolute', inset: '6% 12% 24% 20%' }}>
          <SilhuetaMocambique altura={540} />
        </div>
        <blockquote>
          Diagnósticos feitos no campo, mesmo sem rede, tornam-se informação para agir: onde está a lagarta-do-funil,
          que distritos precisam de visita e a quem enviar um alerta.
          <span>Instituto Superior de Transportes e Comunicações · Projecto Final de Curso</span>
        </blockquote>
      </section>
    </div>
  )
}
