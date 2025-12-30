"""
Procesador de CVs usando OpenAI GPT-4 Vision.
Extrae información estructurada directamente del PDF usando la API de OpenAI.
"""

import os
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class CVData:
    """Datos estructurados extraídos del CV."""
    texto_completo: str
    nombre_completo: str
    email: str
    telefono: str
    ubicacion: str
    linkedin: str
    
    # Experiencia
    años_experiencia: int
    empresas: List[str]
    cargos: List[str]
    industrias: List[str]
    
    # Educación
    titulo_profesional: str
    universidad: str
    postgrados: List[str]
    certificaciones: List[str]
    
    # Habilidades
    habilidades_tecnicas: List[str]
    habilidades_blandas: List[str]
    idiomas: List[str]
    herramientas: List[str]
    
    # Análisis
    resumen_perfil: str
    fortalezas: List[str]
    areas_desarrollo: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "texto_completo": self.texto_completo,
            "nombre_completo": self.nombre_completo,
            "email": self.email,
            "telefono": self.telefono,
            "ubicacion": self.ubicacion,
            "linkedin": self.linkedin,
            "años_experiencia": self.años_experiencia,
            "empresas": self.empresas,
            "cargos": self.cargos,
            "industrias": self.industrias,
            "titulo_profesional": self.titulo_profesional,
            "universidad": self.universidad,
            "postgrados": self.postgrados,
            "certificaciones": self.certificaciones,
            "habilidades_tecnicas": self.habilidades_tecnicas,
            "habilidades_blandas": self.habilidades_blandas,
            "idiomas": self.idiomas,
            "herramientas": self.herramientas,
            "resumen_perfil": self.resumen_perfil,
            "fortalezas": self.fortalezas,
            "areas_desarrollo": self.areas_desarrollo
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class CVProcessor:
    """
    Procesador de CVs usando OpenAI.
    
    Uso:
        processor = CVProcessor()
        cv_data = processor.process_pdf("/path/to/cv.pdf")
        print(cv_data.resumen_perfil)
    """
    
    EXTRACTION_PROMPT = """Analiza este CV y extrae TODA la información en el siguiente formato JSON.
Sé exhaustivo y preciso. Si algún campo no está disponible, usa string vacío "" o lista vacía [].

{
    "texto_completo": "Transcripción completa del CV tal como aparece",
    "nombre_completo": "Nombre completo del candidato",
    "email": "Email de contacto",
    "telefono": "Teléfono con código de país",
    "ubicacion": "Ciudad, País",
    "linkedin": "URL de LinkedIn si existe",
    
    "años_experiencia": número entero de años de experiencia laboral total,
    "empresas": ["Lista de empresas donde ha trabajado"],
    "cargos": ["Lista de cargos que ha tenido"],
    "industrias": ["Industrias en las que tiene experiencia"],
    
    "titulo_profesional": "Título universitario principal",
    "universidad": "Universidad donde estudió",
    "postgrados": ["MBA, Magíster, etc."],
    "certificaciones": ["CPA, CFA, PMP, etc."],
    
    "habilidades_tecnicas": ["Excel avanzado", "SAP", "Python", etc.],
    "habilidades_blandas": ["Liderazgo", "Comunicación", etc.],
    "idiomas": ["Español nativo", "Inglés avanzado", etc.],
    "herramientas": ["SAP", "Oracle", "Power BI", etc.],
    
    "resumen_perfil": "Resumen ejecutivo de 2-3 oraciones describiendo el perfil profesional",
    "fortalezas": ["Lista de 3-5 fortalezas principales"],
    "areas_desarrollo": ["Lista de 1-3 áreas de mejora o gaps identificados"]
}

IMPORTANTE: 
- Responde SOLO con el JSON, sin texto adicional
- El texto_completo debe ser la transcripción fiel del CV
- Calcula años_experiencia sumando la duración de cada trabajo"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API") or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API o OPENAI_API_KEY es requerido")
    
    def process_pdf(self, pdf_path: str) -> CVData:
        """
        Procesa un PDF de CV y extrae información estructurada.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            CVData con toda la información extraída
        """
        from openai import OpenAI
        
        # Convertir PDF a imágenes base64
        images_base64 = self._pdf_to_images(pdf_path)
        
        if not images_base64:
            raise ValueError(f"No se pudo procesar el PDF: {pdf_path}")
        
        # Preparar mensajes para OpenAI
        client = OpenAI(api_key=self.api_key)
        
        # Construir contenido con imágenes
        content = [{"type": "text", "text": self.EXTRACTION_PROMPT}]
        
        for img_b64 in images_base64:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_b64}",
                    "detail": "high"
                }
            })
        
        # Llamar a OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ],
            max_tokens=4096,
            temperature=0
        )
        
        # Parsear respuesta
        response_text = response.choices[0].message.content.strip()
        
        # Limpiar respuesta si viene con markdown
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"Error parseando JSON: {e}")
            print(f"Respuesta: {response_text[:500]}")
            # Intentar extraer JSON de la respuesta
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError(f"No se pudo parsear la respuesta de OpenAI")
        
        return CVData(
            texto_completo=data.get("texto_completo", ""),
            nombre_completo=data.get("nombre_completo", ""),
            email=data.get("email", ""),
            telefono=data.get("telefono", ""),
            ubicacion=data.get("ubicacion", ""),
            linkedin=data.get("linkedin", ""),
            años_experiencia=data.get("años_experiencia", 0),
            empresas=data.get("empresas", []),
            cargos=data.get("cargos", []),
            industrias=data.get("industrias", []),
            titulo_profesional=data.get("titulo_profesional", ""),
            universidad=data.get("universidad", ""),
            postgrados=data.get("postgrados", []),
            certificaciones=data.get("certificaciones", []),
            habilidades_tecnicas=data.get("habilidades_tecnicas", []),
            habilidades_blandas=data.get("habilidades_blandas", []),
            idiomas=data.get("idiomas", []),
            herramientas=data.get("herramientas", []),
            resumen_perfil=data.get("resumen_perfil", ""),
            fortalezas=data.get("fortalezas", []),
            areas_desarrollo=data.get("areas_desarrollo", [])
        )
    
    def process_pdf_text_only(self, pdf_path: str) -> str:
        """
        Extrae solo el texto del CV sin análisis estructurado.
        Más rápido y económico para evaluaciones simples.
        """
        from openai import OpenAI
        
        images_base64 = self._pdf_to_images(pdf_path)
        
        if not images_base64:
            raise ValueError(f"No se pudo procesar el PDF: {pdf_path}")
        
        client = OpenAI(api_key=self.api_key)
        
        content = [{
            "type": "text", 
            "text": "Transcribe todo el texto de este CV exactamente como aparece. Incluye toda la información visible."
        }]
        
        for img_b64 in images_base64:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_b64}",
                    "detail": "high"
                }
            })
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": content}],
            max_tokens=4096,
            temperature=0
        )
        
        return response.choices[0].message.content.strip()
    
    def _pdf_to_images(self, pdf_path: str) -> List[str]:
        """Convierte PDF a lista de imágenes en base64."""
        try:
            from pdf2image import convert_from_path
            import io
            
            # Convertir PDF a imágenes
            images = convert_from_path(pdf_path, dpi=150)
            
            images_base64 = []
            for image in images:
                # Convertir a bytes
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                buffer.seek(0)
                
                # Codificar en base64
                img_b64 = base64.b64encode(buffer.getvalue()).decode()
                images_base64.append(img_b64)
            
            return images_base64
            
        except ImportError:
            # Fallback: intentar leer como imagen directamente
            print("[WARN] pdf2image no instalado, intentando fallback...")
            return self._fallback_pdf_read(pdf_path)
    
    def _fallback_pdf_read(self, pdf_path: str) -> List[str]:
        """Fallback para leer PDF sin pdf2image usando PyMuPDF."""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            images_base64 = []
            
            for page in doc:
                # Renderizar página como imagen
                mat = fitz.Matrix(2, 2)  # Zoom 2x
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")
                img_b64 = base64.b64encode(img_bytes).decode()
                images_base64.append(img_b64)
            
            doc.close()
            return images_base64
            
        except ImportError:
            print("[ERROR] Ni pdf2image ni PyMuPDF están instalados")
            return []




