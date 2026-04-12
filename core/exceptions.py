"""NanoAgent exception hierarchy."""


class NanoAgentError(Exception):
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class LLMError(NanoAgentError):
    def __init__(self, message: str, response: str = None, model: str = None):
        self.response = response
        self.model = model
        super().__init__(message, {"response": response, "model": model})


class LLMRateLimitError(LLMError): ...


class LLMTimeoutError(LLMError): ...


class LLMValidationError(LLMError):
    def __init__(self, message: str, response: str = None, schema: str = None):
        self.schema = schema
        super().__init__(message, {"response": response, "schema": schema})


class ToolError(NanoAgentError):
    def __init__(self, tool_name: str, message: str, arguments: dict = None):
        self.tool_name = tool_name
        self.arguments = arguments or {}
        super().__init__(
            f"Tool '{tool_name}' failed: {message}",
            {"tool_name": tool_name, "arguments": arguments},
        )


class ToolNotFoundError(ToolError):
    def __init__(self, tool_name: str):
        super().__init__(tool_name, "Tool not found")


class ToolSecurityError(ToolError):
    def __init__(self, tool_name: str, reason: str):
        super().__init__(tool_name, f"Security policy blocked: {reason}")


class PhaseError(NanoAgentError):
    def __init__(self, phase_name: str, message: str, context: dict = None):
        self.phase_name = phase_name
        super().__init__(
            f"Phase '{phase_name}' failed: {message}",
            {"phase": phase_name, **(context or {})},
        )


class PhaseTimeoutError(PhaseError): ...


class ConfigError(NanoAgentError):
    def __init__(self, key: str, message: str):
        self.key = key
        super().__init__(f"Config error for '{key}': {message}", {"config_key": key})


class ConfigNotFoundError(ConfigError): ...


class ConfigValidationError(ConfigError): ...


class StateError(NanoAgentError):
    def __init__(
        self, message: str, current_state: str = None, target_state: str = None
    ):
        self.current_state = current_state
        self.target_state = target_state
        super().__init__(
            message, {"current_state": current_state, "target_state": target_state}
        )


class InvalidStateTransitionError(StateError): ...


class SpecError(NanoAgentError):
    def __init__(self, message: str, spec_type: str = None):
        self.spec_type = spec_type
        super().__init__(message, {"spec_type": spec_type})


class SpecGenerationError(SpecError): ...


class SpecValidationError(SpecError): ...


class PersistenceError(NanoAgentError):
    def __init__(self, message: str, path: str = None):
        self.path = path
        super().__init__(message, {"path": path})


class FileAccessError(PersistenceError): ...
