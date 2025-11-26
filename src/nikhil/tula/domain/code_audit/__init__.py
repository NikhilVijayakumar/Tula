"""
Tula Code Audit - AI-powered architectural review system

This package provides AI-powered code review capabilities that can be
integrated into any project's pre-commit hooks.
"""


from .ai_auditor import AIAuditor, AuditConfig, AuditResult

__version__ = "1.5.3"

__all__ = [
    "AIAuditor",
    "AuditConfig", 
    "AuditResult",
]
