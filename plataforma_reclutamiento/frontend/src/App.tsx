import { BrowserRouter, Routes, Route, Navigate, useParams, useNavigate } from 'react-router-dom'
import { Toaster } from 'sonner'

// Pages
import Login from './pages/Login'
import Apply from './pages/Apply'
import SuperAdminDashboard from './pages/SuperAdminDashboard'
import SupervisorDashboard from './pages/SupervisorDashboard'
import ProcesoDetalle from './pages/ProcesoDetalle'
import CandidateDetail from './pages/CandidateDetail'
import Settings from './pages/Settings'

import { api } from './lib/api'

// ============================================================================
// Candidate Detail Wrapper (extracts ID from URL)
// ============================================================================

function CandidateDetailWrapper() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  
  if (!id) {
    return <Navigate to="/" replace />
  }
  
  return (
    <CandidateDetail 
      candidateId={id} 
      onBack={() => navigate(-1)} 
    />
  )
}

// ============================================================================
// Protected Route
// ============================================================================

function ProtectedRoute({ 
  children, 
  allowedRoles 
}: { 
  children: React.ReactNode
  allowedRoles?: string[]
}) {
  const user = api.getStoredUser()
  
  if (!api.isAuthenticated() || !user) {
    return <Navigate to="/login" replace />
  }
  
  if (allowedRoles && !allowedRoles.includes(user.rol)) {
    // Redirigir según rol
    if (user.rol === 'superadmin') {
      return <Navigate to="/admin" replace />
    } else if (user.rol === 'supervisor') {
      return <Navigate to="/dashboard" replace />
    }
    return <Navigate to="/" replace />
  }
  
  return <>{children}</>
}

// ============================================================================
// Smart Dashboard Redirect
// ============================================================================

function DashboardRedirect() {
  const user = api.getStoredUser()
  
  if (!api.isAuthenticated() || !user) {
    return <Navigate to="/login" replace />
  }
  
  // Redirigir según rol
  if (user.rol === 'superadmin') {
    return <Navigate to="/admin" replace />
  } else if (user.rol === 'supervisor') {
    return <Navigate to="/supervisor" replace />
  }
  
  // Usuario básico va a aplicar
  return <Navigate to="/postular" replace />
}

// ============================================================================
// App Router
// ============================================================================

function App() {
  return (
    <>
      <Toaster 
        theme="dark" 
        position="bottom-right"
        toastOptions={{
          style: {
            background: '#18181b',
            border: '1px solid rgba(255,255,255,0.1)',
            color: '#fff',
          },
        }}
      />
      
      <BrowserRouter>
        <Routes>
          {/* ========== Rutas Públicas ========== */}
          <Route path="/login" element={<Login />} />
          <Route path="/postular" element={<Apply />} />
          
          {/* ========== Redireccion Inteligente ========== */}
          <Route path="/" element={
            api.isAuthenticated() 
              ? <DashboardRedirect /> 
              : <Navigate to="/login" replace />
          } />
          
          <Route path="/dashboard" element={<DashboardRedirect />} />
          
          {/* ========== SuperAdmin Dashboard ========== */}
          <Route 
            path="/admin" 
            element={
              <ProtectedRoute allowedRoles={['superadmin']}>
                <SuperAdminDashboard />
              </ProtectedRoute>
            } 
          />
          
          {/* ========== Supervisor Dashboard ========== */}
          <Route 
            path="/supervisor" 
            element={
              <ProtectedRoute allowedRoles={['superadmin', 'supervisor']}>
                <SupervisorDashboard />
              </ProtectedRoute>
            } 
          />
          
          {/* ========== Detalle de Proceso ========== */}
          <Route 
            path="/proceso/:id" 
            element={
              <ProtectedRoute allowedRoles={['superadmin', 'supervisor']}>
                <ProcesoDetalle />
              </ProtectedRoute>
            } 
          />
          
          {/* ========== Detalle de Candidato ========== */}
          <Route 
            path="/candidato/:id" 
            element={
              <ProtectedRoute allowedRoles={['superadmin', 'supervisor']}>
                <CandidateDetailWrapper />
              </ProtectedRoute>
            } 
          />
          
          {/* ========== Configuración ========== */}
          <Route 
            path="/settings" 
            element={
              <ProtectedRoute allowedRoles={['superadmin']}>
                <Settings />
              </ProtectedRoute>
            } 
          />
          
          {/* ========== 404 ========== */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </>
  )
}

export default App
