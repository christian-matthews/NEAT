"""
Generador de PDF para resumen de procesos de reclutamiento.
"""

from fpdf import FPDF
from typing import List, Dict, Any
from datetime import datetime
import io
import re
import os


def clean_text_for_pdf(text: str) -> str:
    """
    Limpia texto para que sea compatible con fuentes no-Unicode de FPDF.
    Reemplaza caracteres especiales por equivalentes ASCII.
    """
    if not text:
        return ""
    
    # Reemplazos de caracteres Unicode problemáticos
    replacements = {
        '•': '-',
        '–': '-',
        '—': '-',
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
        '…': '...',
        '→': '->',
        '←': '<-',
        '✓': '[OK]',
        '✗': '[X]',
        '★': '*',
        '☆': '*',
        '©': '(c)',
        '®': '(R)',
        '™': '(TM)',
        '°': 'o',
        '±': '+/-',
        '×': 'x',
        '÷': '/',
        '≤': '<=',
        '≥': '>=',
        '≠': '!=',
        '∞': 'inf',
        '\u200b': '',
        '\u200c': '',
        '\u200d': '',
        '\ufeff': '',
        # Caracteres españoles - reemplazar por equivalentes ASCII
        'á': 'a',
        'é': 'e',
        'í': 'i',
        'ó': 'o',
        'ú': 'u',
        'Á': 'A',
        'É': 'E',
        'Í': 'I',
        'Ó': 'O',
        'Ú': 'U',
        'ñ': 'n',
        'Ñ': 'N',
        'ü': 'u',
        'Ü': 'U',
        '¿': '?',
        '¡': '!',
    }
    
    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)
    
    # Reemplazar cualquier otro caracter no-ASCII por espacio
    text = text.encode('ascii', errors='replace').decode('ascii').replace('?', '')
    
    return text


async def summarize_comments_with_ai(comentarios: List[Dict], nombre_candidato: str) -> str:
    """
    Usa IA para resumir todos los comentarios de un candidato en un solo parrafo.
    """
    if not comentarios:
        return "Sin notas de entrevista."
    
    # Construir texto de comentarios
    all_comments = []
    for c in comentarios:
        autor = c.get('autor', 'Evaluador')
        texto = c.get('comentario', '')
        if texto:
            all_comments.append(f"{autor}: {texto}")
    
    if not all_comments:
        return "Sin notas de entrevista."
    
    combined_text = "\n\n".join(all_comments)
    
    # Si es corto, no usar IA
    if len(combined_text) < 300:
        return clean_text_for_pdf(combined_text[:500])
    
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Sin API key, retornar resumen manual
            return clean_text_for_pdf(combined_text[:500] + "...")
        
        client = OpenAI(api_key=api_key)
        
        prompt = f"""Resume las siguientes notas de entrevista sobre el candidato {nombre_candidato} en un solo parrafo conciso (maximo 150 palabras). 
Destaca los puntos positivos y negativos mas importantes. No uses bullet points, escribe en prosa.

NOTAS:
{combined_text}

RESUMEN (en espanol, un solo parrafo):"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3
        )
        
        resumen = response.choices[0].message.content.strip()
        return clean_text_for_pdf(resumen)
        
    except Exception as e:
        print(f"[WARN] Error resumiendo con IA: {e}")
        return clean_text_for_pdf(combined_text[:500] + "...")


class ProcesoReportPDF(FPDF):
    """PDF personalizado para reportes de proceso de reclutamiento."""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'The Wingman - Reporte de Proceso', align='R')
        self.ln(15)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Pagina {self.page_no()}/{{nb}}', align='C')
        
    def section_title(self, title: str):
        """Titulo de seccion con estilo."""
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(80, 60, 180)
        self.cell(0, 10, clean_text_for_pdf(title), ln=True)
        self.set_draw_color(80, 60, 180)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)
        
    def subsection_title(self, title: str):
        """Subtitulo de seccion."""
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(60, 60, 60)
        self.cell(0, 8, clean_text_for_pdf(title), ln=True)
        self.ln(2)


async def generate_proceso_pdf(
    proceso: Dict[str, Any],
    candidatos: List[Dict[str, Any]],
    evaluaciones: Dict[str, Dict[str, Any]],
    comentarios: Dict[str, List[Dict[str, Any]]]
) -> bytes:
    """
    Genera un PDF con el resumen completo del proceso de reclutamiento.
    """
    pdf = ProcesoReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # ==========================================================================
    # PAGINA 1: RESUMEN + PIPELINE
    # ==========================================================================
    
    # Titulo principal
    pdf.set_font('Helvetica', 'B', 22)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 12, 'Resumen de Proceso', ln=True, align='C')
    
    pdf.set_font('Helvetica', '', 14)
    pdf.set_text_color(80, 60, 180)
    cargo_nombre = clean_text_for_pdf(proceso.get('cargo_nombre', proceso.get('cargo', 'Sin cargo')))
    pdf.cell(0, 8, cargo_nombre, ln=True, align='C')
    
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Codigo: {proceso.get('codigo_proceso', 'N/A')} | Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
    pdf.ln(8)
    
    # Clasificar candidatos por estado
    total = len(candidatos)
    pendientes = [c for c in candidatos if c.get('estado_candidato', 'nuevo') in ['nuevo', 'en_revision']]
    en_entrevista = [c for c in candidatos if c.get('estado_candidato') == 'entrevista']
    rechazados = [c for c in candidatos if c.get('estado_candidato') in ['rechazado', 'descartado']]
    avanzan = [c for c in candidatos if c.get('estado_candidato') in ['finalista', 'seleccionado']]
    
    # Calcular score promedio
    scores = []
    for c in candidatos:
        eval_data = evaluaciones.get(c['id'], {})
        if eval_data and eval_data.get('score_promedio'):
            scores.append(eval_data['score_promedio'])
    
    avg_score = sum(scores) / len(scores) if scores else 0
    evaluados = len(scores)
    
    # =========== ESTADISTICAS EN 2 COLUMNAS ===========
    pdf.section_title('Estadisticas')
    
    col_width = 95
    start_y = pdf.get_y()
    
    # Columna izquierda
    stats_left = [
        ('Total Candidatos', str(total)),
        ('Evaluados', f"{evaluados} ({int(evaluados/total*100) if total else 0}%)"),
        ('Score Promedio', f"{avg_score:.0f}%"),
        ('Pendientes', str(len(pendientes))),
    ]
    
    # Columna derecha
    stats_right = [
        ('En Entrevista', str(len(en_entrevista))),
        ('Avanzan/Finalistas', str(len(avanzan))),
        ('Rechazados', str(len(rechazados))),
        ('', ''),  # Espacio vacio
    ]
    
    pdf.set_font('Helvetica', '', 10)
    for i, ((label_l, value_l), (label_r, value_r)) in enumerate(zip(stats_left, stats_right)):
        y_pos = start_y + (i * 7)
        
        # Columna izquierda
        pdf.set_xy(10, y_pos)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(45, 6, f"{label_l}:", ln=False)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(40, 6, value_l, ln=False)
        
        # Columna derecha
        if label_r:
            pdf.set_xy(105, y_pos)
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(60, 60, 60)
            pdf.cell(45, 6, f"{label_r}:", ln=False)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(40, 6, value_r, ln=False)
        
        pdf.set_font('Helvetica', '', 10)
    
    pdf.set_y(start_y + 32)
    pdf.ln(5)
    
    # =========== PIPELINE DE CANDIDATOS (EN PAGINA 1) ===========
    pdf.section_title('Pipeline de Candidatos')
    
    col_width = 45
    col_height = 7
    start_x = 12
    
    columns = [
        ('Pendientes', pendientes, (100, 100, 100)),
        ('Entrevista', en_entrevista, (59, 130, 246)),
        ('Rechazados', rechazados, (239, 68, 68)),
        ('Avanzan', avanzan, (34, 197, 94)),
    ]
    
    # Headers de columnas
    header_y = pdf.get_y()
    for i, (title, candidates, color) in enumerate(columns):
        x = start_x + (i * col_width)
        pdf.set_xy(x, header_y)
        pdf.set_fill_color(*color)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.cell(col_width - 2, 7, f"{title} ({len(candidates)})", fill=True, align='C')
    
    pdf.ln(10)
    content_start_y = pdf.get_y()
    
    max_candidates = max(len(c[1]) for c in columns) if columns else 0
    max_rows = min(max_candidates, 15)  # Maximo 15 por columna en pagina 1
    
    for row_idx in range(max_rows):
        for col_idx, (_, candidates, color) in enumerate(columns):
            x = start_x + (col_idx * col_width)
            y = content_start_y + (row_idx * col_height)
            
            if row_idx < len(candidates):
                c = candidates[row_idx]
                eval_data = evaluaciones.get(c['id'], {})
                score = eval_data.get('score_promedio', '-')
                
                pdf.set_xy(x, y)
                pdf.set_text_color(50, 50, 50)
                pdf.set_font('Helvetica', '', 6)
                
                nombre = clean_text_for_pdf(c.get('nombre_completo', 'N/A'))[:18]
                score_str = f" ({score})" if isinstance(score, (int, float)) else ""
                pdf.cell(col_width - 2, col_height - 1, f"{nombre}{score_str}", border=1, align='L')
    
    # ==========================================================================
    # PAGINA 2: RESUMEN DE CANDIDATOS EN ENTREVISTA
    # ==========================================================================
    if en_entrevista:
        pdf.add_page()
        pdf.section_title('Candidatos en Entrevista - Resumen')
        
        for candidato in en_entrevista:
            cid = candidato['id']
            eval_data = evaluaciones.get(cid, {})
            coms = comentarios.get(cid, [])
            
            # Filtrar solo comentarios humanos
            coms_humanos = [c for c in coms if 'Sistema' not in c.get('autor', '')]
            
            nombre = clean_text_for_pdf(candidato.get('nombre_completo', 'N/A'))
            score = eval_data.get('score_promedio', 0)
            profile = clean_text_for_pdf(eval_data.get('profile_type', 'N/A'))
            
            # Header del candidato
            pdf.set_font('Helvetica', 'B', 11)
            pdf.set_text_color(30, 30, 30)
            
            # Score con color
            if score >= 70:
                score_color = (34, 197, 94)
            elif score >= 50:
                score_color = (234, 179, 8)
            else:
                score_color = (239, 68, 68)
            
            pdf.cell(120, 7, nombre, ln=False)
            pdf.set_text_color(*score_color)
            pdf.cell(0, 7, f"Score: {score}%", ln=True, align='R')
            
            pdf.set_text_color(100, 100, 100)
            pdf.set_font('Helvetica', 'I', 9)
            pdf.cell(0, 5, f"Perfil: {profile}", ln=True)
            
            # Resumen de notas con IA
            if coms_humanos:
                resumen = await summarize_comments_with_ai(coms_humanos, nombre)
                pdf.set_font('Helvetica', '', 9)
                pdf.set_text_color(60, 60, 60)
                pdf.multi_cell(0, 5, resumen)
            else:
                pdf.set_font('Helvetica', 'I', 9)
                pdf.set_text_color(150, 150, 150)
                pdf.cell(0, 5, "Sin notas de entrevista", ln=True)
            
            pdf.ln(5)
            
            # Linea separadora
            pdf.set_draw_color(200, 200, 200)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
    
    # ==========================================================================
    # PAGINAS SIGUIENTES: FICHAS DE FINALISTAS Y RECHAZADOS
    # ==========================================================================
    candidatos_detalle = avanzan + rechazados
    
    for candidato in candidatos_detalle:
        pdf.add_page()
        
        cid = candidato['id']
        eval_data = evaluaciones.get(cid, {})
        coms = comentarios.get(cid, [])
        estado = candidato.get('estado_candidato', 'nuevo')
        
        # Filtrar comentarios humanos
        coms_humanos = [c for c in coms if 'Sistema' not in c.get('autor', '')]
        
        # Header del candidato
        pdf.set_font('Helvetica', 'B', 18)
        pdf.set_text_color(30, 30, 30)
        nombre = clean_text_for_pdf(candidato.get('nombre_completo', 'Sin nombre'))
        pdf.cell(0, 12, nombre, ln=True)
        
        # Badge de estado
        estado_colors = {
            'nuevo': (100, 100, 100),
            'en_revision': (59, 130, 246),
            'entrevista': (234, 179, 8),
            'finalista': (249, 115, 22),
            'seleccionado': (34, 197, 94),
            'rechazado': (239, 68, 68),
            'descartado': (239, 68, 68),
        }
        color = estado_colors.get(estado, (100, 100, 100))
        
        pdf.set_fill_color(*color)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(30, 6, estado.upper(), fill=True, align='C')
        pdf.ln(10)
        
        # Info de contacto
        pdf.set_text_color(80, 80, 80)
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 6, f"Email: {candidato.get('email', 'N/A')}", ln=True)
        if candidato.get('telefono'):
            pdf.cell(0, 6, f"Telefono: {candidato['telefono']}", ln=True)
        pdf.ln(5)
        
        # Scores de evaluacion
        if eval_data:
            pdf.subsection_title('Evaluacion IA')
            
            score_promedio = eval_data.get('score_promedio', 0)
            pdf.set_font('Helvetica', 'B', 14)
            
            if score_promedio >= 70:
                pdf.set_text_color(34, 197, 94)
            elif score_promedio >= 50:
                pdf.set_text_color(234, 179, 8)
            else:
                pdf.set_text_color(239, 68, 68)
            
            pdf.cell(0, 8, f"Score General: {score_promedio}%", ln=True)
            
            # Scores en 2 columnas
            pdf.set_text_color(60, 60, 60)
            pdf.set_font('Helvetica', '', 9)
            
            scores_cat = [
                ('Admin & Finanzas', eval_data.get('score_admin', '-')),
                ('Operaciones', eval_data.get('score_ops', '-')),
                ('Growth & Cultura', eval_data.get('score_biz', '-')),
                ('Hands-On Index', eval_data.get('hands_on_index', '-')),
            ]
            
            for i in range(0, len(scores_cat), 2):
                label1, score1 = scores_cat[i]
                score_str1 = f"{score1}%" if isinstance(score1, (int, float)) else str(score1)
                
                pdf.cell(50, 5, f"{label1}: {score_str1}", ln=False)
                
                if i + 1 < len(scores_cat):
                    label2, score2 = scores_cat[i + 1]
                    score_str2 = f"{score2}%" if isinstance(score2, (int, float)) else str(score2)
                    pdf.cell(50, 5, f"{label2}: {score_str2}", ln=True)
                else:
                    pdf.ln()
            
            pdf.ln(3)
            pdf.set_font('Helvetica', 'I', 9)
            profile = clean_text_for_pdf(eval_data.get('profile_type', 'N/A'))
            risk = clean_text_for_pdf(eval_data.get('retention_risk', 'N/A'))
            pdf.cell(0, 5, f"Perfil: {profile} | Riesgo Retencion: {risk}", ln=True)
            pdf.ln(5)
        
        # Resumen de notas (usando IA para consolidar)
        pdf.subsection_title('Resumen de Entrevistas')
        
        if coms_humanos:
            resumen = await summarize_comments_with_ai(coms_humanos, nombre)
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(0, 5, resumen)
        else:
            pdf.set_font('Helvetica', 'I', 10)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 6, "Sin notas de entrevista", ln=True)
        
        # Link al CV
        if candidato.get('cv_url'):
            pdf.ln(5)
            pdf.set_font('Helvetica', '', 8)
            pdf.set_text_color(59, 130, 246)
            cv_url = candidato['cv_url'][:80] + "..." if len(candidato['cv_url']) > 80 else candidato['cv_url']
            pdf.cell(0, 5, f"CV: {cv_url}", ln=True)
    
    return bytes(pdf.output())


def generate_simple_summary(proceso: Dict, candidatos: List) -> bytes:
    """Genera un resumen simple sin evaluaciones detalladas."""
    pdf = ProcesoReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    pdf.set_font('Helvetica', 'B', 20)
    pdf.cell(0, 15, 'Resumen de Proceso', ln=True, align='C')
    pdf.set_font('Helvetica', '', 12)
    pdf.cell(0, 8, clean_text_for_pdf(proceso.get('cargo_nombre', 'Sin cargo')), ln=True, align='C')
    pdf.cell(0, 8, f"Total: {len(candidatos)} candidatos", ln=True, align='C')
    
    return bytes(pdf.output())
