"""
CanaryFile Engine - Generator Package
Injects canary tracking web bugs and URI trigger payloads into document file structures.
"""

from generator.pdf_injector import PDFCanaryInjector
from generator.builder import PDFCanaryBuilder

__version__ = "0.1.0"
__all__ = ["PDFCanaryInjector", "PDFCanaryBuilder"]
