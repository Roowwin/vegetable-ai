"""
AI Model Router
===============
Routes queries to the appropriate model based on complexity.

Three models:
- Router (small): For simple queries, quick responses
- General (medium): For most business questions
- Advanced (large): For complex analysis

All models run locally via Ollama.
"""

from enum import Enum
from typing import Optional
import re


class ModelRole(str, Enum):
    """Which model to use for a query."""
    ROUTER = "router"      # Small model for simple queries
    GENERAL = "general"    # Medium model for most queries
    ADVANCED = "advanced"  # Large model for complex analysis


# Keywords that suggest simple/router queries
SIMPLE_KEYWORDS = [
    "how many", "count", "list", "show me", "what is the",
    "total", "current", "status of", "is there",
]

# Keywords that suggest complex/advanced queries
COMPLEX_KEYWORDS = [
    "why", "analyze", "compare", "predict", "forecast",
    "should we", "recommend", "strategy", "anomaly",
    "investigate", "explain why", "what if", "root cause",
    "compare across", "trend", "correlation", "optimize",
    "is this normal", "what's causing", "evaluate",
]


def estimate_complexity(query: str) -> ModelRole:
    """
    Estimate query complexity to decide which model to use.
    
    Heuristics:
    - Very short queries (1-3 words) Ã¢â€ â€™ ROUTER
    - Contains complex keywords Ã¢â€ â€™ ADVANCED
    - Contains simple keywords Ã¢â€ â€™ ROUTER
    - Multi-part questions Ã¢â€ â€™ ADVANCED
    - Default Ã¢â€ â€™ GENERAL
    """
    query_lower = query.lower().strip()
    word_count = len(query_lower.split())
    
    # Very short = simple
    if word_count <= 3:
        return ModelRole.ROUTER
    
    # Check for complex keywords
    complex_matches = sum(1 for kw in COMPLEX_KEYWORDS if kw in query_lower)
    if complex_matches >= 1:
        return ModelRole.ADVANCED
    
    # Check for simple keywords
    simple_matches = sum(1 for kw in SIMPLE_KEYWORDS if kw in query_lower)
    if simple_matches >= 1 and complex_matches == 0:
        return ModelRole.ROUTER
    
    # Multi-part questions (contain "and" or "?")
    question_marks = query_lower.count("?")
    if question_marks >= 2:
        return ModelRole.ADVANCED
    
    # Long questions with multiple sentences
    if word_count > 20:
        return ModelRole.ADVANCED
    
    # Default: medium
    return ModelRole.GENERAL


# Model name mappings (Ollama model identifiers)
MODEL_NAMES = {
    ModelRole.ROUTER: "qwen2.5:7b",                # Use only model with reliable tool support
    ModelRole.GENERAL: "qwen2.5:7b",                # Medium, supports tool calling
    ModelRole.ADVANCED: "qwen2.5:7b",                # Large, powerful
}


def select_model(query: str, override: Optional[ModelRole] = None) -> ModelRole:
    """
    Select which model to use for a query.
    
    Args:
        query: The user's question
        override: Force a specific model (for testing)
    
    Returns:
        The ModelRole to use
    """
    if override:
        return override
    return estimate_complexity(query)


def get_model_name(role: ModelRole) -> str:
    """Get the Ollama model name for a role."""
    return MODEL_NAMES[role]
