import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { 
  ArrowLeft, 
  Mail, 
  Phone, 
  FileText,
  Zap,
  Shield,
  TrendingUp,
  MessageSquare,
  Send,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  ExternalLink
} from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { 
  getCandidate, 
  getEvaluation, 
  getComments, 
  addComment,
  evaluateCandidate,
  type Candidate,
  type EvaluationResult,
  type Comment
} from '@/lib/api'

interface CandidateDetailProps {
  candidateId: string
  onBack: () => void
}

export default function CandidateDetail({ candidateId, onBack }: CandidateDetailProps) {
  const [newComment, setNewComment] = useState('')
  const [authorName, setAuthorName] = useState('')
  const queryClient = useQueryClient()

  // Queries
  const { data: candidate, isLoading: loadingCandidate } = useQuery({
    queryKey: ['candidate', candidateId],
    queryFn: () => getCandidate(candidateId),
  })

  const { data: evaluation, isLoading: loadingEval, refetch: refetchEval, error: evalError } = useQuery({
    queryKey: ['evaluation', candidateId],
    queryFn: async () => {
      try {
        const result = await getEvaluation(candidateId)
        console.log('[DEBUG] Evaluación obtenida:', result)
        return result
      } catch (err) {
        console.error('[DEBUG] Error al obtener evaluación:', err)
        throw err
      }
    },
    retry: 1,
    staleTime: 0, // Siempre refetch
    refetchOnMount: true,
  })

  const { data: comments = [] } = useQuery({
    queryKey: ['comments', candidateId],
    queryFn: () => getComments(candidateId),
  })

  // Mutations
  const evaluateMutation = useMutation({
    mutationFn: () => evaluateCandidate(candidateId, undefined, true),
    onSuccess: () => {
      toast.success('Evaluación completada')
      refetchEval()
    },
    onError: (err: Error) => {
      toast.error(`Error al evaluar: ${err.message}`)
    },
  })

  const commentMutation = useMutation({
    mutationFn: () => addComment(candidateId, authorName || 'Anónimo', newComment),
    onSuccess: () => {
      toast.success('Comentario agregado')
      setNewComment('')
      queryClient.invalidateQueries({ queryKey: ['comments', candidateId] })
    },
    onError: (err: Error) => {
      toast.error(`Error: ${err.message}`)
    },
  })

  if (loadingCandidate) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 animate-spin text-accent" />
      </div>
    )
  }

  if (!candidate) {
    return (
      <div className="text-center py-12">
        <p className="text-zinc-500">Candidato no encontrado</p>
        <button onClick={onBack} className="btn-secondary mt-4">Volver</button>
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <header className="flex items-center gap-4 mb-8">
        <button 
          onClick={onBack}
          className="p-2 rounded-lg hover:bg-white/5 transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-zinc-400" />
        </button>
        
        <div className="flex-1">
          <h1 className="text-2xl font-semibold text-white">
            {candidate.nombre_completo}
          </h1>
          <div className="flex items-center gap-4 mt-1 text-sm text-zinc-500">
            <span className="flex items-center gap-1">
              <Mail className="w-4 h-4" />
              {candidate.email}
            </span>
            {candidate.telefono && (
              <span className="flex items-center gap-1">
                <Phone className="w-4 h-4" />
                {candidate.telefono}
              </span>
            )}
          </div>
        </div>

        <button
          onClick={() => evaluateMutation.mutate()}
          disabled={evaluateMutation.isPending}
          className="btn-primary flex items-center gap-2"
        >
          {evaluateMutation.isPending ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Zap className="w-4 h-4" />
          )}
          Re-evaluar
        </button>
      </header>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left: Scores & Analysis */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Score Overview */}
          <div className="glass-panel rounded-2xl p-6">
            <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-accent" />
              Resumen de Evaluación
            </h2>

            {loadingEval ? (
              <div className="text-center py-8 text-zinc-500">
                <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2" />
                Cargando evaluación...
              </div>
            ) : !evaluation ? (
              <div className="text-center py-8">
                <AlertCircle className="w-8 h-8 text-amber-500 mx-auto mb-3" />
                <p className="text-zinc-400 mb-4">Este candidato aún no ha sido evaluado</p>
                <button
                  onClick={() => evaluateMutation.mutate()}
                  disabled={evaluateMutation.isPending}
                  className="btn-primary"
                >
                  Evaluar ahora
                </button>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Main Score */}
                <div className="flex items-center gap-6">
                  <div className="relative">
                    <svg className="w-24 h-24 transform -rotate-90">
                      <circle
                        cx="48"
                        cy="48"
                        r="40"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="8"
                        className="text-zinc-800"
                      />
                      <circle
                        cx="48"
                        cy="48"
                        r="40"
                        fill="none"
                        stroke="url(#scoreGradient)"
                        strokeWidth="8"
                        strokeDasharray={`${evaluation.score_promedio * 2.51} 251`}
                        strokeLinecap="round"
                      />
                      <defs>
                        <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                          <stop offset="0%" stopColor="#6366f1" />
                          <stop offset="100%" stopColor="#a855f7" />
                        </linearGradient>
                      </defs>
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-2xl font-bold text-white font-mono">
                        {evaluation.score_promedio}
                      </span>
                    </div>
                  </div>

                  <div className="flex-1">
                    <div className="text-sm text-zinc-500 mb-1">Perfil Inferido</div>
                    <div className="text-lg font-medium text-white mb-2">
                      {evaluation.inference.profile_type}
                    </div>
                    <div className={`text-sm ${
                      evaluation.inference.retention_risk === 'Alto' 
                        ? 'text-red-400' 
                        : 'text-emerald-400'
                    }`}>
                      {evaluation.inference.risk_warning}
                    </div>
                  </div>
                </div>

                {/* Category Scores */}
                <div className="grid grid-cols-3 gap-4">
                  {Object.entries(evaluation.fits).map(([key, cat]) => (
                    <CategoryCard key={key} name={key} data={cat} />
                  ))}
                </div>

                {/* Inference Metrics */}
                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/5">
                  <MetricItem 
                    label="Hands-On Index" 
                    value={`${evaluation.inference.hands_on_index}%`}
                    good={evaluation.inference.hands_on_index >= 60}
                  />
                  <MetricItem 
                    label="Potencial" 
                    value={`${evaluation.inference.potential_score}%`}
                    good={evaluation.inference.potential_score >= 50}
                  />
                  <MetricItem 
                    label="Industry Tier" 
                    value={evaluation.inference.industry_tier}
                    good={evaluation.inference.industry_tier.includes('Fintech') || evaluation.inference.industry_tier.includes('Tech')}
                  />
                  <MetricItem 
                    label="Riesgo Retención" 
                    value={evaluation.inference.retention_risk}
                    good={evaluation.inference.retention_risk === 'Bajo'}
                  />
                </div>
              </div>
            )}
          </div>

          {/* CV Link */}
          {candidate.cv_url && (
            <a 
              href={candidate.cv_url}
              target="_blank"
              rel="noopener noreferrer"
              className="glass-panel rounded-xl p-4 flex items-center gap-3 hover:border-white/10 transition-colors"
            >
              <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
                <FileText className="w-5 h-5 text-accent" />
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium text-white">Ver CV Original</div>
                <div className="text-xs text-zinc-500">Abrir en nueva pestaña</div>
              </div>
              <ExternalLink className="w-4 h-4 text-zinc-500" />
            </a>
          )}
        </div>

        {/* Right: Comments */}
        <div className="space-y-6">
          <div className="glass-panel rounded-2xl p-6">
            <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-accent" />
              Notas y Comentarios
            </h2>

            {/* Comment Form */}
            <div className="space-y-3 mb-6">
              <input
                type="text"
                placeholder="Tu nombre"
                className="input text-sm"
                value={authorName}
                onChange={(e) => setAuthorName(e.target.value)}
              />
              <textarea
                placeholder="Escribe una nota..."
                className="input text-sm min-h-[80px] resize-none"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
              />
              <button
                onClick={() => commentMutation.mutate()}
                disabled={!newComment.trim() || commentMutation.isPending}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {commentMutation.isPending ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
                Guardar nota
              </button>
            </div>

            {/* Comments List */}
            <div className="space-y-3">
              {comments.length === 0 ? (
                <p className="text-sm text-zinc-500 text-center py-4">
                  No hay notas aún
                </p>
              ) : (
                comments.map((comment) => (
                  <CommentItem key={comment.id} comment={comment} />
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Category Card
function CategoryCard({ name, data }: { name: string; data: { score: number; found: string[]; reasoning: string } }) {
  const categoryNames: Record<string, string> = {
    admin: 'Admin & Finanzas',
    ops: 'Operaciones',
    biz: 'Growth & Cultura',
  }

  return (
    <div className="bg-zinc-900/50 rounded-xl p-4 border border-white/5">
      <div className="text-xs text-zinc-500 mb-2">{categoryNames[name] || name}</div>
      <div className="text-2xl font-bold text-white font-mono mb-2">{data.score}%</div>
      <div className="text-xs text-zinc-600 line-clamp-2">{data.reasoning}</div>
    </div>
  )
}

// Metric Item
function MetricItem({ label, value, good }: { label: string; value: string; good: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-zinc-500">{label}</span>
      <span className={`text-sm font-medium ${good ? 'text-emerald-400' : 'text-amber-400'}`}>
        {good ? <CheckCircle2 className="w-3 h-3 inline mr-1" /> : null}
        {value}
      </span>
    </div>
  )
}

// Comment Item
function CommentItem({ comment }: { comment: Comment }) {
  const date = new Date(comment.created_at).toLocaleDateString('es-CL', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })

  return (
    <div className="bg-zinc-900/50 rounded-lg p-3 border border-white/5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-zinc-300">{comment.autor}</span>
        <span className="text-xs text-zinc-600">{date}</span>
      </div>
      <p className="text-sm text-zinc-400">{comment.comentario}</p>
    </div>
  )
}

