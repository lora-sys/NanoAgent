"""NanoAgent core module - backward compatibility exports."""

from domain.models.models import (
    AgentPlan, PlanStep, TaskSpec, RoutingDecision, TaskType,
    Manifest, PipelineStage, TemplateSpecContent,
)
from domain.interfaces.interfaces import (
    ILLMClient, IContextLoader, ISpecGenerator, IRouter,
    IManifestManager, IPersistenceManager, IToolRegistry,
    IConfigManager, ICacheManager,
)
from domain.exceptions.exceptions import (
    NanoAgentError, LLMError, LLMRateLimitError, LLMTimeoutError,
    LLMValidationError, ToolError, ToolNotFoundError, ToolSecurityError,
    PhaseError, PhaseTimeoutError, ConfigError, ConfigNotFoundError,
    ConfigValidationError, StateError, InvalidStateTransitionError,
    SpecError, SpecGenerationError, SpecValidationError,
    PersistenceError, FileAccessError,
)
from domain.entities.state_machine import StateMachine, AgentState
from domain.entities.rule_engine import RuleEngine

from infrastructure.llm.client import NanoLLMClient
from infrastructure.config.manager import ConfigManager, get_config_manager
from infrastructure.cache.manager import CacheManager
from infrastructure.tools.registry import ToolRegistry, get_tool_registry
from infrastructure.container import DIContainer, get_container, reset_container

from core.executor import AgentExecutor
from core.utils import get_timestamp, truncate_text, get_recent_observations_summary
from core.types import (
    StateManagerProtocol, PersistenceManagerProtocol, CacheManagerProtocol,
    ObservationRecord, ExecutionContext, ExecutionResult,
)
from core.di_setup import setup_dependency_injection
from core.config_hotreload import HotReloadableConfig, ConfigWatcher, ConfigObserver
from core.prompt import SYSTEM_PROMPT, REACT_THINK_PROMPT, PLANNING_PROMPT
from core.output_validator import validate_with_retry

__all__ = [
    "AgentPlan", "PlanStep", "TaskSpec", "RoutingDecision", "TaskType",
    "Manifest", "PipelineStage", "TemplateSpecContent",
    "ILLMClient", "IContextLoader", "ISpecGenerator", "IRouter",
    "IManifestManager", "IPersistenceManager", "IToolRegistry",
    "IConfigManager", "ICacheManager",
    "NanoAgentError", "LLMError", "LLMRateLimitError", "LLMTimeoutError",
    "LLMValidationError", "ToolError", "ToolNotFoundError", "ToolSecurityError",
    "PhaseError", "PhaseTimeoutError", "ConfigError", "ConfigNotFoundError",
    "ConfigValidationError", "StateError", "InvalidStateTransitionError",
    "SpecError", "SpecGenerationError", "SpecValidationError",
    "PersistenceError", "FileAccessError",
    "StateMachine", "AgentState", "RuleEngine",
    "NanoLLMClient", "ConfigManager", "get_config_manager", "CacheManager",
    "ToolRegistry", "get_tool_registry", "DIContainer", "get_container", "reset_container",
    "AgentExecutor",
    "get_timestamp", "truncate_text", "get_recent_observations_summary",
    "StateManagerProtocol", "PersistenceManagerProtocol", "CacheManagerProtocol",
    "ObservationRecord", "ExecutionContext", "ExecutionResult",
    "setup_dependency_injection", "HotReloadableConfig", "ConfigWatcher", "ConfigObserver",
    "SYSTEM_PROMPT", "REACT_THINK_PROMPT", "PLANNING_PROMPT", "validate_with_retry",
]
