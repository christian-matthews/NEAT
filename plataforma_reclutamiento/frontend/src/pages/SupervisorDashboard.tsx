import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  Briefcase, Users, Eye, Clock, AlertTriangle, CheckCircle, 
  LogOut, Sparkles, FileText, ChevronRight
} from 'lucide-react'
import { toast } from 'sonner'
import { api, User } from '../lib/api'

// Types
interface Proceso {
  id: string
  codigo_proceso: string
  cargo_nombre?: string
  cargo_id?: string
  estado: string
  vacantes_proceso: number
  fecha_inicio?: string
  fecha_cierre?: string
  postulaciones_count: number
  avances?: string
  bloqueos?: string
  proximos_pasos?: string
}

// Estados disponibles
const ESTADOS = [
  { value: 'publicado', label: 'Publicado', color: 'bg-green-500/20 text-green-400 border-green-500/30', icon: '📢' },
  { value: 'en_revision', label: 'En Revisión', color: 'bg-blue-500/20 text-blue-400 border-blue-500/30', icon: '🔍' },
  { value: 'en_entrevistas', label: 'Entrevistas', color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30', icon: '🗣️' },
  { value: 'finalizado', label: 'Finalizado', color: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30', icon: '✅' },
  { value: 'cancelado', label: 'Cancelado', color: 'bg-red-500/20 text-red-400 border-red-500/30', icon: '❌' },
]

export default function SupervisorDashboard() {
  const navigate = useNavigate()
  const [user, setUser] = useState<User | null>(api.getStoredUser())
  const [procesos, setProcesos] = useState<Proceso[]>([])
  const [loading, setLoading] = useState(true)

  // Load data
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const procesosData = await api.getMisProcesos()
      setProcesos(procesosData)
    } catch (error) {
      toast.error('Error al cargar procesos')
    } finally {
      setLoading(false)
    }
  }

  // KPIs
  const kpis = useMemo(() => {
    const now = new Date()
    const activos = procesos.filter(p => p.estado !== 'finalizado' && p.estado !== 'cancelado')
    const conAlerta = activos.filter(p => p.fecha_cierre && new Date(p.fecha_cierre) < now)
    const totalPostulaciones = procesos.reduce((acc, p) => acc + (p.postulaciones_count || 0), 0)
    
    return {
      total: procesos.length,
      activos: activos.length,
      conAlerta: conAlerta.length,
      totalPostulaciones
    }
  }, [procesos])

  const handleLogout = async () => {
    await api.logout()
    navigate('/login')
  }

  const getEstadoBadge = (estado: string) => {
    const e = ESTADOS.find(s => s.value === estado)
    return e || ESTADOS[0]
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      {/* Background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-1/4 w-80 h-80 bg-teal-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center shadow-lg">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">Mis Procesos</h1>
              <p className="text-zinc-400 text-sm">
                Hola, {user?.nombre_completo || 'Supervisor'}
              </p>
            </div>
          </div>
          
          <button
            onClick={handleLogout}
            className="p-2 bg-zinc-800 hover:bg-red-500/20 hover:text-red-400 rounded-lg transition-colors"
            title="Cerrar sesión"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          <KPICard 
            label="Total Procesos" 
            value={kpis.total} 
            icon={<Briefcase className="w-4 h-4" />} 
          />
          <KPICard 
            label="Activos" 
            value={kpis.activos} 
            icon={<Clock className="w-4 h-4" />}
            variant="success"
          />
          <KPICard 
            label="Con Alerta" 
            value={kpis.conAlerta} 
            icon={<AlertTriangle className="w-4 h-4" />}
            variant={kpis.conAlerta > 0 ? 'danger' : 'success'}
          />
          <KPICard 
            label="CVs Totales" 
            value={kpis.totalPostulaciones} 
            icon={<FileText className="w-4 h-4" />}
          />
        </div>

        {/* Procesos Grid */}
        <div className="grid md:grid-cols-2 gap-4">
          {procesos.map(proceso => {
            const estadoBadge = getEstadoBadge(proceso.estado)
            const isAtrasado = proceso.fecha_cierre && new Date(proceso.fecha_cierre) < new Date() && proceso.estado !== 'finalizado'
            
            return (
              <div
                key={proceso.id}
                className="bg-zinc-900/50 rounded-xl border border-white/5 hover:border-emerald-500/30 transition-all p-4 cursor-pointer group"
                onClick={() => navigate(`/proceso/${proceso.id}`)}
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-sm text-zinc-400">{proceso.codigo_proceso}</span>
                      {isAtrasado && (
                        <span className="text-red-400" title="Proceso atrasado">
                          <AlertTriangle className="w-4 h-4" />
                        </span>
                      )}
                    </div>
                    <h3 className="text-lg font-semibold">{proceso.cargo_nombre || 'Sin cargo'}</h3>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs border ${estadoBadge.color}`}>
                    {estadoBadge.icon} {estadoBadge.label}
                  </span>
                </div>

                <div className="flex justify-between items-center text-sm">
                  <div className="flex items-center gap-4 text-zinc-400">
                    <span className="flex items-center gap-1">
                      <Users className="w-4 h-4" />
                      {proceso.vacantes_proceso} vacantes
                    </span>
                    {proceso.fecha_cierre && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {new Date(proceso.fecha_cierre).toLocaleDateString('es-CL', { day: '2-digit', month: 'short' })}
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className="bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded font-bold">
                      {proceso.postulaciones_count || 0} CVs
                    </span>
                    <ChevronRight className="w-5 h-5 text-zinc-500 group-hover:text-emerald-400 transition-colors" />
                  </div>
                </div>

                {(proceso.avances || proceso.bloqueos) && (
                  <div className="mt-3 pt-3 border-t border-white/5 text-xs space-y-1">
                    {proceso.avances && (
                      <p className="text-zinc-400">
                        <span className="text-green-400">Avances:</span> {proceso.avances.substring(0, 100)}...
                      </p>
                    )}
                    {proceso.bloqueos && (
                      <p className="text-zinc-400">
                        <span className="text-red-400">Bloqueos:</span> {proceso.bloqueos.substring(0, 100)}...
                      </p>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {procesos.length === 0 && (
          <div className="bg-zinc-900/50 rounded-xl border border-white/5 p-12 text-center">
            <Briefcase className="w-12 h-12 mx-auto mb-4 text-zinc-600" />
            <h3 className="text-lg font-semibold mb-2">Sin procesos asignados</h3>
            <p className="text-zinc-400">
              Contacta al SuperAdmin para que te asigne procesos de reclutamiento.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

// ============================================================================
// KPI Card Component
// ============================================================================

function KPICard({ 
  label, 
  value, 
  icon, 
  variant = 'default' 
}: { 
  label: string
  value: string | number
  icon: React.ReactNode
  variant?: 'default' | 'success' | 'warning' | 'danger'
}) {
  const variants = {
    default: 'bg-zinc-800/50 border-zinc-700/50',
    success: 'bg-emerald-500/10 border-emerald-500/30',
    warning: 'bg-yellow-500/10 border-yellow-500/30',
    danger: 'bg-red-500/10 border-red-500/30',
  }

  const textVariants = {
    default: 'text-white',
    success: 'text-emerald-400',
    warning: 'text-yellow-400',
    danger: 'text-red-400',
  }

  return (
    <div className={`p-4 rounded-xl border ${variants[variant]}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-zinc-400 font-medium">{label}</span>
        <span className="text-zinc-500">{icon}</span>
      </div>
      <div className={`text-2xl font-bold ${textVariants[variant]}`}>{value}</div>
    </div>
  )
}




