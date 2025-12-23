/**
 * Cliente API unificado para The Wingman
 * Conecta con el backend FastAPI que usa Airtable
 */

// En producción usa VITE_API_URL, en desarrollo usa /api (proxy de Vite)
const API_BASE = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api'

// ============================================================================
// Types
// ============================================================================

export interface User {
  id: string
  email: string
  nombre_completo: string
  rol: 'superadmin' | 'supervisor' | 'usuario'
  activo: boolean
}

export interface LoginResponse {
  token: string
  user: User
}

export interface Candidate {
  id: string
  codigo_tracking: string
  nombre_completo: string
  email: string
  telefono?: string
  cv_url?: string
  fecha_postulacion?: string
  proceso?: string[]
  cargo?: string[]
  created_at?: string
  score_promedio: number
  hands_on_index: number
  retention_risk: string
  profile_type?: string
  industry_tier?: string
}

export interface DashboardStats {
  total_candidatos: number
  score_promedio: number
  candidatos_alto_riesgo: number
  candidatos_evaluados: number
  candidatos_pendientes: number
  procesos_activos: number
}

export interface CategoryResult {
  score: number
  found: string[]
  reasoning: string
  questions: string[]
}

export interface CategoryResult {
  score: number
  found: string[]
  missing: string[]
  reasoning: string
  questions: string[]
}

export interface InferenceResult {
  profile_type: string
  hands_on_index: number
  risk_warning: string
  retention_risk: string
  scope_intensity: number
  potential_score: number
  industry_tier: string
}

export interface EvaluationResult {
  id: string
  candidato_id: string
  score_promedio: number
  fits: {
    admin: CategoryResult
    ops: CategoryResult
    biz: CategoryResult
  }
  inference: InferenceResult
  config_version?: string
  evaluated_at?: string
  cached?: boolean
}

export interface Comment {
  id: string
  candidato: string[]
  autor: string
  comentario: string
  created_at: string
}

export interface PublicProcess {
  id: string
  codigo_proceso: string
  cargo_nombre: string
  cargo_id: string
  vacantes: number
  fecha_cierre?: string
}

export interface ApplicationResponse {
  id: string
  codigo_tracking: string
  nombre_completo: string
  email: string
  mensaje: string
}

export interface TrackingResponse {
  codigo_tracking: string
  nombre_completo: string
  proceso: string
  cargo: string
  fecha_postulacion: string
  estado: string
}

export interface Proceso {
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
  notas?: string
  avances?: string
  bloqueos?: string
  proximos_pasos?: string
  resultado?: string
}

export interface Cargo {
  id: string
  codigo: string
  nombre: string
  descripcion?: string
  vacantes: number
  activo: boolean
}

export interface Candidato {
  id: string
  codigo_tracking: string
  nombre_completo: string
  email: string
  telefono?: string
  cv_url?: string
  cv_attachment?: any
  fecha_postulacion: string
  proceso_id?: string
  cargo_id?: string
  estado_candidato?: string
}

export interface EvaluacionAI {
  id: string
  candidato_codigo: string
  score_total: number
  score_admin?: number
  score_ops?: number
  score_biz?: number
  hands_on_index?: number
  potencial?: string
  riesgo_retencion?: string
  perfil_tipo?: string
  industry_tier?: string
  keywords_encontradas?: string[]
  resumen?: string
  fecha_evaluacion?: string
}

// ============================================================================
// API Client
// ============================================================================

class ApiClient {
  private token: string | null = null

  constructor() {
    // Recuperar token del localStorage
    this.token = localStorage.getItem('neat_token')
  }

  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers,
      ...options,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
      throw new Error(error.detail || `Error ${response.status}`)
    }

    return response.json()
  }

  private async fetchFormData<T>(endpoint: string, formData: FormData): Promise<T> {
    const headers: Record<string, string> = {}

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers,
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
      throw new Error(error.detail || `Error ${response.status}`)
    }

    return response.json()
  }

  // ==========================================================================
  // Auth
  // ==========================================================================

  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await this.fetch<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    
    this.token = response.token
    localStorage.setItem('neat_token', response.token)
    localStorage.setItem('neat_user', JSON.stringify(response.user))
    
    return response
  }

  async logout(): Promise<void> {
    try {
      await this.fetch('/auth/logout', { method: 'POST' })
    } finally {
      this.token = null
      localStorage.removeItem('neat_token')
      localStorage.removeItem('neat_user')
    }
  }

  async getMe(): Promise<User> {
    return this.fetch<User>('/auth/me')
  }

  async register(email: string, password: string, nombre_completo: string): Promise<User> {
    return this.fetch<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, nombre_completo }),
    })
  }

  isAuthenticated(): boolean {
    return !!this.token
  }

  getStoredUser(): User | null {
    const userStr = localStorage.getItem('neat_user')
    return userStr ? JSON.parse(userStr) : null
  }

  // ==========================================================================
  // Users (Admin)
  // ==========================================================================

  async getUsers(): Promise<User[]> {
    return this.fetch<User[]>('/auth/users')
  }

  async createUser(email: string, password: string, nombre_completo: string): Promise<User> {
    return this.fetch<User>('/auth/users', {
      method: 'POST',
      body: JSON.stringify({ email, password, nombre_completo }),
    })
  }

  async updateUserRole(userId: string, rol: string): Promise<void> {
    await this.fetch(`/auth/users/${userId}/role`, {
      method: 'PATCH',
      body: JSON.stringify({ rol }),
    })
  }

  async deleteUser(userId: string): Promise<void> {
    await this.fetch(`/auth/users/${userId}`, { method: 'DELETE' })
  }

  // ==========================================================================
  // Candidates
  // ==========================================================================

  async getCandidates(): Promise<Candidate[]> {
    return this.fetch<Candidate[]>('/candidates/')
  }

  async getCandidate(id: string): Promise<Candidate> {
    return this.fetch<Candidate>(`/candidates/${id}`)
  }

  async getDashboardStats(): Promise<DashboardStats> {
    return this.fetch<DashboardStats>('/candidates/stats')
  }

  // ==========================================================================
  // Evaluations
  // ==========================================================================

  async getEvaluation(candidateId: string): Promise<EvaluationResult> {
    return this.fetch<EvaluationResult>(`/evaluations/${candidateId}`)
  }

  async evaluateCandidate(candidateId: string): Promise<EvaluationResult> {
    return this.fetch<EvaluationResult>(`/evaluations/${candidateId}/evaluate`, {
      method: 'POST',
    })
  }

  // ==========================================================================
  // Comments
  // ==========================================================================

  async getComments(candidateId: string): Promise<Comment[]> {
    return this.fetch<Comment[]>(`/candidates/${candidateId}/comments`)
  }

  async addComment(candidateId: string, autor: string, comentario: string): Promise<Comment> {
    return this.fetch<Comment>(`/candidates/${candidateId}/comments`, {
      method: 'POST',
      body: JSON.stringify({ autor, comentario }),
    })
  }

  // ==========================================================================
  // Public Applications
  // ==========================================================================

  async getPublicProcesses(): Promise<PublicProcess[]> {
    return this.fetch<PublicProcess[]>('/applications/processes')
  }

  async submitApplication(
    nombre_completo: string,
    email: string,
    telefono: string,
    proceso_id: string,
    cv_file: File
  ): Promise<ApplicationResponse> {
    const formData = new FormData()
    formData.append('nombre_completo', nombre_completo)
    formData.append('email', email)
    formData.append('telefono', telefono)
    formData.append('proceso_id', proceso_id)
    formData.append('cv_file', cv_file)

    return this.fetchFormData<ApplicationResponse>('/applications/submit', formData)
  }

  async trackApplication(trackingCode: string): Promise<TrackingResponse> {
    return this.fetch<TrackingResponse>(`/applications/track/${trackingCode}`)
  }

  // ==========================================================================
  // Config
  // ==========================================================================

  async getConfig(): Promise<any> {
    return this.fetch('/config/')
  }

  // ==========================================================================
  // Procesos
  // ==========================================================================

  async getProcesos(): Promise<Proceso[]> {
    return this.fetch<Proceso[]>('/processes/')
  }

  async getProceso(id: string): Promise<Proceso> {
    return this.fetch<Proceso>(`/processes/${id}`)
  }

  async getMisProcesos(): Promise<Proceso[]> {
    return this.fetch<Proceso[]>('/processes/mine')
  }

  async createProceso(data: {
    cargo_id: string
    codigo_proceso: string
    vacantes_proceso: number
    usuario_asignado_id: string
    fecha_cierre?: string
    notas?: string
  }): Promise<Proceso> {
    return this.fetch<Proceso>('/processes/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateProceso(id: string, data: Partial<Proceso>): Promise<Proceso> {
    return this.fetch<Proceso>(`/processes/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  }

  async deleteProceso(id: string): Promise<void> {
    await this.fetch(`/processes/${id}`, { method: 'DELETE' })
  }

  async exportProcesoCSV(id: string): Promise<Blob> {
    const response = await fetch(`${API_BASE}/processes/${id}/export`, {
      headers: this.token ? { 'Authorization': `Bearer ${this.token}` } : {},
    })
    if (!response.ok) throw new Error('Error al exportar')
    return response.blob()
  }

  // ==========================================================================
  // Cargos
  // ==========================================================================

  async getCargos(): Promise<Cargo[]> {
    return this.fetch<Cargo[]>('/cargos/')
  }

  async getCargo(id: string): Promise<Cargo> {
    return this.fetch<Cargo>(`/cargos/${id}`)
  }

  async createCargo(data: {
    codigo: string
    nombre: string
    descripcion?: string
    vacantes?: number
  }): Promise<Cargo> {
    return this.fetch<Cargo>('/cargos/', {
      method: 'POST',
      body: JSON.stringify({ ...data, activo: true }),
    })
  }

  async updateCargo(id: string, data: Partial<Cargo>): Promise<Cargo> {
    return this.fetch<Cargo>(`/cargos/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  }

  async deleteCargo(id: string): Promise<void> {
    await this.fetch(`/cargos/${id}`, { method: 'DELETE' })
  }

  // ==========================================================================
  // Usuarios (Extended)
  // ==========================================================================

  async getUsuarios(): Promise<User[]> {
    return this.fetch<User[]>('/auth/users')
  }

  async createUsuario(data: {
    email: string
    password: string
    nombre_completo: string
    rol: string
  }): Promise<User> {
    return this.fetch<User>('/auth/users', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateUsuarioRole(userId: string, rol: string): Promise<void> {
    await this.fetch(`/auth/users/${userId}/role`, {
      method: 'PATCH',
      body: JSON.stringify({ rol }),
    })
  }

  async deleteUsuario(userId: string): Promise<void> {
    await this.fetch(`/auth/users/${userId}`, { method: 'DELETE' })
  }

  // ==========================================================================
  // Candidatos (por proceso)
  // ==========================================================================

  async getCandidatosByProceso(procesoId: string): Promise<Candidato[]> {
    return this.fetch<Candidato[]>(`/candidates/by-proceso/${procesoId}`)
  }

  async getCandidato(id: string): Promise<Candidato> {
    return this.fetch<Candidato>(`/candidates/${id}`)
  }

  async updateCandidato(id: string, data: Partial<Candidato>): Promise<Candidato> {
    return this.fetch<Candidato>(`/candidates/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  }

  // ==========================================================================
  // Evaluaciones AI
  // ==========================================================================

  async getEvaluacion(codigoTracking: string): Promise<EvaluacionAI | null> {
    try {
      return await this.fetch<EvaluacionAI>(`/evaluations/${codigoTracking}`)
    } catch {
      return null
    }
  }

  async evaluateCandidato(codigoTracking: string): Promise<EvaluacionAI> {
    return this.fetch<EvaluacionAI>(`/evaluations/${codigoTracking}/evaluate`, {
      method: 'POST',
    })
  }
}

// Singleton instance
export const api = new ApiClient()

// Legacy exports for compatibility
export async function getCandidates(): Promise<Candidate[]> {
  return api.getCandidates()
}

export async function getCandidate(id: string): Promise<Candidate> {
  return api.getCandidate(id)
}

export async function getDashboardStats(): Promise<DashboardStats> {
  return api.getDashboardStats()
}

export async function getEvaluation(candidateId: string): Promise<EvaluationResult> {
  return api.getEvaluation(candidateId)
}

export async function evaluateCandidate(candidateId: string): Promise<EvaluationResult> {
  return api.evaluateCandidate(candidateId)
}

export async function getComments(candidateId: string): Promise<Comment[]> {
  return api.getComments(candidateId)
}

export async function addComment(candidateId: string, autor: string, comentario: string): Promise<Comment> {
  return api.addComment(candidateId, autor, comentario)
}

export async function getConfig(): Promise<any> {
  return api.getConfig()
}
