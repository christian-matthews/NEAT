import { useState, useEffect, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  ArrowLeft, Users, FileText, Sparkles, Download, 
  Eye, RefreshCw, Clock, CheckCircle, AlertTriangle,
  Brain, TrendingUp, ChevronDown, ChevronUp, Search,
  FileSpreadsheet, Archive
} from 'lucide-react'
import { toast } from 'sonner'
import { api, Candidato, EvaluacionAI } from '../lib/api'

// Estados de candidato
const ESTADOS_CANDIDATO = [
  { value: 'nuevo', label: 'Nuevo', color: 'bg-cyan-500/20 text-cyan-400' },
  { value: 'recibido', label: 'Recibido', color: 'bg-zinc-500/20 text-zinc-400' },
  { value: 'en_revision', label: 'En Revisión', color: 'bg-blue-500/20 text-blue-400' },
  { value: 'evaluado', label: 'Evaluado IA', color: 'bg-purple-500/20 text-purple-400' },
  { value: 'entrevista', label: 'Entrevista', color: 'bg-yellow-500/20 text-yellow-400' },
  { value: 'finalista', label: 'Finalista', color: 'bg-amber-500/20 text-amber-400' },
  { value: 'seleccionado', label: 'Seleccionado', color: 'bg-green-500/20 text-green-400' },
  { value: 'rechazado', label: 'Rechazado', color: 'bg-red-500/20 text-red-400' },
  { value: 'descartado', label: 'Descartado', color: 'bg-red-800/20 text-red-500' },
]

// Estados de proceso
const ESTADOS_PROCESO = [
  { value: 'publicado', label: 'Publicado' },
  { value: 'en_revision', label: 'En Revisión' },
  { value: 'en_entrevistas', label: 'Entrevistas' },
  { value: 'finalizado', label: 'Finalizado' },
  { value: 'cancelado', label: 'Cancelado' },
]

interface Proceso {
  id: string
  codigo_proceso: string
  cargo_nombre?: string
  estado: string
  vacantes_proceso: number
  fecha_inicio?: string
  fecha_cierre?: string
  notas?: string
  avances?: string
  bloqueos?: string
  proximos_pasos?: string
}

export default function ProcesoDetalle() {
  const { id } = useParams()
  const navigate = useNavigate()
  
  const [proceso, setProceso] = useState<Proceso | null>(null)
  const [candidatos, setCandidatos] = useState<Candidato[]>([])
  const [evaluaciones, setEvaluaciones] = useState<Record<string, EvaluacionAI>>({})
  const [loading, setLoading] = useState(true)
  const [evaluating, setEvaluating] = useState<string | null>(null)
  const [evaluatingAll, setEvaluatingAll] = useState(false)
  
  // UI States
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState<'nombre' | 'score' | 'fecha'>('score')
  const [sortDesc, setSortDesc] = useState(true)
  const [showNotesModal, setShowNotesModal] = useState(false)
  const [selectedEstados, setSelectedEstados] = useState<string[]>([])
  const [showEstadoFilter, setShowEstadoFilter] = useState(false)

  useEffect(() => {
    if (id) loadData()
  }, [id])

  const loadData = async () => {
    setLoading(true)
    try {
      const [procesoData, candidatosData] = await Promise.all([
        api.getProceso(id!),
        api.getCandidatosByProceso(id!)
      ])
      setProceso(procesoData)
      setCandidatos(candidatosData)
      
      // Los scores ya vienen incluidos en los candidatos desde el backend
      // Crear mapa de evaluaciones desde los datos del candidato
      const evals: Record<string, EvaluacionAI> = {}
      candidatosData.forEach((c: Candidato) => {
        if (c.codigo_tracking && c.score_promedio !== undefined) {
          evals[c.codigo_tracking] = {
            id: c.id,
            candidato_id: c.id,
            score_total: c.score_promedio || 0,
            score_admin: 0,
            score_ops: 0,
            score_biz: 0,
            hands_on_index: c.hands_on_index || 0,
            potential_score: 0,
            retention_risk: c.retention_risk || 'Bajo',
            profile_type: c.profile_type || '',
            industry_tier: c.industry_tier || 'General',
            risk_warning: '',
            created_at: c.created_at || ''
          }
        }
      })
      setEvaluaciones(evals)
    } catch (error) {
      toast.error('Error al cargar datos')
    } finally {
      setLoading(false)
    }
  }

  // Filtrar y ordenar candidatos
  const filteredCandidatos = useMemo(() => {
    let result = candidatos.filter(c => 
      c.nombre_completo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.email.toLowerCase().includes(searchTerm.toLowerCase())
    )
    
    // Filtrar por estados seleccionados
    if (selectedEstados.length > 0) {
      result = result.filter(c => 
        selectedEstados.includes(c.estado_candidato || 'recibido')
      )
    }
    
    return result.sort((a, b) => {
      let compare = 0
      switch (sortBy) {
        case 'nombre':
          compare = a.nombre_completo.localeCompare(b.nombre_completo)
          break
        case 'score':
          const scoreA = evaluaciones[a.codigo_tracking]?.score_total || 0
          const scoreB = evaluaciones[b.codigo_tracking]?.score_total || 0
          compare = scoreA - scoreB
          break
        case 'fecha':
          compare = new Date(a.fecha_postulacion).getTime() - new Date(b.fecha_postulacion).getTime()
          break
      }
      return sortDesc ? -compare : compare
    })
  }, [candidatos, searchTerm, sortBy, sortDesc, evaluaciones, selectedEstados])

  const handleEvaluate = async (candidato: Candidato) => {
    setEvaluating(candidato.codigo_tracking)
    try {
      const result = await api.evaluateCandidato(candidato.codigo_tracking)
      setEvaluaciones(prev => ({
        ...prev,
        [candidato.codigo_tracking]: result
      }))
      toast.success(`Evaluación completada: ${result.score_total}%`)
    } catch (error) {
      toast.error('Error al evaluar candidato')
    } finally {
      setEvaluating(null)
    }
  }

  const handleEvaluateAll = async () => {
    const sinEvaluar = candidatos.filter(c => !evaluaciones[c.codigo_tracking])
    if (sinEvaluar.length === 0) {
      toast.info('Todos los candidatos ya están evaluados')
      return
    }
    
    setEvaluatingAll(true)
    let success = 0
    let failed = 0
    
    for (const candidato of sinEvaluar) {
      try {
        const result = await api.evaluateCandidato(candidato.codigo_tracking)
        setEvaluaciones(prev => ({
          ...prev,
          [candidato.codigo_tracking]: result
        }))
        success++
      } catch (error) {
        failed++
      }
    }
    
    setEvaluatingAll(false)
    toast.success(`Evaluación masiva: ${success} exitosas, ${failed} fallidas`)
  }

  const handleExportCSV = async () => {
    try {
      const blob = await api.exportProcesoCSV(id!)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${proceso?.codigo_proceso || 'proceso'}_candidatos.csv`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('CSV descargado')
    } catch (error) {
      toast.error('Error al exportar')
    }
  }

  const handleUpdateEstado = async (newEstado: string) => {
    try {
      await api.updateProceso(id!, { estado: newEstado })
      setProceso(prev => prev ? { ...prev, estado: newEstado } : null)
      toast.success('Estado actualizado')
    } catch (error) {
      toast.error('Error al actualizar estado')
    }
  }

  const handleUpdateCandidatoEstado = async (candidatoId: string, nuevoEstado: string) => {
    try {
      await api.updateCandidato(candidatoId, { estado_candidato: nuevoEstado })
      setCandidatos(prev => prev.map(c => 
        c.id === candidatoId ? { ...c, estado_candidato: nuevoEstado } : c
      ))
      toast.success('Estado actualizado')
    } catch (error) {
      toast.error('Error al actualizar')
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-400 bg-green-500/20'
    if (score >= 60) return 'text-yellow-400 bg-yellow-500/20'
    if (score >= 40) return 'text-orange-400 bg-orange-500/20'
    return 'text-red-400 bg-red-500/20'
  }

  const getEstadoBadge = (estado: string) => {
    return ESTADOS_CANDIDATO.find(e => e.value === estado) || ESTADOS_CANDIDATO[0]
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500" />
      </div>
    )
  }

  if (!proceso) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-white">
        <div className="text-center">
          <h2 className="text-xl font-bold mb-2">Proceso no encontrado</h2>
          <button onClick={() => navigate(-1)} className="text-purple-400 hover:underline">
            Volver
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      {/* Background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/3 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/3 w-80 h-80 bg-pink-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={() => navigate(-1)}
            className="p-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm text-zinc-400">{proceso.codigo_proceso}</span>
              <select
                value={proceso.estado}
                onChange={e => handleUpdateEstado(e.target.value)}
                className="px-2 py-1 bg-zinc-800 rounded-lg text-sm border border-zinc-700"
              >
                {ESTADOS_PROCESO.map(e => (
                  <option key={e.value} value={e.value}>{e.label}</option>
                ))}
              </select>
            </div>
            <h1 className="text-2xl font-bold">{proceso.cargo_nombre || 'Sin cargo'}</h1>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleExportCSV}
              className="px-3 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg flex items-center gap-2 text-sm"
            >
              <FileSpreadsheet className="w-4 h-4" />
              CSV
            </button>
            <button
              onClick={handleEvaluateAll}
              disabled={evaluatingAll}
              className="px-4 py-2 bg-purple-500 hover:bg-purple-600 rounded-lg flex items-center gap-2 text-sm font-medium disabled:opacity-50"
            >
              {evaluatingAll ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Evaluando...
                </>
              ) : (
                <>
                  <Brain className="w-4 h-4" />
                  Evaluar Todos
                </>
              )}
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <div className="bg-zinc-900/50 rounded-xl border border-white/5 p-4">
            <div className="text-xs text-zinc-400 mb-1">Total CVs</div>
            <div className="text-2xl font-bold">{candidatos.length}</div>
          </div>
          <div className="bg-zinc-900/50 rounded-xl border border-white/5 p-4">
            <div className="text-xs text-zinc-400 mb-1">Evaluados</div>
            <div className="text-2xl font-bold text-purple-400">
              {Object.keys(evaluaciones).length}
            </div>
          </div>
          <div className="bg-zinc-900/50 rounded-xl border border-white/5 p-4">
            <div className="text-xs text-zinc-400 mb-1">Vacantes</div>
            <div className="text-2xl font-bold">{proceso.vacantes_proceso}</div>
          </div>
          <div className="bg-zinc-900/50 rounded-xl border border-white/5 p-4">
            <div className="text-xs text-zinc-400 mb-1">Score Promedio</div>
            <div className="text-2xl font-bold text-green-400">
              {Object.values(evaluaciones).length > 0
                ? Math.round(
                    Object.values(evaluaciones).reduce((acc, e) => acc + (e.score_total || 0), 0) /
                    Object.values(evaluaciones).length
                  )
                : 0}%
            </div>
          </div>
        </div>

        {/* Search & Sort */}
        <div className="bg-zinc-900/50 rounded-xl border border-white/5 p-4 mb-6">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-60 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
              <input
                type="text"
                placeholder="Buscar candidato..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-zinc-800 rounded-lg border border-zinc-700 focus:border-purple-500 outline-none"
              />
            </div>
            
            {/* Filtro por Estado */}
            <div className="relative">
              <button
                onClick={() => setShowEstadoFilter(!showEstadoFilter)}
                className={`px-4 py-2 rounded-lg border flex items-center gap-2 transition-colors ${
                  selectedEstados.length > 0 
                    ? 'bg-purple-500/20 border-purple-500/50 text-purple-300' 
                    : 'bg-zinc-800 border-zinc-700 text-zinc-300 hover:border-zinc-600'
                }`}
              >
                <span>Estado</span>
                {selectedEstados.length > 0 && (
                  <span className="px-1.5 py-0.5 text-xs bg-purple-500 text-white rounded-full">
                    {selectedEstados.length}
                  </span>
                )}
                <ChevronDown className="w-4 h-4" />
              </button>
              
              {showEstadoFilter && (
                <div className="absolute top-full mt-2 right-0 bg-zinc-800 border border-zinc-700 rounded-lg shadow-xl z-50 min-w-48">
                  <div className="p-2 border-b border-zinc-700 flex justify-between items-center">
                    <span className="text-xs text-zinc-400">Filtrar por estado</span>
                    {selectedEstados.length > 0 && (
                      <button 
                        onClick={() => setSelectedEstados([])}
                        className="text-xs text-red-400 hover:text-red-300"
                      >
                        Limpiar
                      </button>
                    )}
                  </div>
                  {ESTADOS_CANDIDATO.map(estado => (
                    <label
                      key={estado.value}
                      className="flex items-center gap-3 px-3 py-2 hover:bg-zinc-700/50 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selectedEstados.includes(estado.value)}
                        onChange={e => {
                          if (e.target.checked) {
                            setSelectedEstados([...selectedEstados, estado.value])
                          } else {
                            setSelectedEstados(selectedEstados.filter(s => s !== estado.value))
                          }
                        }}
                        className="rounded border-zinc-600 bg-zinc-700 text-purple-500 focus:ring-purple-500"
                      />
                      <span className={`px-2 py-0.5 rounded text-xs ${estado.color}`}>
                        {estado.label}
                      </span>
                    </label>
                  ))}
                </div>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              <span className="text-sm text-zinc-400">Ordenar:</span>
              {['score', 'nombre', 'fecha'].map(option => (
                <button
                  key={option}
                  onClick={() => {
                    if (sortBy === option) {
                      setSortDesc(!sortDesc)
                    } else {
                      setSortBy(option as any)
                      setSortDesc(true)
                    }
                  }}
                  className={`px-3 py-1.5 rounded-lg text-sm flex items-center gap-1 transition-colors ${
                    sortBy === option 
                      ? 'bg-purple-500/20 text-purple-400' 
                      : 'bg-zinc-800 hover:bg-zinc-700'
                  }`}
                >
                  {option === 'score' ? 'Score' : option === 'nombre' ? 'Nombre' : 'Fecha'}
                  {sortBy === option && (sortDesc ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />)}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Candidates Table */}
        <div className="bg-zinc-900/50 rounded-xl border border-white/5 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5 text-left text-sm text-zinc-400">
                <th className="px-4 py-3 font-medium">Candidato</th>
                <th className="px-4 py-3 font-medium">Estado</th>
                <th className="px-4 py-3 font-medium text-center">Score IA</th>
                <th className="px-4 py-3 font-medium text-center">Hands-On</th>
                <th className="px-4 py-3 font-medium text-center">Perfil</th>
                <th className="px-4 py-3 font-medium text-center">Retención</th>
                <th className="px-4 py-3 font-medium">Fecha</th>
                <th className="px-4 py-3 font-medium text-center">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filteredCandidatos.map(candidato => {
                const evaluacion = evaluaciones[candidato.codigo_tracking]
                const estadoBadge = getEstadoBadge(candidato.estado_candidato || 'recibido')
                
                return (
                  <tr key={candidato.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="px-4 py-3">
                      <div>
                        <div className="font-medium">{candidato.nombre_completo}</div>
                        <div className="text-sm text-zinc-400">{candidato.email}</div>
                        <div className="text-xs font-mono text-zinc-500">{candidato.codigo_tracking}</div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <select
                        value={candidato.estado_candidato || 'recibido'}
                        onChange={e => handleUpdateCandidatoEstado(candidato.id, e.target.value)}
                        className={`px-2 py-1 rounded text-xs border-none ${estadoBadge.color}`}
                      >
                        {ESTADOS_CANDIDATO.map(e => (
                          <option key={e.value} value={e.value}>{e.label}</option>
                        ))}
                      </select>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {evaluacion ? (
                        <span className={`px-3 py-1 rounded-full font-bold ${getScoreColor(evaluacion.score_total)}`}>
                          {evaluacion.score_total}%
                        </span>
                      ) : (
                        <span className="text-zinc-500">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {evaluacion?.hands_on_index !== undefined ? (
                        <span className="text-sm">{evaluacion.hands_on_index}%</span>
                      ) : (
                        <span className="text-zinc-500">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {evaluacion?.profile_type ? (
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          evaluacion.profile_type.includes('Hands-On') ? 'bg-green-500/20 text-green-400' :
                          evaluacion.profile_type.includes('Híbrido') ? 'bg-blue-500/20 text-blue-400' :
                          'bg-yellow-500/20 text-yellow-400'
                        }`}>
                          {evaluacion.profile_type.split('/')[0].trim()}
                        </span>
                      ) : (
                        <span className="text-zinc-500">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {evaluacion?.retention_risk ? (
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          evaluacion.retention_risk === 'Bajo' ? 'bg-green-500/20 text-green-400' :
                          evaluacion.retention_risk === 'Medio' ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-red-500/20 text-red-400'
                        }`}>
                          {evaluacion.retention_risk}
                        </span>
                      ) : (
                        <span className="text-zinc-500">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-zinc-400">
                      {new Date(candidato.fecha_postulacion).toLocaleDateString('es-CL', {
                        day: '2-digit',
                        month: 'short'
                      })}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-center gap-1">
                        {candidato.cv_url && (
                          <a
                            href={candidato.cv_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-2 hover:bg-zinc-700 rounded-lg transition-colors"
                            title="Ver CV"
                          >
                            <FileText className="w-4 h-4" />
                          </a>
                        )}
                        <button
                          onClick={() => navigate(`/candidato/${candidato.id}`)}
                          className="p-2 hover:bg-purple-500/20 hover:text-purple-400 rounded-lg transition-colors"
                          title="Ver detalle"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        {!evaluacion && (
                          <button
                            onClick={() => handleEvaluate(candidato)}
                            disabled={evaluating === candidato.codigo_tracking}
                            className="p-2 hover:bg-purple-500/20 hover:text-purple-400 rounded-lg transition-colors disabled:opacity-50"
                            title="Evaluar con IA"
                          >
                            {evaluating === candidato.codigo_tracking ? (
                              <RefreshCw className="w-4 h-4 animate-spin" />
                            ) : (
                              <Brain className="w-4 h-4" />
                            )}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
              {filteredCandidatos.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center text-zinc-500">
                    {candidatos.length === 0 
                      ? 'No hay candidatos en este proceso'
                      : 'No se encontraron candidatos con ese filtro'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Notas del proceso */}
        {(proceso.avances || proceso.bloqueos || proceso.proximos_pasos || proceso.notas) && (
          <div className="mt-6 bg-zinc-900/50 rounded-xl border border-white/5 p-4">
            <h3 className="text-sm font-semibold text-zinc-400 mb-3">Notas del Proceso</h3>
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              {proceso.avances && (
                <div className="p-3 bg-green-500/10 rounded-lg border border-green-500/20">
                  <div className="text-green-400 font-medium mb-1 flex items-center gap-2">
                    <CheckCircle className="w-4 h-4" />
                    Avances
                  </div>
                  <p className="text-zinc-300">{proceso.avances}</p>
                </div>
              )}
              {proceso.bloqueos && (
                <div className="p-3 bg-red-500/10 rounded-lg border border-red-500/20">
                  <div className="text-red-400 font-medium mb-1 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" />
                    Bloqueos
                  </div>
                  <p className="text-zinc-300">{proceso.bloqueos}</p>
                </div>
              )}
              {proceso.proximos_pasos && (
                <div className="p-3 bg-blue-500/10 rounded-lg border border-blue-500/20">
                  <div className="text-blue-400 font-medium mb-1 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" />
                    Próximos Pasos
                  </div>
                  <p className="text-zinc-300">{proceso.proximos_pasos}</p>
                </div>
              )}
              {proceso.notas && (
                <div className="p-3 bg-zinc-800/50 rounded-lg border border-white/5">
                  <div className="text-zinc-400 font-medium mb-1">Notas Generales</div>
                  <p className="text-zinc-300">{proceso.notas}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

