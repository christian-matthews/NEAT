import os
import csv
import glob
import json
from datetime import datetime
import pandas as pd
import pdfplumber
import re

# Consts
CSV_PATH = "postulaciones_FIN-002_2025-12-09.csv"
CVS_DIR = "CVs_FIN-002_2025-12-10"
REPORTS_DIR = "Reports"

# Ensure output directory exists
os.makedirs(REPORTS_DIR, exist_ok=True)

def find_cv_path(tracking_code):
    """Finds the PDF file that matches the tracking code."""
    # Pattern: The tracking code is part of the filename.
    # We'll valid files in the directory
    search_pattern = os.path.join(CVS_DIR, f"*{tracking_code}*.pdf")
    matches = glob.glob(search_pattern)
    if matches:
        return matches[0] # Return the first match
    return None

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file using pdfplumber."""
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Extract text preserving layout might help, but standard extract_text() usually handles spacing better than pypdf
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""

def analyze_cv_heuristic(text):
    """
    Analyzes CV text using keyword matching, heuristics, and semantic inference.
    Returns scores, reasoning, questions, and an INFERRED PROFILE.
    """
    text_lower = text.lower()
    lines = text_lower.split('\n')
    
    # --- 1. EXPERT SYSTEM: INFERENCE ENGINES ---
    
    # A. Job Title Detection
    # We look for high-value titles relevant to the JD
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
            
    # B. Action Analysis (Verifying "What they did")
    # We look for strong verbs near keywords
    action_verbs = ["lideré", "implementé", "gestioné", "creé", "desarrollé", "administré", "diseñé", "logré", "aumenté", "reduje"]
    found_verbs = [v for v in action_verbs if v in text_lower]
    execution_score = len(found_verbs) # Proxy for "Doer" vs "Passive"

    # C. Recent Experience Weighting (Heuristic: First 30% of text is usually recent exp)
    recent_text_limit = int(len(text_lower) * 0.35)
    recent_text = text_lower[:recent_text_limit]
    
    # Helper to calculate score with "Recency" and "Inference" bias
    def evaluate_category(keywords, max_expected, booster=1.0, category_name="General"):
        # 1. Base Search
        found = list(set([kw for kw in keywords if kw in text_lower]))
        missing = [kw for kw in keywords if kw not in found]
        
        # 2. Recency Bonus: Check if these keywords appear in the TOP section (Recent Exp)
        recent_matches = [kw for kw in found if kw in recent_text]
        recency_bonus = len(recent_matches) * 5 # +5 points for each key skill used RECENTLY
        
        # 3. Calculation
        base_score = (len(found) / max_expected) * 100
        final_score = int(min((base_score * booster) + recency_bonus, 100))
        
        # 4. Inference-Based Reasoning
        reasoning = f"Detectado {len(found)}/{max_expected} conceptos."
        if recent_matches:
            reasoning += f" **Inferencia:** Experiencia RECIENTE detectada en: {', '.join(recent_matches[:3])}."
        elif found:
            reasoning += " **Alerta:** Los términos aparecen, pero podrían ser de experiencias antiguas (no en el top del CV)."
            
        if final_score > 90:
            reasoning += " **Nivel Senior:** Dominio profundo del área."
            
        # Questions logic (same as before)
        questions = []
        if category_name == "Admin":
            if "cierre contable" in missing: questions.append("No veo 'Cierre Contable' explícito. ¿Cuál es tu nivel de autonomía cerrando el mes?")
            if "imputación" in missing: questions.append("¿Cómo garantizas la integridad de la imputación de gastos?")
        elif category_name == "Ops":
            if "flujo de caja" not in found: questions.append("El Cash Flow es crítico. ¿Has construido flujos de caja desde cero?")
            if "tesorería" not in found: questions.append("¿Qué volumen de tesorería/pagos has gestionado simultáneamente?")
        elif category_name == "Biz":
            if execution_score < 2: questions.append("Tu perfil parece más de análisis. ¿Qué tres proyectos concretos LIDERASTE e implementaste?")

        return {
            "score": final_score,
            "found": found,
            "missing": missing,
            "reasoning": reasoning,
            "questions": questions,
            "summary": f"{final_score}/100"
        }

    # --- 2. EXECUTE CATEGORY ANALYSIS ---
    
    # Same keyword lists but processed with new logic
    admin_keywords = [
        "cierre contable", "mensual", "imputación", "gastos", "ingresos", 
        "reportes financieros", "análisis de cuentas", "excel", "trazabilidad", 
        "contratos", "auditoría", "estados financieros", "contabilidad", "balance",
        "control administrativo", "procedimientos", "normativa"
    ]
    admin_res = evaluate_category(admin_keywords, max_expected=6, category_name="Admin")

    ops_keywords = [
        "flujo de caja", "cash flow", "semanal", "proyección", "liquidez", 
        "priorizar pagos", "tesorería", "banco", "transferencias", "conciliación bancaria",
        "contingencias", "pagos", "operaciones financieras", "clearing", "recaudación"
    ]
    culture_booster = 1.0
    if any(x in text_lower for x in ["fintech", "startup", "emprendimiento", "rápido crecimiento", "scaleup"]):
        culture_booster = 1.25
    ops_res = evaluate_category(ops_keywords, max_expected=5, booster=culture_booster, category_name="Ops")

    biz_keywords = [
        "procesos", "implementación", "mejora continua", "liderazgo", 
        "equipo", "autonomía", "proactividad", "bi", "business intelligence", 
        "automatización", "eficiencia", "escalable", "estrategia", "kpi",
        "growth", "ownership", "colaboración", "user-centric"
    ]
    biz_res = evaluate_category(biz_keywords, max_expected=6, booster=culture_booster, category_name="Biz")

    # ... (Previous code remains until Section 3 Inference) ...
    
    # --- 3. ADVANCED INFERENCE: HANDS-ON VS STRATEGIC (REAL KNOWLEDGE) ---
    
    # A. Technical Execution Keywords (The "Muddy Boots" indicators)
    # Words that a pure delegator usually omits, but a doer keeps.
    technical_micro_tasks = [
        "imputación", "digitación", "conciliación", "cuadratura", "asiento contable", 
        "análisis de cuentas", "tabla dinámica", "macros", "sap", "erp", 
        "facturación electrónica", "nota de crédito", "orden de compra", 
        "transbank", "portal bancario", "nómina", "previred"
    ]
    found_technical = [t for t in technical_micro_tasks if t in text_lower]
    hands_on_index = int((len(found_technical) / 8) * 100) # Aim for at least 8 technical terms for high hands-on
    hands_on_index = min(hands_on_index, 100)

    # B. Strategic/Delegation Keywords
    strategic_keywords = [
        "dirección", "supervisión", "reporta al directorio", "estrategia", 
        "negociación", "fusión", "adquisición", "board", "comité"
    ]
    found_strategic = [t for t in strategic_keywords if t in text_lower]
    
    # NEW: C. Scope Analysis (Corporate vs Startup) -> Overqualification Risk
    # Keywords indicating a scope much larger than a growing startup might offer
    large_scope_keywords = [
        "regional", "latam", "global", "multinacional", "holding", "filiales", 
        "m&a", "ipo", "apertura en bolsa", "billones", "mmus$", "corporate", 
        "directorio", "gobernanza"
    ]
    found_scope = [t for t in large_scope_keywords if t in text_lower]
    scope_intensity = len(found_scope)
    
    # D. Profile Classification & Risk Assessment
    profile_type = "Híbrido (Gestión + Operación)"
    risk_warning = "✅ Perfil balanceado. Nivel de desafío adecuado."
    retention_risk = "Bajo"
    
    # 1. Delegator Check
    if highest_title_rank >= 3 and hands_on_index < 60:
        profile_type = "Estratégico / Delegador"
        risk_warning = "⚠️ RIESGO: Perfil 'De Escritorio'. Puede frustrarse con tareas operativas (Hands-On < 60%)."
        admin_res['score'] = int(admin_res['score'] * 0.8) 
        admin_res['summary'] = f"{admin_res['score']}/100"
        admin_res['reasoning'] += " Penalización por perfil delegador."
        
    # 2. Overqualification / Boredom Check
    # If they have High Title (Manager/Director) AND High Corporate Scope
    elif highest_title_rank >= 3 and scope_intensity >= 3:
        profile_type = "Corporativo Senior / Overqualified"
        risk_warning = "🚨 ALERTA DE RETENCIÓN: Perfil acostumbrado a scopes Regionales/Globales. El cargo podría 'quedarle chico' (Boredom Risk)."
        retention_risk = "Alto"
        # We might penalize potential match score or just warn hard
        
    elif hands_on_index > 60:
        profile_type = "Ejecutor Hands-On (Alto Ajuste Startup)"
        risk_warning = "✅ Match Ideal: Sabe operar y tiene experiencia."

    # --- 4. POTENTIALITY SCORE (Adaptability & Learning) ---
    potential_keywords = [
        "aprendizaje", "autodidacta", "adaptación", "flexible", "polifuncional",
        "innovación", "tecnología", "nuevas herramientas", "desafío", "growth",
        "rápido", "dinámico", "interés", "curiosidad"
    ]
    found_potential = [t for t in potential_keywords if t in text_lower]
    potential_score = int((len(found_potential) / 4) * 100)
    potential_score = min(potential_score, 100)
    
    potential_reasoning = f"Detectados {len(found_potential)} indicadores de adaptabilidad."
    if retention_risk == "Alto":
        potential_score = int(potential_score * 0.7)
        potential_reasoning += " (Castigado por riesgo de sobrecualificación/fuga)."
    
    # --- Update Inference Data ---
    target_titles = {
        "jefe": 3, "gerente": 4, "subgerente": 3, "director": 4,
        "analista senior": 2, "controller": 3, "contador auditor": 2,
        "encargado": 2, "lider": 2, "head": 4, "lead": 3
    }
    titles_list = [t for t in target_titles if t in text_lower]
    titles_str = ", ".join(titles_list[:2]) if titles_list else "Sin cargos jerárquicos"
    
    inference_data = {
        "profile_name": profile_type,
        "detected_titles": titles_str,
        "hands_on_index": f"{hands_on_index}/100",
        "hands_on_warning": risk_warning,
        "scope_intensity": f"{scope_intensity} (Indicadores Corporativos)",
        "retention_risk": retention_risk,
        "potential_score": f"{potential_score}/100",
        "potential_reasoning": potential_reasoning,
        "summary": f"{profile_type}. Hands-On: {hands_on_index}%. Riesgo Fuga: {retention_risk}."
    }

    return {
        "admin_fit": admin_res,
        "ops_fit": ops_res,
        "biz_fit": biz_res,
        "inference": inference_data
    }

def analyze_cv_llm(text):
    """
    Placeholder for LLM analysis.
    If OpenAI key were present, we would send the text here.
    For now, fallback to heuristic or mocking.
    """
    return None

def generate_markdown(candidate, analysis, cv_text_snippet, company_context):
    """Generates the Markdown report content including reasoning and interview questions."""
    
    md = f"# Reporte de Postulante: {candidate['Nombre Completo']}\n\n"
    md += f"- **Email:** {candidate['Email']}\n"
    md += f"- **Teléfono:** {candidate['Teléfono']}\n"
    md += f"- **Fecha Postulación:** {candidate['Fecha Postulación']}\n"
    md += f"- **Tracking ID:** {candidate['Código Tracking']}\n\n"
    
    # NEW: Inferred Profile Section (High Visibility)
    if 'inference' in analysis:
        inf = analysis['inference']
        md += "## 🔍 Resumen de Perfil Inferido (Expert Analysis)\n"
        md += f"- **Perfil Detectado:** {inf['profile_name']}\n"
        md += f"- **Industria Detectada:** {inf.get('industry_tier', 'No Específica')}\n"
        md += f"- **Cargos Previos Clave:** {inf['detected_titles']}\n"
        md += f"- **Nivel Hands-On:** {inf['hands_on_index']} | **Scope Corporativo:** {inf['scope_intensity']}\n"
        md += f"- **Riesgo de Fuga (Overqualification):** {inf['retention_risk']}\n"
        md += f"- **Potencialidad (Adaptabilidad):** {inf['potential_score']}\n\n"
        
        md += f"> **Conclusión de Seniority:** {inf['hands_on_warning']}\n"
        md += f"> **Conclusión de Potencial:** {inf['potential_reasoning']}\n\n"
    
    # Helper to render section
    def render_section(title, data):
        section = f"## {title}\n"
        section += f"**Nota:** {data['summary']}\n\n"
        section += f"**Razón del Puntaje:** {data['reasoning']}\n\n"
        section += f"**Palabras Clave Encontradas:** {', '.join(data['found'])}\n"
        
        if data['missing']:
             # Show top 5 missing to avoid clutter
            missing_str = ', '.join(data['missing'][:5])
            section += f"**No Detectado (Gaps):** {missing_str}...\n"
            
        if data['questions']:
            section += "\n**Preguntas Sugeridas para Entrevista:**\n"
            for q in data['questions']:
                section += f"- ❓ {q}\n"
        section += "\n"
        return section

    md += render_section("1. Fit Administración y Finanzas (Cierre, Reporting, Control)", analysis['admin_fit'])
    md += render_section("2. Fit Operaciones de Caja y Tesorería (Flujo Semanal, Pagos)", analysis['ops_fit'])
    md += render_section("3. Fit Cultural y Liderazgo (Startup, Procesos, Growth)", analysis['biz_fit'])
    
    if company_context:
        md += "## 4. Contexto de Empresas Detectadas\n"
        for company, description in company_context.items():
            md += f"- **{company}:** {description}\n"
        md += "\n"

    md += "## Extracto del CV (Primeros 500 caracteres)\n"
    md += "```text\n"
    md += cv_text_snippet[:500] + "...\n"
    md += "```\n"
    
    return md

def generate_summary_report(results):
    """Generates a comparative summary markdown table."""
    filepath = os.path.join(REPORTS_DIR, "Resumen_Comparativo.md")
    
    # Sort by total score descending
    results.sort(key=lambda x: (x['scores']['admin'] + x['scores']['ops'] + x['scores']['biz']), reverse=True)
    
    md = "# Resumen Comparativo de Candidatos\n\n"
    md += "| Nombre | Admin & Fin (0-100) | Ops & Pagos (0-100) | Growth & Biz (0-100) | **Hands-On** | **Potencial** | **Riesgo Fuga** | Promedio |\n"
    md += "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n"
    
    for r in results:
        name = r['name']
        s_admin = r['scores']['admin']
        s_ops = r['scores']['ops']
        s_biz = r['scores']['biz']
        
        # New Metrics
        # Extract numeric part from string "25/100" -> 25
        try:
            hands_on = r['inference']['hands_on_index'].split('/')[0]
            potential = r['inference']['potential_score'].split('/')[0]
            risk = r['inference'].get('retention_risk', 'Bajo')
        except:
            hands_on = "N/A"
            potential = "N/A"
            risk = "N/A"

        avg = int((s_admin + s_ops + s_biz) / 3)
        # Add risk emoji
        risk_display = risk
        if risk == "Alto": risk_display = "🚨 Alto"
        
        md += f"| {name} | {s_admin} | {s_ops} | {s_biz} | {hands_on} | {potential} | {risk_display} | **{avg}** |\n"
        
    with open(filepath, "w") as f:
        f.write(md)
    
    print(f"Summary report generated: {filepath}")

def load_company_knowledge():
    """Loads company descriptions from JSON."""
    try:
        with open("company_knowledge.json", "r") as f:
            return json.load(f)
    except:
        return {}

def detect_companies_in_text(text, knowledge_base):
    """Matches text against known companies and returns details."""
    found = {}
    text_lower = text.lower()
    for company, info in knowledge_base.items():
        if company.lower() in text_lower:
            found[company] = info # info is now a dict with 'desc' and 'tier'
    return found

def analyze_cv_heuristic(text, company_context_found=None):
    """
    Analyzes CV text using keyword matching, heuristics, and semantic inference.
    Returns scores, reasoning, questions, and an INFERRED PROFILE.
    """
    text_lower = text.lower()
    lines = text_lower.split('\n')
    
    # --- DETERMINING INDUSTRY TIER & MULTIPLIER ---
    industry_tier = "General"
    industry_multiplier = 1.0
    industry_reasoning = ""
    
    if company_context_found:
        # Check for the best tier among found companies
        tiers = [info['tier'] for info in company_context_found.values()]
        
        if "Fintech" in tiers:
            industry_tier = "Fintech (Ideal)"
            industry_multiplier = 1.5 # Golden Ticket!
            industry_reasoning = " **Bonus Fintech:** Experiencia directa en industria detectada."
        elif "Tech" in tiers:
            industry_tier = "Tech / Digital"
            industry_multiplier = 1.2
            industry_reasoning = " **Bonus Tech:** Experiencia en empresas tecnológicas."
        elif "Mining" in tiers or "Industrial" in tiers or "Education" in tiers or "Construction" in tiers or "Real Estate" in tiers or "Logistics" in tiers:
            # Aggressive Penalty for Traditional Industries (Slow pace, different nature)
            industry_tier = f"Traditional ({tiers[0]})"
            industry_multiplier = 0.7 
            industry_reasoning = " **Alerta Industria:** Experiencia principal en industria tradicional (baja afinidad con Fintech)."
        else:
            industry_tier = "General/Industrial"
            
    # --- 1. EXPERT SYSTEM: INFERENCE ENGINES ---
    
    # A. Job Title Detection
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
            
    # B. Strategic/Delegation Keywords
    strategic_keywords = [
        "dirección", "supervisión", "reporta al directorio", "estrategia", 
        "negociación", "fusión", "adquisición", "board", "comité"
    ]
    found_strategic = [t for t in strategic_keywords if t in text_lower]
    
    # NEW: C. Scope Analysis (Corporate vs Startup) -> Overqualification Risk
    large_scope_keywords = [
        "regional", "latam", "global", "multinacional", "holding", "filiales", 
        "m&a", "ipo", "apertura en bolsa", "billones", "mmus$", "corporate", 
        "directorio", "gobernanza"
    ]
    found_scope = [t for t in large_scope_keywords if t in text_lower]
    scope_intensity = len(found_scope)
    
    # D. Action Analysis
    action_verbs = ["lideré", "implementé", "gestioné", "creé", "desarrollé", "administré", "diseñé", "logré", "aumenté", "reduje"]
    found_verbs = [v for v in action_verbs if v in text_lower]
    execution_score = len(found_verbs) 

    # E. Recent Experience Weighting
    recent_text_limit = int(len(text_lower) * 0.35)
    recent_text = text_lower[:recent_text_limit]
    
    # Helper to calculate score
    def evaluate_category(keywords, max_expected, booster=1.0, category_name="General"):
        found = list(set([kw for kw in keywords if kw in text_lower]))
        missing = [kw for kw in keywords if kw not in found]
        
        recent_matches = [kw for kw in found if kw in recent_text]
        recency_bonus = len(recent_matches) * 5 
        
        base_score = (len(found) / max_expected) * 100
        raw_score_with_bonuses = (base_score * booster) + recency_bonus
        
        # Cap at 100 first, THEN apply industry penalty/bonus
        # This ensures that a 200% match in a "bad industry" still gets penalized below 100
        final_score = min(raw_score_with_bonuses, 100)
        final_score = int(final_score * industry_multiplier)
        
        # Re-cap just in case bonus pushes it over 100 (e.g. Fintech x1.5)
        final_score = min(final_score, 100)
        
        reasoning = f"Detectado {len(found)}/{max_expected} conceptos."
        if industry_multiplier != 1.0:
            reasoning += industry_reasoning
            
        if recent_matches:
            reasoning += f" **Inferencia:** Experiencia RECIENTE detectada en: {', '.join(recent_matches[:3])}."
            
        if final_score > 90:
            reasoning += " **Nivel Senior:** Dominio profundo del área."
            
        questions = []
        if category_name == "Admin":
            if "cierre contable" in missing: questions.append("No veo 'Cierre Contable' explícito. ¿Cuál es tu nivel de autonomía cerrando el mes?")
            if "imputación" in missing: questions.append("¿Cómo garantizas la integridad de la imputación de gastos?")
        elif category_name == "Ops":
            if "flujo de caja" not in found: questions.append("El Cash Flow es crítico. ¿Has construido flujos de caja desde cero?")
            if "tesorería" not in found: questions.append("¿Qué volumen de tesorería/pagos has gestionado simultáneamente?")
        elif category_name == "Biz":
            if execution_score < 2: questions.append("Tu perfil parece más de análisis. ¿Qué tres proyectos concretos LIDERASTE e implementaste?")

        return {
            "score": final_score,
            "found": found,
            "missing": missing,
            "reasoning": reasoning,
            "questions": questions,
            "summary": f"{final_score}/100"
        }

    # --- 2. EXECUTE CATEGORY ANALYSIS ---\n
    admin_keywords = [
        "cierre contable", "mensual", "imputación", "gastos", "ingresos", 
        "reportes financieros", "análisis de cuentas", "excel", "trazabilidad", 
        "contratos", "auditoría", "estados financieros", "contabilidad", "balance",
        "control administrativo", "procedimientos", "normativa"
    ]
    admin_res = evaluate_category(admin_keywords, max_expected=6, category_name="Admin")

    ops_keywords = [
        "flujo de caja", "cash flow", "semanal", "proyección", "liquidez", 
        "priorizar pagos", "tesorería", "banco", "transferencias", "conciliación bancaria",
        "contingencias", "pagos", "operaciones financieras", "clearing", "recaudación"
    ]
    culture_booster = 1.0
    if any(x in text_lower for x in ["fintech", "startup", "emprendimiento", "rápido crecimiento", "scaleup"]):
        culture_booster = 1.25
        
    ops_res = evaluate_category(ops_keywords, max_expected=5, booster=culture_booster, category_name="Ops")

    biz_keywords = [
        "procesos", "implementación", "mejora continua", "liderazgo", 
        "equipo", "autonomía", "proactividad", "bi", "business intelligence", 
        "automatización", "eficiencia", "escalable", "estrategia", "kpi",
        "growth", "ownership", "colaboración", "user-centric"
    ]
    biz_res = evaluate_category(biz_keywords, max_expected=6, category_name="Biz")
    
    # --- 3. CALCULATE INFERENCE METRICS ---
    
    # Technical "Hands-On" Index
    technical_keywords = [
        "imputación", "asiento", "conciliación", "tabla dinámica", "macros", 
        "sql", "erp", "sap", "manager", "digitación", "facturación", "rendición",
        "análisis de cuentas", "balance", "declaración"
    ]
    hands_on_matches = [t for t in technical_keywords if t in text_lower]
    hands_on_index = int((len(hands_on_matches) / 5) * 100) # Expecting 5 terms for 100%
    hands_on_index = min(hands_on_index, 100)
    
    # Profile Classification & Risk Assessment
    profile_type = "Híbrido (Gestión + Operación)"
    risk_warning = "✅ Perfil balanceado. Nivel de desafío adecuado."
    retention_risk = "Bajo"
    
    # 1. Delegator Check
    if highest_title_rank >= 3 and hands_on_index < 60:
        profile_type = "Estratégico / Delegador"
        risk_warning = "⚠️ RIESGO: Perfil 'De Escritorio'. Puede frustrarse con tareas operativas (Hands-On < 60%)."
        admin_res['score'] = int(admin_res['score'] * 0.8) 
        admin_res['summary'] = f"{admin_res['score']}/100"
        admin_res['reasoning'] += " Penalización por perfil delegador."
        
    # 2. Overqualification / Boredom Check
    # If they have High Title (Manager/Director) AND High Corporate Scope
    elif highest_title_rank >= 3 and scope_intensity >= 3:
        profile_type = "Corporativo Senior / Overqualified"
        risk_warning = "🚨 ALERTA DE RETENCIÓN: Perfil acostumbrado a scopes Regionales/Globales. El cargo podría 'quedarle chico' (Boredom Risk)."
        retention_risk = "Alto"
        
    elif hands_on_index > 60:
        profile_type = "Ejecutor Hands-On"
        risk_warning = "✅ Match Ideal: Sabe operar y tiene experiencia."

    # --- 4. POTENTIALITY SCORE ---
    potential_keywords = [
        "aprendizaje", "autodidacta", "adaptación", "flexible", "polifuncional",
        "innovación", "tecnología", "nuevas herramientas", "desafío", "growth",
        "rápido", "dinámico", "interés", "curiosidad"
    ]
    found_potential = [t for t in potential_keywords if t in text_lower]
    potential_score = int((len(found_potential) / 4) * 100)
    potential_score = min(potential_score, 100)
    
    potential_reasoning = f"Detectados {len(found_potential)} indicadores."
    if retention_risk == "Alto":
        potential_score = int(potential_score * 0.7)
        potential_reasoning += " (Castigado por riesgo de sobrecualificación)."
    
    # --- Update Inference Data ---
    target_titles = {
        "jefe": 3, "gerente": 4, "subgerente": 3, "director": 4,
        "analista senior": 2, "controller": 3, "contador auditor": 2,
        "encargado": 2, "lider": 2, "head": 4, "lead": 3
    }
    titles_list = [t for t in target_titles if t in text_lower]
    titles_str = ", ".join(titles_list[:2]) if titles_list else "Sin cargos jerárquicos"
    
    inference_data = {
        "profile_name": profile_type,
        "detected_titles": titles_str,
        "hands_on_index": f"{hands_on_index}/100",
        "hands_on_warning": risk_warning,
        "scope_intensity": f"{scope_intensity} (Indicadores Corporativos)",
        "retention_risk": retention_risk,
        "potential_score": f"{potential_score}/100",
        "potential_reasoning": potential_reasoning,
        "industry_tier": industry_tier, 
        "summary": f"{profile_type}. Hands-On: {hands_on_index}%. Riesgo Fuga: {retention_risk}."
    }

    return {
        "admin_fit": admin_res,
        "ops_fit": ops_res,
        "biz_fit": biz_res,
        "inference": inference_data
    }

def main():
    print("Loading CSV...")
    try:
        df = pd.read_csv(CSV_PATH)
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return

    company_knowledge = load_company_knowledge()
    print(f"Loaded {len(company_knowledge)} company descriptions.")
    print(f"Found {len(df)} candidates.")

    all_results = []

    for index, row in df.iterrows():
        name = row['Nombre Completo']
        tracking_id = row['Código Tracking']
        print(f"Processing {name} ({tracking_id})...")

        pdf_path = find_cv_path(tracking_id)
        
        if pdf_path:
            text = extract_text_from_pdf(pdf_path)
            
            # Company Context
            company_context = detect_companies_in_text(text, company_knowledge)
            
            # Enrich text
            enriched_text = text + "\n"
            if company_context:
                enriched_text += "\n--- CONTEXTO EMPRESAS ---\n"
                for info in company_context.values():
                    if isinstance(info, dict):
                        enriched_text += f"{info.get('desc', '')}\n"
                    else:
                        enriched_text += f"{str(info)}\n"

            # Hybrid Analysis
            # Pass company_context to heuristic analysis for multipliers
            analysis = analyze_cv_heuristic(enriched_text, company_context_found=company_context)
            
            # Pass company_context values (descriptions) to markdown generator
            # Need to extract descriptions from the dicts for the generator
            company_descriptions_only = {}
            for k, v in company_context.items():
                if isinstance(v, dict):
                    company_descriptions_only[k] = v.get('desc', '')
                else:
                    company_descriptions_only[k] = str(v)
            
            report_content = generate_markdown(row, analysis, text, company_descriptions_only)
            
            # Save Report
            filename = f"{name.replace(' ', '_')}_{tracking_id}_Report.md"
            filepath = os.path.join(REPORTS_DIR, filename)
            with open(filepath, "w") as f:
                f.write(report_content)
                
            # Collect for summary
            all_results.append({
                "name": name,
                "scores": {
                    "admin": analysis['admin_fit']['score'],
                    "ops": analysis['ops_fit']['score'],
                    "biz": analysis['biz_fit']['score']
                },
                "inference": analysis.get('inference', {}) 
            })
            
            print(f"  Report generated: {filename}")
        else:
            print("  CV PDF not found.")

    generate_summary_report(all_results)
    print("\nProcessing Complete. Reports saved in 'Reports/' directory.")

if __name__ == "__main__":
    main()
