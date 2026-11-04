import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'
import { CircleAlert, CircleCheck } from 'lucide-react'

interface Notificacao {
  id: number
  texto: string
  tipo: 'sucesso' | 'erro'
}

const Contexto = createContext<(texto: string, tipo?: Notificacao['tipo']) => void>(() => {})

export function FornecedorNotificacoes({ children }: { children: ReactNode }) {
  const [lista, setLista] = useState<Notificacao[]>([])
  const notificar = useCallback((texto: string, tipo: Notificacao['tipo'] = 'sucesso') => {
    const id = Date.now() + Math.random()
    setLista((l) => [...l, { id, texto, tipo }])
    setTimeout(() => setLista((l) => l.filter((n) => n.id !== id)), tipo === 'erro' ? 6000 : 3500)
  }, [])
  return (
    <Contexto.Provider value={notificar}>
      {children}
      <div className="notificacoes" role="status" aria-live="polite">
        {lista.map((n) => (
          <div key={n.id} className="notificacao">
            {n.tipo === 'erro' ? <CircleAlert size={16} color="#e66767" /> : <CircleCheck size={16} color="#3fb06e" />}
            {n.texto}
          </div>
        ))}
      </div>
    </Contexto.Provider>
  )
}

export const useNotificar = () => useContext(Contexto)
