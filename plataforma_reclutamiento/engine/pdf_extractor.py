"""
Extractor de texto de PDFs.
Soporta múltiples backends: pdfplumber, PyPDF2, y OpenAI Vision.
"""

import os
from typing import Optional
from abc import ABC, abstractmethod


class PDFExtractorBase(ABC):
    """Interfaz base para extractores de PDF."""
    
    @abstractmethod
    def extract(self, pdf_path: str) -> str:
        """Extrae texto de un PDF."""
        pass


class PDFPlumberExtractor(PDFExtractorBase):
    """Extractor usando pdfplumber (mejor para tablas)."""
    
    def extract(self, pdf_path: str) -> str:
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except ImportError:
            raise ImportError("pdfplumber no está instalado. Instala con: pip install pdfplumber")
        except Exception as e:
            raise Exception(f"Error extrayendo texto de {pdf_path}: {e}")


class PyPDF2Extractor(PDFExtractorBase):
    """Extractor usando PyPDF2 (más rápido, menos preciso)."""
    
    def extract(self, pdf_path: str) -> str:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        except ImportError:
            raise ImportError("PyPDF2 no está instalado. Instala con: pip install PyPDF2")
        except Exception as e:
            raise Exception(f"Error extrayendo texto de {pdf_path}: {e}")


class OpenAIVisionExtractor(PDFExtractorBase):
    """Extractor usando OpenAI Vision API (mejor para PDFs escaneados)."""
    
    def __init__(self, api_key: Optional[str] = None):
        # Buscar en múltiples variables de entorno
        self.api_key = api_key or os.getenv("OPENAI_API") or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API o OPENAI_API_KEY es requerido para OpenAIVisionExtractor")
    
    def extract(self, pdf_path: str) -> str:
        try:
            import base64
            from openai import OpenAI
            from pdf2image import convert_from_path
            
            client = OpenAI(api_key=self.api_key)
            
            # Convertir PDF a imágenes
            images = convert_from_path(pdf_path)
            
            all_text = []
            for i, image in enumerate(images):
                # Convertir imagen a base64
                import io
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                base64_image = base64.b64encode(buffer.getvalue()).decode()
                
                # Enviar a OpenAI Vision
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Extrae todo el texto de esta imagen de CV. Mantén el formato y estructura. Solo devuelve el texto, sin comentarios adicionales."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=4096
                )
                
                all_text.append(response.choices[0].message.content)
            
            return "\n\n".join(all_text)
            
        except ImportError as e:
            raise ImportError(f"Dependencias faltantes para OpenAI Vision: {e}")
        except Exception as e:
            raise Exception(f"Error con OpenAI Vision: {e}")


class PDFExtractor:
    """
    Extractor de texto de PDFs con soporte para múltiples backends.
    
    Uso:
        extractor = PDFExtractor()
        text = extractor.extract("cv.pdf")
        
        # O con backend específico:
        extractor = PDFExtractor(backend="openai", api_key="...")
        text = extractor.extract("cv_escaneado.pdf")
    """
    
    BACKENDS = {
        "pdfplumber": PDFPlumberExtractor,
        "pypdf2": PyPDF2Extractor,
        "openai": OpenAIVisionExtractor
    }
    
    def __init__(self, backend: str = "pdfplumber", **kwargs):
        """
        Inicializa el extractor.
        
        Args:
            backend: "pdfplumber" (default), "pypdf2", o "openai"
            **kwargs: Argumentos adicionales para el backend
        """
        if backend not in self.BACKENDS:
            raise ValueError(f"Backend '{backend}' no soportado. Usa: {list(self.BACKENDS.keys())}")
        
        self.backend_name = backend
        self._extractor = self.BACKENDS[backend](**kwargs)
    
    def extract(self, pdf_path: str) -> str:
        """
        Extrae texto de un archivo PDF.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Texto extraído del PDF
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Archivo no encontrado: {pdf_path}")
        
        return self._extractor.extract(pdf_path)
    
    def extract_with_fallback(self, pdf_path: str) -> str:
        """
        Intenta extraer con el backend principal, si falla usa fallback.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Texto extraído del PDF
        """
        try:
            text = self.extract(pdf_path)
            if text.strip():
                return text
        except Exception:
            pass
        
        # Fallback a pypdf2 si no es el backend actual
        if self.backend_name != "pypdf2":
            try:
                fallback = PyPDF2Extractor()
                text = fallback.extract(pdf_path)
                if text.strip():
                    return text
            except Exception:
                pass
        
        # Último fallback: OpenAI Vision para PDFs escaneados
        try:
            import os
            api_key = os.getenv("OPENAI_API") or os.getenv("OPENAI_API_KEY")
            if api_key:
                vision = OpenAIVisionExtractor(api_key)
                text = vision.extract(pdf_path)
                if text.strip():
                    return text
        except Exception as e:
            print(f"[DEBUG] OpenAI Vision fallback failed: {e}")
            pass
        
        # Si todo falla, retornar string vacío
        return ""

