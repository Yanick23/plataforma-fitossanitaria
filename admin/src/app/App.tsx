import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useSessao } from '@/nucleo/sessao'
import { Esqueleto } from '@/ui/componentes'
import { AlertasView } from '@/views/AlertasView'
import { CatalogoView } from '@/views/CatalogoView'
import { DiagnosticosView } from '@/views/DiagnosticosView'
import { EntradaView } from '@/views/EntradaView'
import { ModelosView } from '@/views/ModelosView'
import { PainelView } from '@/views/PainelView'
import { UtilizadoresView } from '@/views/UtilizadoresView'
import { AuditoriaView } from '@/views/AuditoriaView'
import { ValidacaoView } from '@/views/ValidacaoView'
import { VigilanciaView } from '@/views/VigilanciaView'
import { VisitasView } from '@/views/VisitasView'
import { Casca } from './Casca'

export function App() {
  const { utilizador, aVerificar, eAdministrador } = useSessao()
  if (aVerificar) {
    return <div style={{ padding: 48, maxWidth: 420 }}><Esqueleto altura={20} /><br /><Esqueleto altura={120} /></div>
  }
  if (!utilizador) return <EntradaView />
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Casca />}>
          <Route index element={<PainelView />} />
          <Route path="diagnosticos" element={<DiagnosticosView />} />
          <Route path="alertas" element={<AlertasView />} />
          <Route path="catalogo" element={<CatalogoView />} />
          <Route path="modelos" element={<ModelosView />} />
          <Route path="utilizadores" element={<UtilizadoresView />} />
          <Route path="vigilancia" element={<VigilanciaView />} />
          <Route path="validacao" element={<ValidacaoView />} />
          <Route path="visitas" element={<VisitasView />} />
          {eAdministrador && <Route path="auditoria" element={<AuditoriaView />} />}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
