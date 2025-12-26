import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  Briefcase, Users, Plus, Eye, Settings2, Trash2, 
  Filter, X, Clock, AlertTriangle, CheckCircle, LogOut,
  FileSpreadsheet, Edit, Power, Sparkles
} from 'lucide-react'
import { toast } from 'sonner'
import { api, User } from '../lib/api'

// Types
interface Proceso {
  id: string
  codigo_proceso: string
  cargo_nombre?: string
  cargo_id?: string
  usuario_asignado_nombre?: string
  usuario_asignado_id?: string
  estado: string
  vacantes_proceso: number
  fecha_inicio?: string
  fecha_cierre?: string
  postulaciones_count: number
}

interface Cargo {
  id: string
  codigo: string
  nombre: string
  descripcion?: string
  vacantes: number
  activo: boolean
}

// Estados disponibles
const ESTADOS = [
  { value: 'publicado', label: 'Publicado', color: 'bg-green-500/20 text-green-400 border-green-500/30' },
  { value: 'en_revision', label: 'En Revisión', color: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
  { value: 'en_entrevistas', label: 'Entrevistas', color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' },
  { value: 'finalizado', label: 'Finalizado', color: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30' },
  { value: 'cancelado', label: 'Cancelado', color: 'bg-red-500/20 text-red-400 border-red-500/30' },
]

export default function SuperAdminDashboard() {
  const navigate = useNavigate()
  const [user, setUser] = useState<User | null>(api.getStoredUser())
  const [procesos, setProcesos] = useState<Proceso[]>([])
  const [usuarios, setUsuarios] = useState<User[]>([])
  const [cargos, setCargos] = useState<Cargo[]>([])
  const [loading, setLoading] = useState(true)
  
  // Filters
  const [selectedEstados, setSelectedEstados] = useState<string[]>([])
  const [selectedSupervisors, setSelectedSupervisors] = useState<string[]>([])
  
  // Modals
  const [showUserModal, setShowUserModal] = useState(false)
  const [showCargoModal, setShowCargoModal] = useState(false)
  const [showProcesoModal, setShowProcesoModal] = useState(false)

  // Load data
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [procesosData, usuariosData, cargosData] = await Promise.all([
        api.getProcesos(),
        api.getUsuarios(),
        api.getCargos()
      ])
      setProcesos(procesosData)
      setUsuarios(usuariosData)
      setCargos(cargosData)
    } catch (error) {
      toast.error('Error al cargar datos')
    } finally {
      setLoading(false)
    }
  }

  // Filter procesos
  const filteredProcesos = useMemo(() => {
    let result = procesos
    if (selectedEstados.length > 0) {
      result = result.filter(p => selectedEstados.includes(p.estado))
    }
    if (selectedSupervisors.length > 0) {
      result = result.filter(p => selectedSupervisors.includes(p.usuario_asignado_id || ''))
    }
    return result
  }, [procesos, selectedEstados, selectedSupervisors])

  // KPIs
  const kpis = useMemo(() => {
    const now = new Date()
    const activos = procesos.filter(p => p.estado !== 'finalizado' && p.estado !== 'cancelado')
    const onTime = activos.filter(p => !p.fecha_cierre || new Date(p.fecha_cierre) >= now)
    const atrasados = activos.filter(p => p.fecha_cierre && new Date(p.fecha_cierre) < now)
    const totalPostulaciones = procesos.reduce((acc, p) => acc + (p.postulaciones_count || 0), 0)
    
    return {
      activos: activos.length,
      onTime: onTime.length,
      atrasados: atrasados.length,
      porcentajeAtrasos: activos.length > 0 ? Math.round((atrasados.length / activos.length) * 100) : 0,
      totalPostulaciones,
      usuarios: usuarios.filter(u => u.rol !== 'usuario').length
    }
  }, [procesos, usuarios])

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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      {/* Background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-80 h-80 bg-purple-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-500 flex items-center justify-center shadow-lg">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">Panel SuperAdmin</h1>
              <p className="text-zinc-400 text-sm">Control total del sistema</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowUserModal(true)}
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg flex items-center gap-2 text-sm transition-colors"
            >
              <Users className="w-4 h-4" />
              Usuarios
            </button>
            <button
              onClick={() => setShowCargoModal(true)}
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg flex items-center gap-2 text-sm transition-colors"
            >
              <Briefcase className="w-4 h-4" />
              Cargos
            </button>
            <button
              onClick={handleLogout}
              className="p-2 bg-zinc-800 hover:bg-red-500/20 hover:text-red-400 rounded-lg transition-colors"
              title="Cerrar sesión"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4 mb-8">
          <KPICard 
            label="Activos" 
            value={kpis.activos} 
            icon={<Briefcase className="w-4 h-4" />} 
          />
          <KPICard 
            label="On Time" 
            value={kpis.onTime} 
            icon={<CheckCircle className="w-4 h-4" />}
            variant="success"
          />
          <KPICard 
            label="Atrasados" 
            value={kpis.atrasados} 
            icon={<AlertTriangle className="w-4 h-4" />}
            variant={kpis.atrasados > 0 ? 'danger' : 'success'}
          />
          <KPICard 
            label="% Atrasos" 
            value={`${kpis.porcentajeAtrasos}%`} 
            icon={<Clock className="w-4 h-4" />}
            variant={kpis.porcentajeAtrasos > 20 ? 'warning' : 'success'}
          />
          <KPICard 
            label="Postulaciones" 
            value={kpis.totalPostulaciones} 
            icon={<Users className="w-4 h-4" />}
          />
          <KPICard 
            label="Staff" 
            value={kpis.usuarios} 
            icon={<Users className="w-4 h-4" />}
          />
        </div>

        {/* Procesos Table */}
        <div className="bg-zinc-900/50 rounded-xl border border-white/5 overflow-hidden">
          <div className="p-4 border-b border-white/5 flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold">Procesos de Reclutamiento</h2>
              <p className="text-zinc-400 text-sm">
                {filteredProcesos.length} de {procesos.length} procesos
              </p>
            </div>
            <div className="flex items-center gap-2">
              {/* Estado Filter */}
              <div className="relative group">
                <button className="px-3 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg flex items-center gap-2 text-sm">
                  <Filter className="w-4 h-4" />
                  Estado
                  {selectedEstados.length > 0 && (
                    <span className="bg-cyan-500 text-white text-xs px-1.5 rounded-full">
                      {selectedEstados.length}
                    </span>
                  )}
                </button>
                <div className="absolute right-0 mt-2 w-48 bg-zinc-800 rounded-lg shadow-xl border border-white/10 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 p-2">
                  {ESTADOS.map(estado => (
                    <label key={estado.value} className="flex items-center gap-2 px-2 py-1.5 hover:bg-white/5 rounded cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedEstados.includes(estado.value)}
                        onChange={() => {
                          setSelectedEstados(prev =>
                            prev.includes(estado.value)
                              ? prev.filter(e => e !== estado.value)
                              : [...prev, estado.value]
                          )
                        }}
                        className="rounded border-zinc-600"
                      />
                      <span className="text-sm">{estado.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {(selectedEstados.length > 0 || selectedSupervisors.length > 0) && (
                <button
                  onClick={() => {
                    setSelectedEstados([])
                    setSelectedSupervisors([])
                  }}
                  className="p-2 hover:bg-zinc-700 rounded-lg"
                  title="Limpiar filtros"
                >
                  <X className="w-4 h-4" />
                </button>
              )}

              <button
                onClick={() => setShowProcesoModal(true)}
                className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 rounded-lg flex items-center gap-2 text-sm font-medium transition-colors"
              >
                <Plus className="w-4 h-4" />
                Nuevo Proceso
              </button>
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/5 text-left text-sm text-zinc-400">
                  <th className="px-4 py-3 font-medium">Código</th>
                  <th className="px-4 py-3 font-medium">Cargo</th>
                  <th className="px-4 py-3 font-medium">Asignado</th>
                  <th className="px-4 py-3 font-medium">Estado</th>
                  <th className="px-4 py-3 font-medium text-center">Vac.</th>
                  <th className="px-4 py-3 font-medium">F. Cierre</th>
                  <th className="px-4 py-3 font-medium text-center">CVs</th>
                  <th className="px-4 py-3 font-medium text-center">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filteredProcesos.map(proceso => {
                  const estadoBadge = getEstadoBadge(proceso.estado)
                  const isAtrasado = proceso.fecha_cierre && new Date(proceso.fecha_cierre) < new Date() && proceso.estado !== 'finalizado'
                  
                  return (
                    <tr key={proceso.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                      <td className="px-4 py-3 font-mono text-sm">{proceso.codigo_proceso}</td>
                      <td className="px-4 py-3">{proceso.cargo_nombre || '-'}</td>
                      <td className="px-4 py-3 text-sm text-zinc-400">{proceso.usuario_asignado_nombre || 'Sin asignar'}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs border ${estadoBadge.color}`}>
                          {estadoBadge.label}
                        </span>
                        {isAtrasado && (
                          <span className="ml-2 text-red-400" title="Proceso atrasado">
                            <AlertTriangle className="w-4 h-4 inline" />
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">{proceso.vacantes_proceso}</td>
                      <td className="px-4 py-3 text-sm text-zinc-400">
                        {proceso.fecha_cierre 
                          ? new Date(proceso.fecha_cierre).toLocaleDateString('es-CL', { day: '2-digit', month: 'short' })
                          : '-'}
                      </td>
                      <td className="px-4 py-3 text-center font-bold text-cyan-400">{proceso.postulaciones_count || 0}</td>
                      <td className="px-4 py-3">
                        <div className="flex justify-center gap-1">
                          <button
                            onClick={() => navigate(`/proceso/${proceso.id}`)}
                            className="p-2 hover:bg-cyan-500/20 hover:text-cyan-400 rounded-lg transition-colors"
                            title="Ver detalle"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            className="p-2 hover:bg-zinc-700 rounded-lg transition-colors"
                            title="Configurar"
                          >
                            <Settings2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
                {filteredProcesos.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-4 py-12 text-center text-zinc-500">
                      No hay procesos que mostrar
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Modal: Usuarios */}
      {showUserModal && (
        <UserManagementModal
          usuarios={usuarios}
          onClose={() => setShowUserModal(false)}
          onRefresh={loadData}
        />
      )}

      {/* Modal: Cargos */}
      {showCargoModal && (
        <CargoManagementModal
          cargos={cargos}
          onClose={() => setShowCargoModal(false)}
          onRefresh={loadData}
        />
      )}

      {/* Modal: Nuevo Proceso */}
      {showProcesoModal && (
        <ProcesoModal
          cargos={cargos}
          usuarios={usuarios}
          onClose={() => setShowProcesoModal(false)}
          onRefresh={loadData}
        />
      )}
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
    success: 'bg-green-500/10 border-green-500/30',
    warning: 'bg-yellow-500/10 border-yellow-500/30',
    danger: 'bg-red-500/10 border-red-500/30',
  }

  const textVariants = {
    default: 'text-white',
    success: 'text-green-400',
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

// ============================================================================
// User Management Modal
// ============================================================================

function UserManagementModal({ 
  usuarios, 
  onClose, 
  onRefresh 
}: { 
  usuarios: User[]
  onClose: () => void
  onRefresh: () => void
}) {
  const [showCreate, setShowCreate] = useState(false)
  const [newUser, setNewUser] = useState({ email: '', password: '', nombre_completo: '', rol: 'supervisor' })
  const [creating, setCreating] = useState(false)

  const handleCreate = async () => {
    if (!newUser.email || !newUser.password || !newUser.nombre_completo) {
      toast.error('Completa todos los campos')
      return
    }
    
    setCreating(true)
    try {
      await api.createUsuario(newUser)
      toast.success('Usuario creado')
      setShowCreate(false)
      setNewUser({ email: '', password: '', nombre_completo: '', rol: 'supervisor' })
      onRefresh()
    } catch (error) {
      toast.error('Error al crear usuario')
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (userId: string, email: string) => {
    if (!confirm(`¿Eliminar usuario ${email}?`)) return
    try {
      await api.deleteUsuario(userId)
      toast.success('Usuario eliminado')
      onRefresh()
    } catch (error) {
      toast.error('Error al eliminar')
    }
  }

  const handleRoleChange = async (userId: string, newRole: string) => {
    try {
      await api.updateUsuarioRole(userId, newRole)
      toast.success('Rol actualizado')
      onRefresh()
    } catch (error) {
      toast.error('Error al actualizar rol')
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-zinc-900 rounded-xl border border-white/10 w-full max-w-3xl max-h-[80vh] overflow-hidden">
        <div className="p-4 border-b border-white/5 flex justify-between items-center">
          <h2 className="text-lg font-semibold">Gestión de Usuarios</h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowCreate(!showCreate)}
              className="px-3 py-1.5 bg-cyan-500 hover:bg-cyan-600 rounded-lg text-sm font-medium"
            >
              <Plus className="w-4 h-4 inline mr-1" />
              Nuevo
            </button>
            <button onClick={onClose} className="p-2 hover:bg-zinc-700 rounded-lg">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {showCreate && (
          <div className="p-4 border-b border-white/5 bg-zinc-800/50">
            <div className="grid grid-cols-4 gap-3">
              <input
                type="email"
                placeholder="Email"
                value={newUser.email}
                onChange={e => setNewUser({ ...newUser, email: e.target.value })}
                className="px-3 py-2 bg-zinc-700 rounded-lg text-sm border border-zinc-600 focus:border-cyan-500 outline-none"
              />
              <input
                type="password"
                placeholder="Contraseña"
                value={newUser.password}
                onChange={e => setNewUser({ ...newUser, password: e.target.value })}
                className="px-3 py-2 bg-zinc-700 rounded-lg text-sm border border-zinc-600 focus:border-cyan-500 outline-none"
              />
              <input
                type="text"
                placeholder="Nombre completo"
                value={newUser.nombre_completo}
                onChange={e => setNewUser({ ...newUser, nombre_completo: e.target.value })}
                className="px-3 py-2 bg-zinc-700 rounded-lg text-sm border border-zinc-600 focus:border-cyan-500 outline-none"
              />
              <div className="flex gap-2">
                <select
                  value={newUser.rol}
                  onChange={e => setNewUser({ ...newUser, rol: e.target.value })}
                  className="flex-1 px-3 py-2 bg-zinc-700 rounded-lg text-sm border border-zinc-600"
                >
                  <option value="supervisor">Supervisor</option>
                  <option value="superadmin">SuperAdmin</option>
                </select>
                <button
                  onClick={handleCreate}
                  disabled={creating}
                  className="px-4 py-2 bg-green-500 hover:bg-green-600 rounded-lg text-sm font-medium disabled:opacity-50"
                >
                  {creating ? '...' : 'Crear'}
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="overflow-auto max-h-96">
          <table className="w-full">
            <thead className="bg-zinc-800/50 sticky top-0">
              <tr className="text-left text-sm text-zinc-400">
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Nombre</th>
                <th className="px-4 py-3">Rol</th>
                <th className="px-4 py-3 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {usuarios.map(u => (
                <tr key={u.id} className="border-b border-white/5 hover:bg-white/5">
                  <td className="px-4 py-3 text-sm">{u.email}</td>
                  <td className="px-4 py-3">{u.nombre_completo}</td>
                  <td className="px-4 py-3">
                    <select
                      value={u.rol}
                      onChange={e => handleRoleChange(u.id, e.target.value)}
                      className="px-2 py-1 bg-zinc-700 rounded text-sm border border-zinc-600"
                    >
                      <option value="usuario">Usuario</option>
                      <option value="supervisor">Supervisor</option>
                      <option value="superadmin">SuperAdmin</option>
                    </select>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <button
                      onClick={() => handleDelete(u.id, u.email)}
                      className="p-2 hover:bg-red-500/20 hover:text-red-400 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// Cargo Management Modal
// ============================================================================

function CargoManagementModal({ 
  cargos, 
  onClose, 
  onRefresh 
}: { 
  cargos: Cargo[]
  onClose: () => void
  onRefresh: () => void
}) {
  const [showCreate, setShowCreate] = useState(false)
  const [newCargo, setNewCargo] = useState({ codigo: '', nombre: '', descripcion: '', vacantes: 1 })
  const [creating, setCreating] = useState(false)

  const handleCreate = async () => {
    if (!newCargo.codigo || !newCargo.nombre) {
      toast.error('Código y nombre son requeridos')
      return
    }
    
    setCreating(true)
    try {
      await api.createCargo(newCargo)
      toast.success('Cargo creado')
      setShowCreate(false)
      setNewCargo({ codigo: '', nombre: '', descripcion: '', vacantes: 1 })
      onRefresh()
    } catch (error) {
      toast.error('Error al crear cargo')
    } finally {
      setCreating(false)
    }
  }

  const handleToggle = async (cargoId: string, activo: boolean) => {
    try {
      await api.updateCargo(cargoId, { activo: !activo })
      toast.success(activo ? 'Cargo desactivado' : 'Cargo activado')
      onRefresh()
    } catch (error) {
      toast.error('Error al actualizar')
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-zinc-900 rounded-xl border border-white/10 w-full max-w-2xl max-h-[80vh] overflow-hidden">
        <div className="p-4 border-b border-white/5 flex justify-between items-center">
          <h2 className="text-lg font-semibold">Gestión de Cargos</h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowCreate(!showCreate)}
              className="px-3 py-1.5 bg-cyan-500 hover:bg-cyan-600 rounded-lg text-sm font-medium"
            >
              <Plus className="w-4 h-4 inline mr-1" />
              Nuevo
            </button>
            <button onClick={onClose} className="p-2 hover:bg-zinc-700 rounded-lg">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {showCreate && (
          <div className="p-4 border-b border-white/5 bg-zinc-800/50">
            <div className="grid grid-cols-2 gap-3 mb-3">
              <input
                type="text"
                placeholder="Código (ej: DEV-001)"
                value={newCargo.codigo}
                onChange={e => setNewCargo({ ...newCargo, codigo: e.target.value.toUpperCase() })}
                className="px-3 py-2 bg-zinc-700 rounded-lg text-sm border border-zinc-600 focus:border-cyan-500 outline-none"
              />
              <input
                type="text"
                placeholder="Nombre del cargo"
                value={newCargo.nombre}
                onChange={e => setNewCargo({ ...newCargo, nombre: e.target.value })}
                className="px-3 py-2 bg-zinc-700 rounded-lg text-sm border border-zinc-600 focus:border-cyan-500 outline-none"
              />
            </div>
            <div className="flex gap-3">
              <input
                type="text"
                placeholder="Descripción (opcional)"
                value={newCargo.descripcion}
                onChange={e => setNewCargo({ ...newCargo, descripcion: e.target.value })}
                className="flex-1 px-3 py-2 bg-zinc-700 rounded-lg text-sm border border-zinc-600 focus:border-cyan-500 outline-none"
              />
              <input
                type="number"
                min="1"
                placeholder="Vacantes"
                value={newCargo.vacantes}
                onChange={e => setNewCargo({ ...newCargo, vacantes: parseInt(e.target.value) || 1 })}
                className="w-24 px-3 py-2 bg-zinc-700 rounded-lg text-sm border border-zinc-600 focus:border-cyan-500 outline-none"
              />
              <button
                onClick={handleCreate}
                disabled={creating}
                className="px-4 py-2 bg-green-500 hover:bg-green-600 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                {creating ? '...' : 'Crear'}
              </button>
            </div>
          </div>
        )}

        <div className="overflow-auto max-h-96">
          <table className="w-full">
            <thead className="bg-zinc-800/50 sticky top-0">
              <tr className="text-left text-sm text-zinc-400">
                <th className="px-4 py-3 w-12">Activo</th>
                <th className="px-4 py-3">Código</th>
                <th className="px-4 py-3">Nombre</th>
                <th className="px-4 py-3">Vacantes</th>
              </tr>
            </thead>
            <tbody>
              {cargos.map(cargo => (
                <tr key={cargo.id} className="border-b border-white/5 hover:bg-white/5">
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleToggle(cargo.id, cargo.activo)}
                      className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
                        cargo.activo 
                          ? 'bg-green-500/20 text-green-400' 
                          : 'bg-zinc-700 text-zinc-500'
                      }`}
                    >
                      <Power className="w-4 h-4" />
                    </button>
                  </td>
                  <td className="px-4 py-3 font-mono text-sm">{cargo.codigo}</td>
                  <td className="px-4 py-3">{cargo.nombre}</td>
                  <td className="px-4 py-3">{cargo.vacantes}</td>
                </tr>
              ))}
              {cargos.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-zinc-500">
                    No hay cargos registrados
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// Proceso Modal
// ============================================================================

function ProcesoModal({ 
  cargos, 
  usuarios, 
  onClose, 
  onRefresh 
}: { 
  cargos: Cargo[]
  usuarios: User[]
  onClose: () => void
  onRefresh: () => void
}) {
  const [form, setForm] = useState({
    cargo_id: '',
    codigo_proceso: '',
    vacantes_proceso: 1,
    usuario_asignado_id: '',
    fecha_cierre: '',
    notas: ''
  })
  const [creating, setCreating] = useState(false)

  const supervisores = usuarios.filter(u => u.rol === 'supervisor' || u.rol === 'superadmin')

  const handleCreate = async () => {
    if (!form.cargo_id || !form.codigo_proceso || !form.usuario_asignado_id) {
      toast.error('Completa los campos requeridos')
      return
    }
    
    setCreating(true)
    try {
      await api.createProceso(form)
      toast.success('Proceso creado')
      onClose()
      onRefresh()
    } catch (error) {
      toast.error('Error al crear proceso')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-zinc-900 rounded-xl border border-white/10 w-full max-w-lg">
        <div className="p-4 border-b border-white/5 flex justify-between items-center">
          <h2 className="text-lg font-semibold">Crear Nuevo Proceso</h2>
          <button onClick={onClose} className="p-2 hover:bg-zinc-700 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 space-y-4">
          <div>
            <label className="block text-sm text-zinc-400 mb-1">Cargo *</label>
            <select
              value={form.cargo_id}
              onChange={e => setForm({ ...form, cargo_id: e.target.value })}
              className="w-full px-3 py-2 bg-zinc-800 rounded-lg border border-zinc-700 focus:border-cyan-500 outline-none"
            >
              <option value="">Selecciona un cargo</option>
              {cargos.filter(c => c.activo).map(cargo => (
                <option key={cargo.id} value={cargo.id}>
                  {cargo.nombre} ({cargo.codigo})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-zinc-400 mb-1">Código del Proceso *</label>
            <input
              type="text"
              placeholder="ej: DEV-001-P001"
              value={form.codigo_proceso}
              onChange={e => setForm({ ...form, codigo_proceso: e.target.value.toUpperCase() })}
              className="w-full px-3 py-2 bg-zinc-800 rounded-lg border border-zinc-700 focus:border-cyan-500 outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-zinc-400 mb-1">Vacantes *</label>
              <input
                type="number"
                min="1"
                value={form.vacantes_proceso}
                onChange={e => setForm({ ...form, vacantes_proceso: parseInt(e.target.value) || 1 })}
                className="w-full px-3 py-2 bg-zinc-800 rounded-lg border border-zinc-700 focus:border-cyan-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm text-zinc-400 mb-1">Fecha Cierre</label>
              <input
                type="date"
                value={form.fecha_cierre}
                onChange={e => setForm({ ...form, fecha_cierre: e.target.value })}
                className="w-full px-3 py-2 bg-zinc-800 rounded-lg border border-zinc-700 focus:border-cyan-500 outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-zinc-400 mb-1">Supervisor Asignado *</label>
            <select
              value={form.usuario_asignado_id}
              onChange={e => setForm({ ...form, usuario_asignado_id: e.target.value })}
              className="w-full px-3 py-2 bg-zinc-800 rounded-lg border border-zinc-700 focus:border-cyan-500 outline-none"
            >
              <option value="">Selecciona un supervisor</option>
              {supervisores.map(u => (
                <option key={u.id} value={u.id}>
                  {u.nombre_completo} ({u.rol})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-zinc-400 mb-1">Notas (opcional)</label>
            <textarea
              placeholder="Notas adicionales..."
              value={form.notas}
              onChange={e => setForm({ ...form, notas: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 bg-zinc-800 rounded-lg border border-zinc-700 focus:border-cyan-500 outline-none resize-none"
            />
          </div>
        </div>

        <div className="p-4 border-t border-white/5 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg text-sm"
          >
            Cancelar
          </button>
          <button
            onClick={handleCreate}
            disabled={creating}
            className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 rounded-lg text-sm font-medium disabled:opacity-50"
          >
            {creating ? 'Creando...' : 'Crear Proceso'}
          </button>
        </div>
      </div>
    </div>
  )
}



