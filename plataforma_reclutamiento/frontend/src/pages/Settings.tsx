import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { 
  Settings2, 
  Key, 
  Sliders,
  Database,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Code2
} from 'lucide-react'
import { getConfig } from '@/lib/api'

// Alias para compatibilidad
const getKeywords = getConfig

export default function Settings() {
  const { data: keywords, isLoading } = useQuery({
    queryKey: ['keywords'],
    queryFn: getKeywords,
  })

  return (
    <div className="max-w-4xl mx-auto animate-fade-in">
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-2xl font-semibold text-white mb-1 flex items-center gap-3">
          <Settings2 className="w-6 h-6 text-accent" />
          Configuración
        </h1>
        <p className="text-sm text-zinc-500">
          Ajusta los parámetros del motor de evaluación
        </p>
      </header>

      <div className="space-y-6">
        
        {/* Connection Status */}
        <div className="glass-panel rounded-2xl p-6">
          <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-accent" />
            Estado de Conexión
          </h2>
          
          <div className="space-y-3">
            <StatusItem 
              label="API Backend" 
              status="connected" 
              detail="localhost:8000"
            />
            <StatusItem 
              label="Airtable" 
              status="pending" 
              detail="Configura las variables de entorno"
            />
            <StatusItem 
              label="Motor de Evaluación" 
              status="connected" 
              detail="v2.0.0"
            />
          </div>
        </div>

        {/* Keywords Config */}
        <div className="glass-panel rounded-2xl p-6">
          <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
            <Key className="w-5 h-5 text-accent" />
            Keywords del Modelo
          </h2>

          {isLoading ? (
            <div className="text-center py-8 text-zinc-500">
              <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2" />
              Cargando configuración...
            </div>
          ) : !keywords ? (
            <div className="text-center py-8 text-zinc-500">
              No se pudo cargar la configuración
            </div>
          ) : (
            <div className="space-y-6">
              {/* Categories */}
              {keywords.categories && Object.entries(keywords.categories as Record<string, { name: string; keywords: string[] }>).map(([key, cat]) => (
                <KeywordSection 
                  key={key}
                  title={cat.name}
                  keywords={cat.keywords}
                />
              ))}
            </div>
          )}
        </div>

        {/* Multipliers */}
        <div className="glass-panel rounded-2xl p-6">
          <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
            <Sliders className="w-5 h-5 text-accent" />
            Multiplicadores de Industria
          </h2>

          {keywords?.industry_multipliers && (
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(keywords.industry_multipliers as Record<string, number>).map(([key, value]) => (
                <MultiplierItem key={key} industry={key} multiplier={value} />
              ))}
            </div>
          )}
        </div>

        {/* Raw Config */}
        <div className="glass-panel rounded-2xl p-6">
          <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
            <Code2 className="w-5 h-5 text-accent" />
            Configuración Raw (JSON)
          </h2>

          <pre className="bg-zinc-900 rounded-lg p-4 text-xs text-zinc-400 overflow-auto max-h-60 font-mono">
            {JSON.stringify(keywords, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  )
}

// Status Item
function StatusItem({ label, status, detail }: { 
  label: string
  status: 'connected' | 'disconnected' | 'pending'
  detail: string 
}) {
  const statusConfig = {
    connected: {
      icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
    },
    disconnected: {
      icon: <AlertCircle className="w-4 h-4 text-red-400" />,
      color: 'text-red-400',
      bg: 'bg-red-500/10',
    },
    pending: {
      icon: <AlertCircle className="w-4 h-4 text-amber-400" />,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10',
    },
  }

  const config = statusConfig[status]

  return (
    <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/50 border border-white/5">
      <div className="flex items-center gap-3">
        <div className={`w-8 h-8 rounded-lg ${config.bg} flex items-center justify-center`}>
          {config.icon}
        </div>
        <div>
          <div className="text-sm font-medium text-white">{label}</div>
          <div className="text-xs text-zinc-500">{detail}</div>
        </div>
      </div>
      <span className={`text-xs font-medium ${config.color} capitalize`}>
        {status === 'connected' ? 'Conectado' : status === 'pending' ? 'Pendiente' : 'Desconectado'}
      </span>
    </div>
  )
}

// Keyword Section
function KeywordSection({ title, keywords }: { title: string; keywords: string[] }) {
  return (
    <div>
      <h3 className="text-sm font-medium text-zinc-300 mb-2">{title}</h3>
      <div className="flex flex-wrap gap-2">
        {keywords.map((kw, i) => (
          <span 
            key={i}
            className="px-2 py-1 text-xs bg-zinc-800 text-zinc-400 rounded-md border border-white/5"
          >
            {kw}
          </span>
        ))}
      </div>
    </div>
  )
}

// Multiplier Item
function MultiplierItem({ industry, multiplier }: { industry: string; multiplier: number }) {
  const industryNames: Record<string, string> = {
    fintech: 'Fintech',
    tech: 'Tech / Digital',
    general: 'General',
    traditional: 'Tradicional',
  }

  const color = multiplier > 1 
    ? 'text-emerald-400' 
    : multiplier < 1 
      ? 'text-red-400' 
      : 'text-zinc-400'

  return (
    <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/50 border border-white/5">
      <span className="text-sm text-zinc-300">{industryNames[industry] || industry}</span>
      <span className={`text-sm font-mono font-bold ${color}`}>
        x{multiplier.toFixed(1)}
      </span>
    </div>
  )
}

