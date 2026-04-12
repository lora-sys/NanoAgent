"""
领域异常定义

统一的异常层次结构
"""

from .exceptions import (
    NanoAgentError,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
    ToolError,
    ToolNotFoundError,
    ToolSecurityError,
    PhaseError,
    PhaseTimeoutError,
    ConfigError,
    ConfigNotFoundError,
    ConfigValidationError,
    StateError,
    InvalidStateTransitionError,
    SpecError,
    SpecGenerationError,
    SpecValidationError,
    PersistenceError,
    FileAccessError,
)

__all__ = [
    "NanoAgentError",
    "LLMError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "LLMValidationError",
    "ToolError",
    "ToolNotFoundError",
    "ToolSecurityError",
    "PhaseError",
    "PhaseTimeoutError",
    "ConfigError",
    "ConfigNotFoundError",
    "ConfigValidationError",
    "StateError",
    "InvalidStateTransitionError",
    "SpecError",
    "SpecGenerationError",
    "SpecValidationError",
    "PersistenceError",
    "FileAccessError",
]
