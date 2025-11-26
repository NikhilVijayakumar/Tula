# src/nikhil/tula/__init__.py
"""
Tula - AI-Powered Code Audit Tool

Simple API for code quality audits with pattern matching + LLM analysis.
"""

from nikhil.tula.tula_auditor import TulaAuditor
from nikhil.tula.domain.code_audit.ai_auditor import AuditResult

__version__ = "1.0.0"

__all__ = [
    "TulaAuditor",
    "AuditResult",
]
