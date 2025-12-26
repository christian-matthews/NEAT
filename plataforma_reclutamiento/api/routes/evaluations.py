"""
Rutas de la API para evaluación de candidatos.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional
import sys
import os

# Agregar el path del engine
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ..models import EvaluateRequest, EvaluationResponse, CategoryResultSchema, InferenceResultSchema
from ..services.airtable import AirtableService
from engine import CandidateEvaluator, PDFExtractor, CVProcessor, EvaluationConfig

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])


def get_airtable_service() -> AirtableService:
    """Dependency para obtener el servicio de Airtable."""
    return AirtableService.from_env()


def get_evaluator() -> CandidateEvaluator:
    """Dependency para obtener el evaluador."""
    return CandidateEvaluator()


def get_pdf_extractor() -> PDFExtractor:
    """Dependency para obtener el extractor de PDFs."""
    return PDFExtractor()


# ============================================================================
# Análisis Inteligente de Comentarios con IA
# ============================================================================

async def analyze_interview_feedback(comentarios: list) -> dict:
    """
    Analiza comentarios de entrevista con IA para extraer ajustes de evaluación.
    
    Args:
        comentarios: Lista de comentarios de evaluadores
        
    Returns:
        Dict con ajustes de score basados en el análisis
    """
    if not comentarios:
        return {}
    
    # Construir texto de comentarios
    feedback_text = "\n\n".join([
        f"**{c.get('autor', 'Evaluador')}** ({c.get('created_at', 'sin fecha')}):\n{c.get('comentario', '')}"
        for c in comentarios
    ])
    
    if len(feedback_text.strip()) < 50:
        return {}
    
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("[WARN] No hay API key de OpenAI para análisis de comentarios")
            return {}
        
        client = OpenAI(api_key=api_key)
        
        prompt = """Analiza los siguientes comentarios de entrevista de un candidato y extrae ajustes de evaluación.

COMENTARIOS DE EVALUADORES:
---
{feedback}
---

Basándote en los comentarios, genera ajustes de score en formato JSON. 

REGLAS DE AJUSTE (IMPORTANTES):
- Comentarios MUY NEGATIVOS ("no match cultural", "descartar", "no funciona", "mala actitud") -> score 30-50%
- Comentarios NEGATIVOS ("brechas", "falta experiencia", "sin ownership") -> score 50-65%
- Comentarios MIXTOS (positivos y negativos) -> score 60-75%
- Comentarios POSITIVOS -> mantener 80%+
- Si mencionan "perfil ejecutor" o "sin ownership" -> hands_on_index bajo (30-50%)
- Si mencionan "brecha para rol Senior" -> potential_score bajo (30-50%)
- Si mencionan "riesgo de que se vaya" o "no match cultural" -> retention_risk "Alto"

Responde SOLO con JSON válido, sin explicaciones:
{{
    "score_promedio": número 0-100 (OBLIGATORIO si hay comentarios negativos),
    "hands_on_index": null o número 0-100,
    "potential_score": null o número 0-100,
    "retention_risk": null o "Alto" o "Medio" o "Bajo",
    "reasoning": "Explicación breve de los ajustes"
}}

IMPORTANTE: Si el evaluador indica que quiere descartar o sacar del proceso al candidato, el score_promedio debe ser 40% o menos."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt.format(feedback=feedback_text)}
            ],
            max_tokens=500,
            temperature=0
        )
        
        response_text = response.choices[0].message.content.strip()
        print(f"[DEBUG] Respuesta OpenAI: {response_text[:200]}...")
        
        # Limpiar respuesta de markdown
        import re as regex_module
        json_match = regex_module.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            response_text = json_match.group()
        
        import json
        adjustments = json.loads(response_text)
        print(f"[DEBUG] Ajustes parseados: {adjustments}")
        
        # Filtrar valores null
        result = {}
        for key in ['score_promedio', 'hands_on_index', 'potential_score', 'retention_risk']:
            if adjustments.get(key) is not None:
                result[key] = adjustments[key]
        
        if result:
            print(f"[INFO] ✅ Ajustes IA de comentarios: {result}")
            if adjustments.get('reasoning'):
                print(f"[INFO] Razón: {adjustments['reasoning']}")
        else:
            print(f"[WARN] No se detectaron ajustes en la respuesta")
        
        return result
        
    except Exception as e:
        import traceback
        print(f"[ERROR] Error analizando comentarios con IA: {e}")
        traceback.print_exc()
        return {}


# ============================================================================
# Evaluation Endpoints
# ============================================================================

@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_candidate(
    request: EvaluateRequest,
    airtable: AirtableService = Depends(get_airtable_service),
    evaluator: CandidateEvaluator = Depends(get_evaluator),
    pdf_extractor: PDFExtractor = Depends(get_pdf_extractor)
):
    """
    Evalúa un candidato usando el motor de IA.
    
    - Si cv_text está presente, usa ese texto
    - Si no, extrae el texto del PDF (cv_url del candidato)
    - Guarda los resultados en Airtable
    """
    try:
        # Verificar si ya existe evaluación (cache)
        if not request.force_reeval:
            existing = await airtable.get_evaluacion(request.candidato_id)
            if existing and existing.get("id"):
                return EvaluationResponse(
                    id=existing["id"],
                    candidato_id=request.candidato_id,
                    score_promedio=existing.get("score_promedio", 0),
                    fits={},  # No tenemos el detalle en cache simple
                    inference=InferenceResultSchema(
                        profile_type=existing.get("profile_type", ""),
                        hands_on_index=existing.get("hands_on_index", 0),
                        retention_risk=existing.get("retention_risk", "Bajo"),
                        industry_tier=existing.get("industry_tier", "General")
                    ),
                    cached=True
                )
        
        # Obtener texto del CV
        cv_text = request.cv_text
        if not cv_text:
            # Obtener candidato para conseguir cv_url
            candidato = await airtable.get_candidato_by_id(request.candidato_id)
            if not candidato or not candidato.get("cv_url"):
                raise HTTPException(
                    status_code=400,
                    detail="No se encontró el CV del candidato. Proporciona cv_text o asegúrate que el candidato tiene cv_url."
                )
            
            # Extraer texto del PDF
            cv_url = candidato["cv_url"]
            
            # Si es una URL remota, necesitamos descargar primero
            if cv_url.startswith("http"):
                import httpx
                import tempfile
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(cv_url)
                    response.raise_for_status()
                    
                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                        tmp.write(response.content)
                        tmp_path = tmp.name
                
                cv_text = pdf_extractor.extract_with_fallback(tmp_path)
                os.unlink(tmp_path)  # Limpiar archivo temporal
            else:
                # Es un path local
                cv_text = pdf_extractor.extract_with_fallback(cv_url)
        
        if not cv_text or not cv_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No se pudo extraer texto del CV"
            )
        
        # Ejecutar evaluación
        result = evaluator.evaluate(cv_text)
        
        # Preparar datos para Airtable
        evaluation_data = {
            "score_promedio": result.score_promedio,
            "config_version": result.config_version,
            "fits": {
                k: {
                    "score": v.score,
                    "found": v.found,
                    "missing": v.missing,
                    "reasoning": v.reasoning,
                    "questions": v.questions
                }
                for k, v in result.fits.items()
            },
            "inference": {
                "profile_type": result.inference.profile_type.value,
                "hands_on_index": result.inference.hands_on_index,
                "risk_warning": result.inference.risk_warning,
                "retention_risk": result.inference.retention_risk.value,
                "scope_intensity": result.inference.scope_intensity,
                "potential_score": result.inference.potential_score,
                "industry_tier": result.inference.industry_tier.value
            }
        }
        
        # Guardar en Airtable
        saved = await airtable.create_evaluacion(request.candidato_id, evaluation_data)
        
        # Formatear respuesta
        fits_response = {
            k: CategoryResultSchema(
                score=v.score,
                found=v.found,
                missing=v.missing,
                reasoning=v.reasoning,
                questions=v.questions
            )
            for k, v in result.fits.items()
        }
        
        inference_response = InferenceResultSchema(
            profile_type=result.inference.profile_type.value,
            hands_on_index=result.inference.hands_on_index,
            risk_warning=result.inference.risk_warning,
            retention_risk=result.inference.retention_risk.value,
            scope_intensity=result.inference.scope_intensity,
            potential_score=result.inference.potential_score,
            industry_tier=result.inference.industry_tier.value
        )
        
        return EvaluationResponse(
            id=saved.get("id"),
            candidato_id=request.candidato_id,
            score_promedio=result.score_promedio,
            fits=fits_response,
            inference=inference_response,
            config_version=result.config_version,
            cached=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{candidate_id_or_tracking}", response_model=EvaluationResponse)
async def get_evaluation(
    candidate_id_or_tracking: str,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """
    Obtiene la evaluación de un candidato si existe.
    Acepta tanto record_id de Airtable como codigo_tracking.
    """
    try:
        candidato = None
        tracking_code = None
        candidate_id = candidate_id_or_tracking
        
        # Detectar si es tracking code o record ID
        if candidate_id_or_tracking.startswith("rec"):
            # Es un record ID de Airtable
            candidato = await airtable.get_candidato_by_id(candidate_id_or_tracking)
            tracking_code = candidato.get("codigo_tracking") if candidato else None
        else:
            # Es un tracking code
            tracking_code = candidate_id_or_tracking
            candidato = await airtable.get_candidato(tracking_code)
            candidate_id = candidato.get("id") if candidato else candidate_id_or_tracking
        
        # Buscar evaluación por tracking code o por ID
        evaluacion = await airtable.get_evaluacion(candidate_id, tracking_code)
        
        if not evaluacion or not evaluacion.get("id"):
            raise HTTPException(
                status_code=404,
                detail="Evaluación no encontrada. Usa POST /evaluations/evaluate para evaluar."
            )
        
        return EvaluationResponse(
            id=evaluacion["id"],
            candidato_id=candidate_id,
            score_promedio=evaluacion.get("score_promedio") or 0,
            fits={
                "admin": CategoryResultSchema(score=evaluacion.get("score_admin") or 0),
                "ops": CategoryResultSchema(score=evaluacion.get("score_ops") or 0),
                "biz": CategoryResultSchema(score=evaluacion.get("score_biz") or 0)
            },
            inference=InferenceResultSchema(
                profile_type=evaluacion.get("profile_type") or "",
                hands_on_index=evaluacion.get("hands_on_index") or 0,
                risk_warning=evaluacion.get("risk_warning") or "",
                retention_risk=evaluacion.get("retention_risk") or "Bajo",
                industry_tier=evaluacion.get("industry_tier") or "General"
            ),
            cached=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{candidate_id_or_tracking}/evaluate")
async def evaluate_by_tracking_code(
    candidate_id_or_tracking: str,
    force_reprocess: bool = False,
    airtable: AirtableService = Depends(get_airtable_service),
    evaluator: CandidateEvaluator = Depends(get_evaluator)
):
    """
    Evalúa un candidato usando OpenAI.
    Acepta tanto record_id de Airtable como codigo_tracking.
    
    El proceso:
    1. Obtiene el PDF del CV
    2. Usa OpenAI GPT-4 Vision para extraer toda la información
    3. Guarda la información estructurada en Airtable (campo cv_data_json)
    4. Ejecuta la evaluación basada en keywords
    5. Considera los comentarios/notas del candidato para ajustar la evaluación
    6. Guarda los resultados de evaluación
    
    Args:
        candidate_id_or_tracking: Record ID o código de tracking del candidato
        force_reprocess: Si True, reprocesa el CV aunque ya exista evaluación
    """
    from pathlib import Path
    import tempfile
    import httpx
    import urllib.parse
    
    try:
        # Detectar si es record ID o tracking code
        if candidate_id_or_tracking.startswith("rec"):
            # Es un record ID de Airtable
            candidato = await airtable.get_candidato_by_id(candidate_id_or_tracking)
            codigo_tracking = candidato.get("codigo_tracking") if candidato else None
        else:
            # Es un tracking code
            codigo_tracking = candidate_id_or_tracking
            candidato = await airtable.get_candidato(codigo_tracking)
        
        if not candidato or not candidato.get("id"):
            raise HTTPException(status_code=404, detail=f"Candidato {candidate_id_or_tracking} no encontrado")
        
        candidato_id = candidato["id"]
        estado_candidato = candidato.get("estado_candidato", "nuevo")
        
        # =====================================================================
        # VALIDACIONES Y LÓGICA INTELIGENTE DE RE-EVALUACIÓN
        # =====================================================================
        
        # 1. No re-evaluar candidatos rechazados o descartados
        if estado_candidato in ["rechazado", "descartado"]:
            # Retornar evaluación existente si hay, sino error
            existing = await airtable.get_evaluacion(candidato_id, codigo_tracking)
            if existing and existing.get("id"):
                return {
                    "id": existing["id"],
                    "candidato_codigo": codigo_tracking,
                    "score_total": existing.get("score_promedio", 0),
                    "score_admin": existing.get("score_admin", 0),
                    "score_ops": existing.get("score_ops", 0),
                    "score_biz": existing.get("score_biz", 0),
                    "hands_on_index": existing.get("hands_on_index", 0),
                    "potencial": "Alto" if existing.get("potential_score", 0) >= 70 else ("Medio" if existing.get("potential_score", 0) >= 40 else "Bajo"),
                    "riesgo_retencion": existing.get("retention_risk", "Bajo"),
                    "perfil_tipo": existing.get("profile_type", ""),
                    "industry_tier": existing.get("industry_tier", ""),
                    "cached": True,
                    "skipped": True,
                    "skip_reason": "rechazado"
                }
            raise HTTPException(status_code=400, detail=f"Candidato rechazado sin evaluación previa")
        
        # 2. Obtener evaluación existente y comentarios
        existing = await airtable.get_evaluacion(candidato_id, codigo_tracking)
        comentarios_check = await airtable.get_comentarios(candidato_id)
        
        # 3. Si no se fuerza reproceso, retornar evaluación existente
        if not force_reprocess:
            if existing and existing.get("id"):
                return {
                    "id": existing["id"],
                    "candidato_codigo": codigo_tracking,
                    "score_total": existing.get("score_promedio", 0),
                    "score_admin": existing.get("score_admin", 0),
                    "score_ops": existing.get("score_ops", 0),
                    "score_biz": existing.get("score_biz", 0),
                    "hands_on_index": existing.get("hands_on_index", 0),
                    "potencial": "Alto" if existing.get("potential_score", 0) >= 70 else ("Medio" if existing.get("potential_score", 0) >= 40 else "Bajo"),
                    "riesgo_retencion": existing.get("retention_risk", "Bajo"),
                    "perfil_tipo": existing.get("profile_type", ""),
                    "industry_tier": existing.get("industry_tier", ""),
                    "cached": True
                }
        
        # 4. Si es re-evaluación, verificar si hay comentarios nuevos
        if force_reprocess and existing and existing.get("id"):
            if not comentarios_check or len(comentarios_check) == 0:
                # Sin comentarios → retornar evaluación existente (no error)
                print(f"[INFO] {codigo_tracking}: Sin comentarios, retornando evaluación existente")
                return {
                    "id": existing["id"],
                    "candidato_codigo": codigo_tracking,
                    "score_total": existing.get("score_promedio", 0),
                    "score_admin": existing.get("score_admin", 0),
                    "score_ops": existing.get("score_ops", 0),
                    "score_biz": existing.get("score_biz", 0),
                    "hands_on_index": existing.get("hands_on_index", 0),
                    "potencial": "Alto" if existing.get("potential_score", 0) >= 70 else ("Medio" if existing.get("potential_score", 0) >= 40 else "Bajo"),
                    "riesgo_retencion": existing.get("retention_risk", "Bajo"),
                    "perfil_tipo": existing.get("profile_type", ""),
                    "industry_tier": existing.get("industry_tier", ""),
                    "cached": True,
                    "skipped": True,
                    "skip_reason": "sin_comentarios"
                }
            
            # Verificar si hay comentarios más recientes que la evaluación
            from datetime import datetime
            eval_time = existing.get("created_at", "")
            
            # Buscar el comentario más reciente
            comentario_mas_reciente = None
            for c in comentarios_check:
                c_time = c.get("created_at", "")
                if c_time and (not comentario_mas_reciente or c_time > comentario_mas_reciente):
                    comentario_mas_reciente = c_time
            
            # Si la evaluación es más reciente que todos los comentarios, no re-evaluar
            if eval_time and comentario_mas_reciente and eval_time > comentario_mas_reciente:
                print(f"[INFO] {codigo_tracking}: Evaluación más reciente que comentarios, saltando")
                return {
                    "id": existing["id"],
                    "candidato_codigo": codigo_tracking,
                    "score_total": existing.get("score_promedio", 0),
                    "score_admin": existing.get("score_admin", 0),
                    "score_ops": existing.get("score_ops", 0),
                    "score_biz": existing.get("score_biz", 0),
                    "hands_on_index": existing.get("hands_on_index", 0),
                    "potencial": "Alto" if existing.get("potential_score", 0) >= 70 else ("Medio" if existing.get("potential_score", 0) >= 40 else "Bajo"),
                    "riesgo_retencion": existing.get("retention_risk", "Bajo"),
                    "perfil_tipo": existing.get("profile_type", ""),
                    "industry_tier": existing.get("industry_tier", ""),
                    "cached": True,
                    "skipped": True,
                    "skip_reason": "ya_actualizado"
                }
            
            print(f"[INFO] {codigo_tracking}: Hay comentarios nuevos, re-evaluando...")
        
        # Obtener path al PDF
        cv_url = candidato.get("cv_url")
        cv_attachment = candidato.get("cv_archivo") or candidato.get("cv_attachment")
        pdf_path = None
        temp_file = None
        
        # Intentar primero con attachment de Airtable
        if cv_attachment and isinstance(cv_attachment, list) and len(cv_attachment) > 0:
            attachment_url = cv_attachment[0].get("url")
            if attachment_url:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.get(attachment_url)
                    response.raise_for_status()
                    
                    temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
                    temp_file.write(response.content)
                    temp_file.close()
                    pdf_path = temp_file.name
        
        # Si no hay attachment, buscar archivo local
        if not pdf_path and cv_url:
            if "localhost:8000/files/" in cv_url or "/files/" in cv_url:
                filename = cv_url.split("/files/")[-1]
                filename = urllib.parse.unquote(filename)
                
                cvs_dir = Path(__file__).parent.parent.parent / "data" / "cvs"
                local_path = cvs_dir / filename
                
                if local_path.exists():
                    pdf_path = str(local_path)
            elif cv_url.startswith("http"):
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.get(cv_url)
                    response.raise_for_status()
                    
                    temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
                    temp_file.write(response.content)
                    temp_file.close()
                    pdf_path = temp_file.name
        
        if not pdf_path:
            raise HTTPException(
                status_code=400,
                detail=f"No se encontró el CV para {codigo_tracking}. CV URL: {cv_url}"
            )
        
        # =====================================================================
        # PROCESAR CV CON OPENAI
        # =====================================================================
        
        try:
            print(f"[INFO] Procesando CV con OpenAI: {codigo_tracking}")
            
            # Crear procesador de CV
            cv_processor = CVProcessor()
            
            # Extraer información estructurada del CV
            cv_data = cv_processor.process_pdf(pdf_path)
            
            # Obtener texto completo para evaluación
            cv_text = cv_data.texto_completo
            
            # Guardar datos extraídos en el candidato
            cv_data_json = cv_data.to_json()
            
            # Actualizar candidato con información extraída
            await airtable.update_candidato(candidato_id, {
                "cv_texto": cv_text[:10000] if len(cv_text) > 10000 else cv_text,  # Limitar tamaño
                "cv_data_json": cv_data_json,
                "años_experiencia": cv_data.años_experiencia,
                "titulo_profesional": cv_data.titulo_profesional,
                "resumen_perfil": cv_data.resumen_perfil,
            })
            
            print(f"[INFO] CV procesado. Texto extraído: {len(cv_text)} caracteres")
            
        except Exception as e:
            print(f"[WARN] Error procesando CV con OpenAI: {e}")
            # Fallback a extractor tradicional
            from engine import PDFExtractor
            pdf_extractor = PDFExtractor()
            cv_text = pdf_extractor.extract_with_fallback(pdf_path)
            cv_data = None
        
        finally:
            # Limpiar archivo temporal si existe
            if temp_file:
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
        
        if not cv_text or not cv_text.strip():
            raise HTTPException(
                status_code=400,
                detail=f"No se pudo extraer texto del CV para {codigo_tracking}"
            )
        
        # =====================================================================
        # OBTENER COMENTARIOS/NOTAS PARA CONTEXTO Y AJUSTES
        # =====================================================================
        
        comentarios = await airtable.get_comentarios(candidato_id)
        notas_contexto = ""
        ajustes_manuales = {}
        ajustes_ia = {}
        
        if comentarios:
            notas_contexto = "\n\n=== NOTAS DE EVALUADORES ===\n"
            for c in comentarios:
                nota_texto = c.get('comentario', '')
                notas_contexto += f"- {c.get('autor', 'Usuario')}: {nota_texto}\n"
            
            print(f"[INFO] Incluyendo {len(comentarios)} notas de evaluadores en la evaluación")
            
            # =====================================================================
            # PASO 1: ANÁLISIS INTELIGENTE CON IA (comentarios de texto libre)
            # =====================================================================
            ajustes_ia = await analyze_interview_feedback(comentarios)
            if ajustes_ia:
                print(f"[INFO] Ajustes IA detectados: {ajustes_ia}")
            
            # =====================================================================
            # PASO 2: PARSEAR AJUSTES MANUALES EXPLÍCITOS (tienen prioridad)
            # Formatos: "hands on: 80%", "potencial: bajo", "score: 50%"
            # =====================================================================
            import re
            for c in comentarios:
                nota_texto = c.get('comentario', '')
                nota_lower = nota_texto.lower()
                
                # Hands-On Index
                match = re.search(r'hands?[-\s]?on[:\s]*(?:a\s+)?(\d+)%?', nota_lower)
                if not match:
                    match = re.search(r'indicador\s+(?:a\s+)?(\d+)%?', nota_lower)
                if match:
                    ajustes_manuales['hands_on_index'] = int(match.group(1))
                
                # Potencial
                match = re.search(r'potencial[:\s]+(alto|medio|bajo|\d+)%?', nota_lower)
                if match:
                    valor = match.group(1)
                    if valor == 'alto':
                        ajustes_manuales['potential_score'] = 85
                    elif valor == 'medio':
                        ajustes_manuales['potential_score'] = 55
                    elif valor == 'bajo':
                        ajustes_manuales['potential_score'] = 25
                    else:
                        ajustes_manuales['potential_score'] = int(valor)
                
                # Riesgo Retención
                match = re.search(r'(?:riesgo\s+)?retenci[oó]n[:\s]+(alto|medio|bajo)', nota_lower)
                if match:
                    ajustes_manuales['retention_risk'] = match.group(1).capitalize()
                
                # Score general
                match = re.search(r'score[:\s]+(\d+)%?', nota_lower)
                if match:
                    ajustes_manuales['score_promedio'] = int(match.group(1))
                
                # Admin
                match = re.search(r'admin[:\s]+(\d+)%?', nota_lower)
                if match:
                    ajustes_manuales['score_admin'] = int(match.group(1))
                
                # Ops/Operaciones
                match = re.search(r'(?:ops|operaciones)[:\s]+(\d+)%?', nota_lower)
                if match:
                    ajustes_manuales['score_ops'] = int(match.group(1))
                
                # Biz/Growth
                match = re.search(r'(?:biz|growth|cultura)[:\s]+(\d+)%?', nota_lower)
                if match:
                    ajustes_manuales['score_biz'] = int(match.group(1))
            
            if ajustes_manuales:
                print(f"[INFO] Ajustes manuales explícitos: {ajustes_manuales}")
            
            # =====================================================================
            # PASO 3: COMBINAR AJUSTES (manuales tienen prioridad sobre IA)
            # =====================================================================
            # Primero IA, luego manuales sobrescriben
            ajustes_finales = {**ajustes_ia, **ajustes_manuales}
            ajustes_manuales = ajustes_finales
            
            if ajustes_manuales:
                print(f"[INFO] Ajustes finales aplicados: {ajustes_manuales}")
        
        # Combinar CV con notas para evaluación completa
        texto_completo = cv_text
        if notas_contexto:
            texto_completo += notas_contexto
        
        # =====================================================================
        # EJECUTAR EVALUACIÓN
        # =====================================================================
        
        result = evaluator.evaluate(texto_completo)
        print(f"[DEBUG] Score base del motor: {result.score_promedio}")
        print(f"[DEBUG] Ajustes a aplicar: {ajustes_manuales}")
        
        # Preparar datos para Airtable (aplicando ajustes manuales si existen)
        # Si hay ajuste de score_promedio, también ajustar proporcionalmente admin/ops/biz
        base_score = result.score_promedio
        adjusted_score = ajustes_manuales.get('score_promedio', base_score)
        
        # Si el score fue ajustado, calcular factor de ajuste para las subcategorías
        if 'score_promedio' in ajustes_manuales and base_score > 0:
            adjustment_factor = adjusted_score / base_score
            print(f"[DEBUG] Factor de ajuste: {adjustment_factor:.2f}")
        else:
            adjustment_factor = 1.0
        
        # Obtener scores base
        admin_base = result.fits.get("admin", type("obj", (), {"score": 0})).score if "admin" in result.fits else 0
        ops_base = result.fits.get("ops", type("obj", (), {"score": 0})).score if "ops" in result.fits else 0
        biz_base = result.fits.get("biz", type("obj", (), {"score": 0})).score if "biz" in result.fits else 0
        
        evaluation_data = {
            "score_promedio": adjusted_score,
            "score_admin": ajustes_manuales.get('score_admin', int(admin_base * adjustment_factor)),
            "score_ops": ajustes_manuales.get('score_ops', int(ops_base * adjustment_factor)),
            "score_biz": ajustes_manuales.get('score_biz', int(biz_base * adjustment_factor)),
            "hands_on_index": ajustes_manuales.get('hands_on_index', result.inference.hands_on_index),
            "potential_score": ajustes_manuales.get('potential_score', result.inference.potential_score),
            "retention_risk": ajustes_manuales.get('retention_risk', result.inference.retention_risk.value),
            "profile_type": result.inference.profile_type.value,
            "industry_tier": result.inference.industry_tier.value,
            "config_version": result.config_version
        }
        
        print(f"[INFO] ✅ Evaluación final: score={evaluation_data['score_promedio']}, "
              f"admin={evaluation_data['score_admin']}, ops={evaluation_data['score_ops']}, "
              f"biz={evaluation_data['score_biz']}, hands_on={evaluation_data['hands_on_index']}")
        
        # Guardar evaluación en Airtable
        saved = await airtable.create_evaluacion(candidato_id, evaluation_data, codigo_tracking)
        
        # =====================================================================
        # CREAR COMENTARIO AUTOMÁTICO CON AJUSTES APLICADOS
        # =====================================================================
        if ajustes_manuales and force_reprocess:
            from datetime import datetime
            
            # Construir resumen de ajustes
            ajustes_texto = []
            if 'score_promedio' in ajustes_manuales:
                ajustes_texto.append(f"score: {ajustes_manuales['score_promedio']}%")
            if 'hands_on_index' in ajustes_manuales:
                ajustes_texto.append(f"hands on: {ajustes_manuales['hands_on_index']}%")
            if 'potential_score' in ajustes_manuales:
                pot = ajustes_manuales['potential_score']
                pot_label = "alto" if pot >= 70 else ("medio" if pot >= 40 else "bajo")
                ajustes_texto.append(f"potencial: {pot_label}")
            if 'retention_risk' in ajustes_manuales:
                ajustes_texto.append(f"retención: {ajustes_manuales['retention_risk'].lower()}")
            
            if ajustes_texto:
                fecha_actual = datetime.now().strftime("%d/%m/%Y")
                comentario_auto = f"""AJUSTES AUTOMÁTICOS ({fecha_actual}):

Basado en análisis de notas de entrevista:
- Score ajustado de {int(base_score)}% a {evaluation_data['score_promedio']}%
- Admin/Ops/Biz ajustados proporcionalmente

SCORES APLICADOS:
{', '.join(ajustes_texto)}"""
                
                try:
                    await airtable.create_comentario(
                        candidato_id=candidato_id,
                        autor="Sistema (Re-evaluación IA)",
                        comentario=comentario_auto
                    )
                    print(f"[INFO] ✅ Comentario automático creado con ajustes")
                except Exception as e:
                    print(f"[WARN] No se pudo crear comentario automático: {e}")
        
        # Calcular potencial basado en el score (con ajuste manual aplicado)
        potential = evaluation_data["potential_score"]
        potencial_label = "Alto" if potential >= 70 else ("Medio" if potential >= 40 else "Bajo")
        
        return {
            "id": saved.get("id"),
            "candidato_codigo": codigo_tracking,
            "score_total": evaluation_data["score_promedio"],
            "score_admin": evaluation_data["score_admin"],
            "score_ops": evaluation_data["score_ops"],
            "score_biz": evaluation_data["score_biz"],
            "hands_on_index": evaluation_data["hands_on_index"],
            "potencial": potencial_label,
            "riesgo_retencion": evaluation_data["retention_risk"],
            "perfil_tipo": evaluation_data["profile_type"],
            "industry_tier": evaluation_data["industry_tier"],
            "cv_procesado": cv_data is not None,
            "ajustes_manuales_aplicados": bool(ajustes_manuales),
            "cached": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al evaluar: {str(e)}")


@router.post("/evaluate-text")
async def evaluate_text_only(
    cv_text: str,
    evaluator: CandidateEvaluator = Depends(get_evaluator)
):
    """
    Evalúa un texto de CV sin guardarlo.
    Útil para testing y demos.
    """
    try:
        result = evaluator.evaluate(cv_text)
        
        return {
            "score_promedio": result.score_promedio,
            "fits": {
                k: {
                    "score": v.score,
                    "found": v.found,
                    "missing": v.missing,
                    "reasoning": v.reasoning,
                    "questions": v.questions
                }
                for k, v in result.fits.items()
            },
            "inference": {
                "profile_type": result.inference.profile_type.value,
                "hands_on_index": result.inference.hands_on_index,
                "risk_warning": result.inference.risk_warning,
                "retention_risk": result.inference.retention_risk.value,
                "scope_intensity": result.inference.scope_intensity,
                "potential_score": result.inference.potential_score,
                "industry_tier": result.inference.industry_tier.value
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

