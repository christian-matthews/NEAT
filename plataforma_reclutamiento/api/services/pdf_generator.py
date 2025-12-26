"""
Generador de PDF para resumen de procesos de reclutamiento.
"""

from fpdf import FPDF
from typing import List, Dict, Any
from datetime import datetime
import io


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
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', align='C')
        
    def section_title(self, title: str):
        """Título de sección con estilo."""
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(80, 60, 180)  # Purple
        self.cell(0, 10, title, ln=True)
        self.set_draw_color(80, 60, 180)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)
        
    def subsection_title(self, title: str):
        """Subtítulo de sección."""
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(60, 60, 60)
        self.cell(0, 8, title, ln=True)
        self.ln(2)


def generate_proceso_pdf(
    proceso: Dict[str, Any],
    candidatos: List[Dict[str, Any]],
    evaluaciones: Dict[str, Dict[str, Any]],
    comentarios: Dict[str, List[Dict[str, Any]]]
) -> bytes:
    """
    Genera un PDF con el resumen completo del proceso de reclutamiento.
    
    Args:
        proceso: Datos del proceso
        candidatos: Lista de candidatos del proceso
        evaluaciones: Dict de evaluaciones por candidato_id
        comentarios: Dict de comentarios por candidato_id
        
    Returns:
        bytes del PDF generado
    """
    pdf = ProcesoReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # ==========================================================================
    # PÁGINA 1: RESUMEN EJECUTIVO
    # ==========================================================================
    
    # Título principal
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 15, 'Resumen de Proceso', ln=True, align='C')
    
    pdf.set_font('Helvetica', '', 16)
    pdf.set_text_color(80, 60, 180)
    cargo_nombre = proceso.get('cargo_nombre', proceso.get('cargo', 'Sin cargo'))
    pdf.cell(0, 10, cargo_nombre, ln=True, align='C')
    
    pdf.ln(5)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Código: {proceso.get('codigo_proceso', 'N/A')}", ln=True, align='C')
    pdf.cell(0, 6, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    # Estadísticas generales
    pdf.section_title('Estadísticas Generales')
    
    total = len(candidatos)
    
    # Clasificar candidatos por estado
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
    
    # Box de stats
    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(50, 50, 50)
    
    stats_data = [
        ('Total Candidatos', str(total)),
        ('Evaluados', f"{evaluados} ({int(evaluados/total*100) if total else 0}%)"),
        ('Score Promedio', f"{avg_score:.0f}%"),
        ('Pendientes', str(len(pendientes))),
        ('En Entrevista', str(len(en_entrevista))),
        ('Rechazados', str(len(rechazados))),
        ('Avanzan/Finalistas', str(len(avanzan))),
    ]
    
    for label, value in stats_data:
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(60, 7, f"  • {label}:", ln=False)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 7, value, ln=True)
    
    pdf.ln(10)
    
    # ==========================================================================
    # PÁGINA 2: VISTA CANVAS (4 COLUMNAS)
    # ==========================================================================
    pdf.add_page()
    pdf.section_title('Pipeline de Candidatos')
    
    # Calcular ancho de columnas
    col_width = 45
    col_height = 8
    start_x = 12
    
    # Headers de columnas
    columns = [
        ('Pendientes', pendientes, (100, 100, 100)),
        ('En Entrevista', en_entrevista, (59, 130, 246)),
        ('Rechazados', rechazados, (239, 68, 68)),
        ('Avanzan', avanzan, (34, 197, 94)),
    ]
    
    # Dibujar headers
    pdf.set_y(pdf.get_y() + 5)
    header_y = pdf.get_y()
    
    for i, (title, candidates, color) in enumerate(columns):
        x = start_x + (i * col_width)
        pdf.set_xy(x, header_y)
        pdf.set_fill_color(*color)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(col_width - 2, 8, f"{title} ({len(candidates)})", fill=True, align='C')
    
    pdf.ln(12)
    content_start_y = pdf.get_y()
    
    # Encontrar el máximo de candidatos en una columna
    max_candidates = max(len(c[1]) for c in columns) if columns else 0
    
    # Dibujar candidatos en cada columna
    for row_idx in range(min(max_candidates, 25)):  # Máximo 25 por columna en esta página
        for col_idx, (_, candidates, color) in enumerate(columns):
            x = start_x + (col_idx * col_width)
            y = content_start_y + (row_idx * col_height)
            
            if row_idx < len(candidates):
                c = candidates[row_idx]
                eval_data = evaluaciones.get(c['id'], {})
                score = eval_data.get('score_promedio', '-')
                
                pdf.set_xy(x, y)
                pdf.set_text_color(50, 50, 50)
                pdf.set_font('Helvetica', '', 7)
                
                nombre = c.get('nombre_completo', 'N/A')[:20]
                score_str = f" ({score}%)" if isinstance(score, (int, float)) else ""
                pdf.cell(col_width - 2, col_height - 1, f"{nombre}{score_str}", border=1, align='L')
    
    # ==========================================================================
    # PÁGINAS SIGUIENTES: FICHAS DE CANDIDATOS
    # ==========================================================================
    
    # Ordenar: primero los que avanzan, luego rechazados
    candidatos_ordenados = avanzan + rechazados
    
    for candidato in candidatos_ordenados:
        pdf.add_page()
        
        cid = candidato['id']
        eval_data = evaluaciones.get(cid, {})
        coms = comentarios.get(cid, [])
        estado = candidato.get('estado_candidato', 'nuevo')
        
        # Header del candidato
        pdf.set_font('Helvetica', 'B', 18)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 12, candidato.get('nombre_completo', 'Sin nombre'), ln=True)
        
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
            pdf.cell(0, 6, f"Teléfono: {candidato['telefono']}", ln=True)
        pdf.cell(0, 6, f"Código: {candidato.get('codigo_tracking', 'N/A')}", ln=True)
        pdf.ln(5)
        
        # Scores de evaluación
        if eval_data:
            pdf.subsection_title('Evaluación IA')
            
            score_promedio = eval_data.get('score_promedio', 0)
            pdf.set_font('Helvetica', 'B', 14)
            
            # Color basado en score
            if score_promedio >= 70:
                pdf.set_text_color(34, 197, 94)
            elif score_promedio >= 50:
                pdf.set_text_color(234, 179, 8)
            else:
                pdf.set_text_color(239, 68, 68)
            
            pdf.cell(0, 8, f"Score General: {score_promedio}%", ln=True)
            
            pdf.set_text_color(60, 60, 60)
            pdf.set_font('Helvetica', '', 10)
            
            # Scores por categoría
            scores_cat = [
                ('Admin & Finanzas', eval_data.get('score_admin', '-')),
                ('Operaciones', eval_data.get('score_ops', '-')),
                ('Growth & Cultura', eval_data.get('score_biz', '-')),
                ('Hands-On Index', eval_data.get('hands_on_index', '-')),
                ('Potencial', eval_data.get('potential_score', '-')),
            ]
            
            for label, score in scores_cat:
                score_str = f"{score}%" if isinstance(score, (int, float)) else str(score)
                pdf.cell(50, 6, f"  • {label}:", ln=False)
                pdf.cell(0, 6, score_str, ln=True)
            
            # Perfil y riesgo
            pdf.ln(3)
            pdf.set_font('Helvetica', 'I', 10)
            profile = eval_data.get('profile_type', 'N/A')
            risk = eval_data.get('retention_risk', 'N/A')
            pdf.cell(0, 6, f"Perfil: {profile} | Riesgo Retención: {risk}", ln=True)
            pdf.ln(5)
        else:
            pdf.set_font('Helvetica', 'I', 10)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 8, "Sin evaluación IA disponible", ln=True)
            pdf.ln(5)
        
        # Comentarios de entrevistas
        pdf.subsection_title('Notas de Entrevistas')
        
        # Filtrar comentarios (excluir los del sistema)
        coms_humanos = [c for c in coms if 'Sistema' not in c.get('autor', '')]
        
        if coms_humanos:
            for com in coms_humanos[:5]:  # Máximo 5 comentarios
                pdf.set_font('Helvetica', 'B', 9)
                pdf.set_text_color(80, 60, 180)
                
                autor = com.get('autor', 'Evaluador')
                fecha = com.get('created_at', '')[:10] if com.get('created_at') else ''
                pdf.cell(0, 6, f"{autor} - {fecha}", ln=True)
                
                pdf.set_font('Helvetica', '', 9)
                pdf.set_text_color(60, 60, 60)
                
                comentario = com.get('comentario', '')
                # Truncar si es muy largo
                if len(comentario) > 500:
                    comentario = comentario[:500] + "..."
                
                pdf.multi_cell(0, 5, comentario)
                pdf.ln(3)
        else:
            pdf.set_font('Helvetica', 'I', 10)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 6, "Sin notas de entrevista", ln=True)
        
        # Link al CV
        if candidato.get('cv_url'):
            pdf.ln(5)
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(59, 130, 246)
            pdf.cell(0, 6, f"CV: {candidato['cv_url'][:80]}...", ln=True)
    
    # Generar bytes del PDF
    return bytes(pdf.output())


def generate_simple_summary(proceso: Dict, candidatos: List) -> bytes:
    """Genera un resumen simple sin evaluaciones detalladas."""
    pdf = ProcesoReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    pdf.set_font('Helvetica', 'B', 20)
    pdf.cell(0, 15, 'Resumen de Proceso', ln=True, align='C')
    pdf.set_font('Helvetica', '', 12)
    pdf.cell(0, 8, proceso.get('cargo_nombre', 'Sin cargo'), ln=True, align='C')
    pdf.cell(0, 8, f"Total: {len(candidatos)} candidatos", ln=True, align='C')
    
    return bytes(pdf.output())

