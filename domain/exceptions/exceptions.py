"""NanoAgent 异常体系"""


class NanoAgentError(Exception):
    """基础异常"""
    def __init__(self, message="", details=None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class LLMError(NanoAgentError): pass
class LLMRateLimitError(LLMError): pass
class LLMTimeoutError(LLMError): pass
class LLMValidationError(LLMError): pass

class ToolError(NanoAgentError):
    def __init__(self, tool_name="", message=""):
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' failed: {message}")

class ToolNotFoundError(ToolError): pass
class ToolSecurityError(ToolError): pass

class PhaseError(NanoAgentError): pass
class PhaseTimeoutError(PhaseError): pass

class ConfigError(NanoAgentError): pass
class ConfigNotFoundError(ConfigError): pass
class ConfigValidationError(ConfigError): pass

class StateError(NanoAgentError): pass
class InvalidStateTransitionError(StateError): pass

class SpecError(NanoAgentError): pass
class SpecGenerationError(SpecError): pass
class SpecValidationError(SpecError): pass

class PersistenceError(NanoAgentError): pass
class FileAccessError(PersistenceError): pass
