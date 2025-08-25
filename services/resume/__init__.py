"""
Resume optimization service layer.
Handles AI-powered resume analysis, rewriting, and optimization.
"""

# Import main components for easy access
from .pipeline import ResumeOptimizer
from .schemas import ResumeInput, JDInput, OptimizedResume, GapReport

__all__ = [
    'ResumeOptimizer',
    'ResumeInput', 
    'JDInput',
    'OptimizedResume',
    'GapReport'
]