import json
import os
import glob
import pdfplumber
import pandas as pd

# Define paths relative to the backend folder or workspace root
# Assuming this runs from workspace root or we adjust paths. 
# Ideally we pass base paths to the engine.

def load_config(config_path="backend/model_config.json"):
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file using pdfplumber."""
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""

def load_company_knowledge(path="company_knowledge.json"):
    """Loads company descriptions from JSON."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return {}

def detect_companies_in_text(text, knowledge_base):
    """Matches text against known companies and returns details."""
    found = {}
    text_lower = text.lower()
    for company, info in knowledge_base.items():
        if company.lower() in text_lower:
            found[company] = info 
    return found

def evaluate_candidate(text, config, company_context_found=None):
    """
    Analyzes CV text using the configuration rules.
    """
    text_lower = text.lower()
    
    # --- INDUSTRY TIER LOGIC ---
    industry_tier = "General"
    industry_multiplier = 1.0
    industry_reasoning = ""
    
    if company_context_found:
        tiers = [info['tier'] for info in company_context_found.values()]
        if "Fintech" in tiers:
            industry_tier = "Fintech (Ideal)"
            industry_multiplier = 1.5
            industry_reasoning = " **Bonus Fintech:** Experiencia directa en industria detectada."
        elif "Tech" in tiers:
            industry_tier = "Tech / Digital"
            industry_multiplier = 1.2
            industry_reasoning = " **Bonus Tech:** Experiencia en empresas tecnológicas."
        elif any(x in tiers for x in ["Mining", "Industrial", "Education", "Construction", "Real Estate", "Logistics"]):
            industry_tier = f"Traditional ({tiers[0]})"
            industry_multiplier = 0.7 
            industry_reasoning = " **Alerta Industria:** Experiencia principal en industria tradicional."

    # --- ACTION VERBS ---
    action_verbs = ["lideré", "implementé", "gestioné", "creé", "desarrollé", "administré", "diseñé", "logré", "aumenté", "reduje"]
    found_verbs = [v for v in action_verbs if v in text_lower]
    execution_score = len(found_verbs)

    # --- RECENT TEXT LIMIT ---
    recent_text_limit = int(len(text_lower) * 0.35)
    recent_text = text_lower[:recent_text_limit]

    # --- CATEGORY EVALUATION ---
    results = {}
    categories = config.get("categories", {})
    
    for cat_key, cat_data in categories.items():
        keywords = cat_data.get("keywords", [])
        max_expected = cat_data.get("max_expected", 5)
        
        # Check for booster
        booster = 1.0
        culture_booster_kws = cat_data.get("culture_booster_keywords", [])
        if culture_booster_kws and any(x in text_lower for x in culture_booster_kws):
            booster = 1.25
            
        found = list(set([kw for kw in keywords if kw in text_lower]))
        missing = [kw for kw in keywords if kw not in found]
        
        recent_matches = [kw for kw in found if kw in recent_text]
        recency_bonus = len(recent_matches) * 5
        
        base_score = (len(found) / max_expected) * 100
        raw_score = (base_score * booster) + recency_bonus
        final_score = min(raw_score, 100)
        
        # Apply industry multiplier
        final_score = int(min(final_score * industry_multiplier, 100))
        
        reasoning = f"Detectado {len(found)}/{max_expected} conceptos."
        if industry_multiplier != 1.0:
            reasoning += industry_reasoning
        if recent_matches:
            reasoning += f" **Inferencia Reciente:** {', '.join(recent_matches[:3])}."
            
        questions = []
        # Basic generic questions logic can be enhanced or moved to config later
        if cat_key == "admin" and len(missing) > 0:
             questions.append(f"Faltan conceptos clave: {', '.join(missing[:2])}. Profundizar.")
             
        results[cat_key] = {
            "score": final_score,
            "found": found,
            "missing": missing,
            "reasoning": reasoning,
            "questions": questions
        }

    # --- INFERENCE METRICS ---
    inf_config = config.get("inference", {})
    
    # Hands On
    tech_kws = inf_config.get("technical_keywords", [])
    hands_on_matches = [t for t in tech_kws if t in text_lower]
    hands_on_index = int((len(hands_on_matches) / 5) * 100)
    hands_on_index = min(hands_on_index, 100)
    
    # Strategic
    strat_kws = inf_config.get("strategic_keywords", [])
    found_strategic = [t for t in strat_kws if t in text_lower] # stored but not used for score yet?
    
    # Scope
    scope_kws = inf_config.get("corporate_scope_keywords", [])
    found_scope = [t for t in scope_kws if t in text_lower]
    scope_intensity = len(found_scope)
    
    # Hiring Titles (we can keep the hardcoded for now or move to config if critical)
    target_titles = {
        "jefe": 3, "gerente": 4, "subgerente": 3, "director": 4,
        "analista senior": 2, "controller": 3, "contador auditor": 2,
        "encargado": 2, "lider": 2, "head": 4, "lead": 3
    }
    found_titles = []
    highest_title_rank = 0
    for title, rank in target_titles.items():
        if title in text_lower:
            found_titles.append(title)
            if rank > highest_title_rank: highest_title_rank = rank
            
    # Risk Logic
    profile_type = "Híbrido (Gestión + Operación)"
    risk_warning = "✅ Perfil balanceado."
    retention_risk = "Bajo"
    
    if highest_title_rank >= 3 and hands_on_index < 60:
        profile_type = "Estratégico / Delegador"
        risk_warning = "⚠️ RIESGO: Perfil 'De Escritorio'. Hands-On < 60%."
        # Penalize Admin
        if "admin" in results:
            results["admin"]["score"] = int(results["admin"]["score"] * 0.8)
            results["admin"]["reasoning"] += " Penalización por perfil delegador."
            
    elif highest_title_rank >= 3 and scope_intensity >= 3:
        profile_type = "Corporativo Senior / Overqualified"
        risk_warning = "🚨 ALERTA: Acostumbrado a scopes Regionales/Globales."
        retention_risk = "Alto"
        
    elif hands_on_index > 60:
        profile_type = "Ejecutor Hands-On"
        risk_warning = "✅ Match Ideal: Sabe operar."

    # Potencial
    pot_kws = ["aprendizaje", "autodidacta", "adaptación", "flexible", "polifuncional", "innovación", "tecnología", "growth"]
    found_pot = [t for t in pot_kws if t in text_lower]
    pot_score = int((len(found_pot) / 4) * 100)
    pot_score = min(pot_score, 100)
    
    return {
        "fits": results,
        "inference": {
            "profile_type": profile_type,
            "hands_on_index": hands_on_index,
            "risk_warning": risk_warning,
            "retention_risk": retention_risk,
            "scope_intensity": scope_intensity,
            "potential_score": pot_score,
            "industry_tier": industry_tier
        }
    }
