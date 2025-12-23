import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { api, PublicProcess } from '../lib/api'

export default function Apply() {
  const [processes, setProcesses] = useState<PublicProcess[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)
  const [trackingCode, setTrackingCode] = useState('')
  const [error, setError] = useState('')

  // Form state
  const [formData, setFormData] = useState({
    nombre_completo: '',
    email: '',
    telefono: '',
    proceso_id: '',
  })
  const [cvFile, setCvFile] = useState<File | null>(null)
  const [consent, setConsent] = useState(false)

  useEffect(() => {
    loadProcesses()
  }, [])

  const loadProcesses = async () => {
    try {
      const data = await api.getPublicProcesses()
      setProcesses(data)
    } catch (err) {
      console.error('Error loading processes:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!cvFile) {
      setError('Debes adjuntar tu CV')
      return
    }

    if (!consent) {
      setError('Debes aceptar los términos y condiciones')
      return
    }

    setError('')
    setSubmitting(true)

    try {
      const response = await api.submitApplication(
        formData.nombre_completo,
        formData.email,
        formData.telefono,
        formData.proceso_id,
        cvFile
      )

      setTrackingCode(response.codigo_tracking)
      setSuccess(true)
    } catch (err: any) {
      setError(err.message || 'Error al enviar postulación')
    } finally {
      setSubmitting(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Validar tipo
      const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
      if (!validTypes.includes(file.type)) {
        setError('Solo se permiten archivos PDF, DOC o DOCX')
        return
      }
      // Validar tamaño (10MB)
      if (file.size > 10 * 1024 * 1024) {
        setError('El archivo no debe superar 10MB')
        return
      }
      setCvFile(file)
      setError('')
    }
  }

  // Success view
  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-md"
        >
          <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-8 shadow-2xl text-center">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring' }}
              className="w-20 h-20 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full flex items-center justify-center mx-auto mb-6"
            >
              <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </svg>
            </motion.div>

            <h1 className="text-2xl font-bold text-white mb-4">
              ¡Postulación Enviada!
            </h1>
            
            <p className="text-slate-400 mb-6">
              Hemos recibido tu información correctamente. Este es tu código de seguimiento:
            </p>

            <div className="bg-slate-900/50 border-2 border-cyan-500/50 rounded-xl p-4 mb-6">
              <p className="text-2xl font-mono font-bold text-cyan-400">
                {trackingCode}
              </p>
            </div>

            <p className="text-slate-500 text-sm">
              Guárdalo para consultar el estado de tu postulación.
            </p>

            <button
              onClick={() => window.location.reload()}
              className="mt-6 px-6 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
            >
              Nueva Postulación
            </button>
          </div>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-lg"
      >
        <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-8 shadow-2xl">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              Postulación
            </h1>
            <p className="text-slate-400 mt-2">
              Completa la información para registrar tu postulación
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <AnimatePresence>
              {error && (
                <motion.div 
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="bg-red-500/10 border border-red-500/50 rounded-lg p-3 text-red-400 text-sm"
                >
                  {error}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Nombre */}
            <div>
              <label htmlFor="nombre_completo" className="block text-sm font-medium text-slate-300 mb-2">
                Nombre completo <span className="text-red-400">*</span>
              </label>
              <input
                id="nombre_completo"
                name="nombre_completo"
                type="text"
                value={formData.nombre_completo}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
                placeholder="Juan Pérez González"
                required
              />
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                Correo electrónico <span className="text-red-400">*</span>
              </label>
              <input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
                placeholder="tu@email.com"
                required
              />
            </div>

            {/* Teléfono */}
            <div>
              <label htmlFor="telefono" className="block text-sm font-medium text-slate-300 mb-2">
                Teléfono celular <span className="text-red-400">*</span>
              </label>
              <input
                id="telefono"
                name="telefono"
                type="tel"
                value={formData.telefono}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
                placeholder="+56 9 1234 5678"
                required
              />
            </div>

            {/* Proceso */}
            <div>
              <label htmlFor="proceso_id" className="block text-sm font-medium text-slate-300 mb-2">
                Proceso al que postulas <span className="text-red-400">*</span>
              </label>
              <select
                id="proceso_id"
                name="proceso_id"
                value={formData.proceso_id}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
                required
              >
                <option value="">Selecciona un proceso</option>
                {processes.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.cargo_nombre} - {p.codigo_proceso} ({p.vacantes} vacante{p.vacantes > 1 ? 's' : ''})
                  </option>
                ))}
              </select>
              {loading && (
                <p className="text-slate-500 text-sm mt-1">Cargando procesos...</p>
              )}
            </div>

            {/* CV */}
            <div>
              <label htmlFor="cv_file" className="block text-sm font-medium text-slate-300 mb-2">
                Curriculum Vitae (PDF o DOC) <span className="text-red-400">*</span>
              </label>
              <input
                id="cv_file"
                name="cv_file"
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={handleFileChange}
                className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-cyan-500 file:text-white hover:file:bg-cyan-400 transition-colors"
                required
              />
              {cvFile && (
                <p className="text-slate-400 text-sm mt-1">
                  ✓ {cvFile.name} ({(cvFile.size / 1024 / 1024).toFixed(2)} MB)
                </p>
              )}
            </div>

            {/* Consentimiento */}
            <div className="flex items-start space-x-3">
              <input
                id="consent"
                type="checkbox"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
                className="mt-1 w-4 h-4 text-cyan-500 bg-slate-900 border-slate-700 rounded focus:ring-cyan-500 focus:ring-offset-slate-900"
              />
              <label htmlFor="consent" className="text-sm text-slate-400">
                Acepto los{' '}
                <a href="/terminos" className="text-cyan-400 hover:underline">
                  términos y condiciones
                </a>{' '}
                y autorizo el tratamiento de mis datos personales.
              </label>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={submitting || !consent}
              className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-semibold rounded-lg hover:from-cyan-400 hover:to-blue-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-900 transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-6"
            >
              {submitting ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Enviando...
                </span>
              ) : (
                'Enviar Postulación'
              )}
            </button>
          </form>

          {/* Link a login */}
          <div className="mt-6 text-center">
            <a href="/login" className="text-cyan-400 hover:text-cyan-300 text-sm transition-colors">
              Acceso Staff
            </a>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

