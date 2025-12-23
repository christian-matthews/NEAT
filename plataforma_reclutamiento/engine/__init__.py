# The Wingman Evaluation Engine
# Motor de evaluación de candidatos con IA

from .evaluator import CandidateEvaluator
from .pdf_extractor import PDFExtractor
from .cv_processor import CVProcessor, CVData
from .models import (
    EvaluationConfig,
    CategoryConfig,
    InferenceConfig,
    EvaluationResult,
    CategoryResult,
    InferenceResult
)

__all__ = [
    'CandidateEvaluator',
    'PDFExtractor',
    'CVProcessor',
    'CVData',
    'EvaluationConfig',
    'CategoryConfig',
    'InferenceConfig',
    'EvaluationResult',
    'CategoryResult',
    'InferenceResult'
]

__version__ = '2.0.0'

