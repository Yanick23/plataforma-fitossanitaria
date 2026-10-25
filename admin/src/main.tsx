import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import '@fontsource/ibm-plex-sans/400.css'
import '@fontsource/ibm-plex-sans/500.css'
import '@fontsource/ibm-plex-sans/600.css'
import '@fontsource/ibm-plex-mono/400.css'
import './estilos/tokens.css'
import './estilos/base.css'
import './estilos/componentes.css'
import { App } from './app/App'
import { FornecedorNotificacoes } from './nucleo/notificacoes'
import { FornecedorSessao } from './nucleo/sessao'

const cliente = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false },
  },
})

createRoot(document.getElementById('raiz')!).render(
  <StrictMode>
    <QueryClientProvider client={cliente}>
      <FornecedorNotificacoes>
        <FornecedorSessao>
          <App />
        </FornecedorSessao>
      </FornecedorNotificacoes>
    </QueryClientProvider>
  </StrictMode>,
)
