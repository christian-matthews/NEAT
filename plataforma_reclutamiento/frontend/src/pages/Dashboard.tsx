import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { 
  Search, 
  Users, 
  TrendingUp, 
  AlertTriangle,
  ArrowUpRight,
  Zap,
  Target,
  RefreshCw
} from 'lucide-react'
import { useState } from 'react'
import { getCandidates, getDashboardStats, type Candidate, type DashboardStats } from '@/lib/api'

interface DashboardProps {
  onSelectCandidate: (id: string) => void
}

export default function Dashboard({ onSelectCandidate }: DashboardProps) {
  const [search, setSearch] = useState('')

  const { data: candidates, isLoading, refetch } = useQuery({
    queryKey: ['candidates'],
    queryFn: getCandidates,
  })

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: getDashboardStats,
  })

  const filtered = candidates?.filter(c => 
    c.nombre_completo.toLowerCase().includes(search.toLowerCase()) ||
    c.email.toLowerCase().includes(search.toLowerCase())
  ) || []

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white mb-1 flex items-center gap-3">
            Dashboard
            <span className="text-xs font-normal px-2 py-1 rounded-full bg-accent/10 text-accent border border-accent/20">
              AI Powered
            </span>
          </h1>
          <p className="text-sm text-zinc-500">
            Vista general de candidatos y métricas del proceso
          </p>
        </div>
        
        <button 
          onClick={() => refetch()}
          className="btn-secondary flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Actualizar
        </button>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Candidatos"
          value={stats?.total_candidatos || 0}
          icon={<Users className="w-5 h-5" />}
          color="accent"
        />
        <StatCard
          title="Score Promedio"
          value={`${stats?.score_promedio?.toFixed(0) || 0}%`}
          subtitle="Target: 70%"
          icon={<Target className="w-5 h-5" />}
          color="success"
        />
        <StatCard
          title="Evaluados"
          value={stats?.candidatos_evaluados || 0}
          subtitle={`${stats?.candidatos_pendientes || 0} pendientes`}
          icon={<TrendingUp className="w-5 h-5" />}
          color="info"
        />
        <StatCard
          title="Alto Riesgo"
          value={stats?.candidatos_alto_riesgo || 0}
          subtitle="Requieren atención"
          icon={<AlertTriangle className="w-5 h-5" />}
          color="warning"
        />
      </div>

      {/* Candidates Table */}
      <div className="glass-panel rounded-2xl overflow-hidden">
        {/* Search Bar */}
        <div className="p-4 border-b border-white/5">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
            <input
              type="text"
              placeholder="Buscar candidatos por nombre o email..."
              className="input pl-11"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        {/* Table Header */}
        <div className="grid grid-cols-12 gap-4 px-6 py-3 border-b border-white/5 text-xs font-medium text-zinc-500 uppercase tracking-wider">
          <div className="col-span-4">Candidato</div>
          <div className="col-span-2">Score</div>
          <div className="col-span-2">Hands-On</div>
          <div className="col-span-2">Riesgo</div>
          <div className="col-span-2 text-right">Perfil</div>
        </div>

        {/* Table Body */}
        <div className="divide-y divide-white/5">
          {isLoading ? (
            <div className="p-12 text-center text-zinc-500">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-3" />
              Cargando candidatos...
            </div>
          ) : filtered.length === 0 ? (
            <div className="p-12 text-center text-zinc-500">
              No se encontraron candidatos
            </div>
          ) : (
            filtered.map((candidate, index) => (
              <CandidateRow
                key={candidate.id}
                candidate={candidate}
                index={index}
                onClick={() => onSelectCandidate(candidate.id)}
              />
            ))
          )}
        </div>
      </div>
    </div>
  )
}

// Stat Card Component
interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ReactNode
  color: 'accent' | 'success' | 'warning' | 'info'
}

function StatCard({ title, value, subtitle, icon, color }: StatCardProps) {
  const colorClasses = {
    accent: 'from-accent/20 to-accent/5 text-accent',
    success: 'from-emerald-500/20 to-emerald-500/5 text-emerald-400',
    warning: 'from-amber-500/20 to-amber-500/5 text-amber-400',
    info: 'from-sky-500/20 to-sky-500/5 text-sky-400',
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel rounded-xl p-5 relative overflow-hidden group hover:border-white/10 transition-colors"
    >
      {/* Background gradient */}
      <div className={`absolute inset-0 bg-gradient-to-br ${colorClasses[color]} opacity-50`} />
      
      <div className="relative">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
            {title}
          </span>
          <span className={colorClasses[color].split(' ')[1]}>
            {icon}
          </span>
        </div>
        
        <div className="text-3xl font-bold text-white font-mono">
          {value}
        </div>
        
        {subtitle && (
          <div className="text-xs text-zinc-500 mt-1">
            {subtitle}
          </div>
        )}
      </div>
    </motion.div>
  )
}

// Candidate Row Component
interface CandidateRowProps {
  candidate: Candidate
  index: number
  onClick: () => void
}

function CandidateRow({ candidate, index, onClick }: CandidateRowProps) {
  const scoreColor = candidate.score_promedio >= 80 
    ? 'score-high' 
    : candidate.score_promedio >= 60 
      ? 'score-medium' 
      : 'score-low'

  const riskColor = candidate.retention_risk === 'Alto'
    ? 'text-red-400'
    : candidate.retention_risk === 'Medio'
      ? 'text-amber-400'
      : 'text-zinc-500'

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.03 }}
      onClick={onClick}
      className="grid grid-cols-12 gap-4 px-6 py-4 items-center interactive-item cursor-pointer group"
    >
      {/* Candidate Info */}
      <div className="col-span-4 flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-zinc-700 to-zinc-800 flex items-center justify-center text-sm font-bold text-white border border-white/10">
          {candidate.nombre_completo.charAt(0)}
        </div>
        <div>
          <div className="text-sm font-medium text-zinc-200 group-hover:text-white transition-colors">
            {candidate.nombre_completo}
          </div>
          <div className="text-xs text-zinc-600 truncate max-w-[200px]">
            {candidate.email}
          </div>
        </div>
      </div>

      {/* Score */}
      <div className="col-span-2">
        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium border ${scoreColor}`}>
          <Zap className="w-3 h-3" />
          {candidate.score_promedio}%
        </span>
      </div>

      {/* Hands On */}
      <div className="col-span-2">
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-accent to-purple-500 rounded-full transition-all"
              style={{ width: `${candidate.hands_on_index}%` }}
            />
          </div>
          <span className="text-xs text-zinc-500 font-mono w-8">
            {candidate.hands_on_index}%
          </span>
        </div>
      </div>

      {/* Risk */}
      <div className="col-span-2">
        <span className={`text-xs font-medium ${riskColor}`}>
          {candidate.retention_risk === 'Alto' && '🚨 '}
          {candidate.retention_risk}
        </span>
      </div>

      {/* Profile Type */}
      <div className="col-span-2 flex items-center justify-end gap-2">
        <span className="text-xs text-zinc-500 truncate max-w-[120px]">
          {candidate.profile_type || '-'}
        </span>
        <ArrowUpRight className="w-4 h-4 text-zinc-600 opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>
    </motion.div>
  )
}

