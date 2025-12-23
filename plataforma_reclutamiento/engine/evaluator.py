"""
Motor de Evaluación de Candidatos NEAT v2.0

Este módulo contiene la lógica principal de evaluación de CVs usando
análisis de keywords, inferencia de perfil y multiplicadores de industria.
"""

from typing import Dict, List, Optional, Any
from .models import (
    EvaluationConfig,
    EvaluationResult,
    CategoryResult,
    InferenceResult,
    ProfileType,
    RetentionRisk,
    IndustryTier,
    CompanyInfo
)


class CandidateEvaluator:
    """
    Motor de evaluación de candidatos.
    
    Analiza el texto de un CV y genera scores basados en:
    - Coincidencia de keywords por categoría
    - Recencia de experiencia (primeros 35% del CV)
    - Multiplicadores por industria
    - Inferencia de tipo de perfil
    - Detección de riesgos
    
    Uso:
        evaluator = CandidateEvaluator()
        result = evaluator.evaluate(cv_text)
        print(result.score_promedio)
    """
    
    # Títulos de cargos con su nivel jerárquico
    TITLE_RANKS = {
        "jefe": 3, "gerente": 4, "subgerente": 3, "director": 4,
        "analista senior": 2, "controller": 3, "contador auditor": 2,
        "encargado": 2, "lider": 2, "head": 4, "lead": 3
    }
    
    # Keywords de potencial/adaptabilidad
    POTENTIAL_KEYWORDS = [
        "aprendizaje", "autodidacta", "adaptación", "flexible",
        "polifuncional", "innovación", "tecnología", "growth"
    ]
    
    # Verbos de acción (indican ejecución)
    ACTION_VERBS = [
        "lideré", "implementé", "gestioné", "creé", "desarrollé",
        "administré", "diseñé", "logré", "aumenté", "reduje"
    ]
    
    def __init__(self, config: Optional[EvaluationConfig] = None):
        """
        Inicializa el evaluador.
        
        Args:
            config: Configuración de evaluación. Si es None, usa la config por defecto.
        """
        self.config = config or EvaluationConfig.default_config()
    
    def set_config(self, config: EvaluationConfig) -> None:
        """Actualiza la configuración del evaluador."""
        self.config = config
    
    def evaluate(
        self,
        text: str,
        company_context: Optional[Dict[str, CompanyInfo]] = None
    ) -> EvaluationResult:
        """
        Evalúa el texto de un CV.
        
        Args:
            text: Texto completo del CV
            company_context: Diccionario de empresas detectadas en el CV
            
        Returns:
            EvaluationResult con scores y análisis completo
        """
        text_lower = text.lower()
        
        # 1. Detectar industria y calcular multiplicador
        industry_tier, industry_multiplier, industry_reasoning = self._detect_industry(
            text_lower, company_context
        )
        
        # 2. Calcular texto reciente (primer 35%)
        recent_text_limit = int(len(text_lower) * 0.35)
        recent_text = text_lower[:recent_text_limit]
        
        # 3. Evaluar cada categoría
        category_results = {}
        for cat_key, cat_config in self.config.categories.items():
            category_results[cat_key] = self._evaluate_category(
                text_lower=text_lower,
                recent_text=recent_text,
                category_key=cat_key,
                category_config=cat_config,
                industry_multiplier=industry_multiplier,
                industry_reasoning=industry_reasoning
            )
        
        # 4. Calcular métricas de inferencia
        inference = self._calculate_inference(
            text_lower=text_lower,
            category_results=category_results,
            industry_tier=industry_tier
        )
        
        # 5. Construir resultado final
        result = EvaluationResult(
            fits=category_results,
            inference=inference,
            config_version=self.config.version
        )
        
        return result
    
    def _detect_industry(
        self,
        text_lower: str,
        company_context: Optional[Dict[str, CompanyInfo]] = None
    ) -> tuple[IndustryTier, float, str]:
        """
        Detecta el tier de industria basándose en empresas conocidas o keywords.
        
        Returns:
            Tuple de (tier, multiplicador, razonamiento)
        """
        tier = IndustryTier.GENERAL
        multiplier = self.config.industry_multipliers.general
        reasoning = ""
        
        if company_context:
            tiers = [info.tier for info in company_context.values()]
            
            if "Fintech" in tiers:
                tier = IndustryTier.FINTECH
                multiplier = self.config.industry_multipliers.fintech
                reasoning = " **Bonus Fintech:** Experiencia directa en industria detectada."
            elif "Tech" in tiers:
                tier = IndustryTier.TECH
                multiplier = self.config.industry_multipliers.tech
                reasoning = " **Bonus Tech:** Experiencia en empresas tecnológicas."
            elif any(t in tiers for t in ["Mining", "Industrial", "Education", "Construction", "Real Estate", "Logistics"]):
                tier = IndustryTier.TRADITIONAL
                multiplier = self.config.industry_multipliers.traditional
                reasoning = " **Alerta Industria:** Experiencia principal en industria tradicional."
        
        # Fallback: detectar por keywords si no hay contexto de empresas
        if tier == IndustryTier.GENERAL and not company_context:
            fintech_kws = ["fintech", "fintoc", "mercadopago", "rappi", "klarna", "stripe"]
            tech_kws = ["startup", "software", "tech", "saas", "platform"]
            traditional_kws = ["minería", "construcción", "educación", "retail", "manufactura"]
            
            if any(kw in text_lower for kw in fintech_kws):
                tier = IndustryTier.FINTECH
                multiplier = self.config.industry_multipliers.fintech
                reasoning = " **Bonus Fintech:** Keywords de industria detectadas."
            elif any(kw in text_lower for kw in tech_kws):
                tier = IndustryTier.TECH
                multiplier = self.config.industry_multipliers.tech
                reasoning = " **Bonus Tech:** Keywords de industria detectadas."
            elif any(kw in text_lower for kw in traditional_kws):
                tier = IndustryTier.TRADITIONAL
                multiplier = self.config.industry_multipliers.traditional
                reasoning = " **Alerta Industria:** Keywords de industria tradicional detectadas."
        
        return tier, multiplier, reasoning
    
    def _evaluate_category(
        self,
        text_lower: str,
        recent_text: str,
        category_key: str,
        category_config: Any,
        industry_multiplier: float,
        industry_reasoning: str
    ) -> CategoryResult:
        """
        Evalúa una categoría específica.
        
        Args:
            text_lower: Texto en minúsculas
            recent_text: Primer 35% del texto
            category_key: Clave de la categoría (admin, ops, biz)
            category_config: Configuración de la categoría
            industry_multiplier: Multiplicador de industria
            industry_reasoning: Texto explicativo del multiplicador
            
        Returns:
            CategoryResult con score y análisis
        """
        keywords = category_config.keywords
        max_expected = category_config.max_expected
        
        # Detectar booster cultural
        booster = 1.0
        culture_kws = category_config.culture_booster_keywords or []
        if culture_kws and any(kw in text_lower for kw in culture_kws):
            booster = 1.25
        
        # Encontrar keywords
        found = list(set(kw for kw in keywords if kw in text_lower))
        missing = [kw for kw in keywords if kw not in found]
        
        # Bonus por recencia
        recent_matches = [kw for kw in found if kw in recent_text]
        recency_bonus = len(recent_matches) * 5
        
        # Calcular score
        base_score = (len(found) / max_expected) * 100
        raw_score = (base_score * booster) + recency_bonus
        final_score = min(raw_score, 100)
        
        # Aplicar multiplicador de industria
        final_score = int(min(final_score * industry_multiplier, 100))
        
        # Construir razonamiento
        reasoning = f"Detectado {len(found)}/{max_expected} conceptos."
        if industry_multiplier != 1.0:
            reasoning += industry_reasoning
        if recent_matches:
            top_recent = ", ".join(recent_matches[:3])
            reasoning += f" **Inferencia Reciente:** {top_recent}."
        
        # Generar preguntas sugeridas
        questions = []
        if category_key == "admin" and missing:
            top_missing = ", ".join(missing[:2])
            questions.append(f"Faltan conceptos clave: {top_missing}. Profundizar.")
        
        return CategoryResult(
            score=final_score,
            found=found,
            missing=missing,
            reasoning=reasoning,
            questions=questions
        )
    
    def _calculate_inference(
        self,
        text_lower: str,
        category_results: Dict[str, CategoryResult],
        industry_tier: IndustryTier
    ) -> InferenceResult:
        """
        Calcula las métricas de inferencia del perfil.
        
        Detecta:
        - Índice Hands-On
        - Tipo de perfil
        - Riesgo de retención
        - Score de potencial
        """
        inference_cfg = self.config.inference
        
        # Hands-On Index
        tech_kws = inference_cfg.technical_keywords
        hands_on_matches = [t for t in tech_kws if t in text_lower]
        hands_on_index = min(int((len(hands_on_matches) / 5) * 100), 100)
        
        # Strategic keywords (para referencia futura)
        strat_kws = inference_cfg.strategic_keywords
        found_strategic = [t for t in strat_kws if t in text_lower]
        
        # Corporate scope
        scope_kws = inference_cfg.corporate_scope_keywords
        found_scope = [t for t in scope_kws if t in text_lower]
        scope_intensity = len(found_scope)
        
        # Detectar títulos de cargo
        found_titles = []
        highest_title_rank = 0
        for title, rank in self.TITLE_RANKS.items():
            if title in text_lower:
                found_titles.append(title)
                if rank > highest_title_rank:
                    highest_title_rank = rank
        
        # Determinar tipo de perfil y riesgo
        profile_type = ProfileType.HYBRID
        risk_warning = "✅ Perfil balanceado."
        retention_risk = RetentionRisk.LOW
        
        if highest_title_rank >= 3 and hands_on_index < 60:
            profile_type = ProfileType.DELEGATOR
            risk_warning = "⚠️ RIESGO: Perfil 'De Escritorio'. Hands-On < 60%."
            
            # Penalizar categoría admin
            if "admin" in category_results:
                old_score = category_results["admin"].score
                new_score = int(old_score * 0.8)
                category_results["admin"].score = new_score
                category_results["admin"].reasoning += " Penalización por perfil delegador."
                
        elif highest_title_rank >= 3 and scope_intensity >= 3:
            profile_type = ProfileType.CORPORATE
            risk_warning = "🚨 ALERTA: Acostumbrado a scopes Regionales/Globales."
            retention_risk = RetentionRisk.HIGH
            
        elif hands_on_index > 60:
            profile_type = ProfileType.HANDS_ON
            risk_warning = "✅ Match Ideal: Sabe operar."
        
        # Calcular potencial
        found_potential = [kw for kw in self.POTENTIAL_KEYWORDS if kw in text_lower]
        potential_score = min(int((len(found_potential) / 4) * 100), 100)
        
        return InferenceResult(
            profile_type=profile_type,
            hands_on_index=hands_on_index,
            risk_warning=risk_warning,
            retention_risk=retention_risk,
            scope_intensity=scope_intensity,
            potential_score=potential_score,
            industry_tier=industry_tier
        )
    
    def detect_companies(
        self,
        text: str,
        knowledge_base: Dict[str, CompanyInfo]
    ) -> Dict[str, CompanyInfo]:
        """
        Detecta empresas conocidas en el texto.
        
        Args:
            text: Texto del CV
            knowledge_base: Base de conocimiento de empresas
            
        Returns:
            Diccionario de empresas encontradas
        """
        text_lower = text.lower()
        found = {}
        
        for company, info in knowledge_base.items():
            if company.lower() in text_lower:
                found[company] = info
        
        return found

