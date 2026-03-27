import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import ValidatePage from './pages/ValidatePage'
import ProbePage from './pages/ProbePage'
import ExamplesPage from './pages/ExamplesPage'

export default function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<Navigate to="/validate" replace />} />
        <Route path="/validate" element={<ValidatePage />} />
        <Route path="/probe" element={<ProbePage />} />
        <Route path="/examples" element={<ExamplesPage />} />
      </Routes>
    </AppLayout>
  )
}
