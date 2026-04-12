"""
NanoAgent 异常定义

统一的异常层次结构，确保错误处理一致性
"""


class NanoAgentError(Exception):
    """NanoAgent 基础异常类"""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# ============ LLM 相关异常 ============

class LLMError(NanoAgentError):
    """LLM 调用失败"""
    
    def __init__(self, message: str, response: str = None, model: str = None):
        self.response = response
        self.model = model
        super().__init__(message, {"response": response, "model": model})


class LLMRateLimitError(LLMError):
    """LLM 速率限制"""
    pass


class LLMTimeoutError(LLMError):
    """LLM 超时"""
    pass


class LLMValidationError(LLMError):
    """LLM 输出验证失败"""
    
    def __init__(self, message: str, response: str = None, schema: str = None):
        self.schema = schema
        super().__init__(message, {"response": response, "schema": schema})


# ============ 工具相关异常 ============

class ToolError(NanoAgentError):
    """工具执行失败"""
    
    def __init__(self, tool_name: str, message: str, arguments: dict = None):
        self.tool_name = tool_name
        self.arguments = arguments or {}
        super().__init__(
            f"Tool '{tool_name}' failed: {message}",
            {"tool_name": tool_name, "arguments": arguments}
        )


class ToolNotFoundError(ToolError):
    """工具未找到"""
    
    def __init__(self, tool_name: str):
        super().__init__(tool_name, "Tool not found")


class ToolSecurityError(ToolError):
    """工具安全策略阻止"""
    
    def __init__(self, tool_name: str, reason: str):
        super().__init__(tool_name, f"Security policy blocked: {reason}")


# ============ 阶段相关异常 ============

class PhaseError(NanoAgentError):
    """阶段执行失败"""
    
    def __init__(self, phase_name: str, message: str, context: dict = None):
        self.phase_name = phase_name
        super().__init__(
            f"Phase '{phase_name}' failed: {message}",
            {"phase": phase_name, **context} if context else {"phase": phase_name}
        )


class PhaseTimeoutError(PhaseError):
    """阶段执行超时"""
    pass


# ============ 配置相关异常 ============

class ConfigError(NanoAgentError):
    """配置错误"""
    
    def __init__(self, key: str, message: str):
        self.key = key
        super().__init__(
            f"Config error for '{key}': {message}",
            {"config_key": key}
        )


class ConfigNotFoundError(ConfigError):
    """配置项未找到"""
    pass


class ConfigValidationError(ConfigError):
    """配置验证失败"""
    pass


# ============ 状态机相关异常 ============

class StateError(NanoAgentError):
    """状态机错误"""
    
    def __init__(self, message: str, current_state: str = None, target_state: str = None):
        self.current_state = current_state
        self.target_state = target_state
        super().__init__(
            message,
            {"current_state": current_state, "target_state": target_state}
        )


class InvalidStateTransitionError(StateError):
    """无效状态转换"""
    pass


# ============ Spec 相关异常 ============

class SpecError(NanoAgentError):
    """Spec 相关错误"""
    
    def __init__(self, message: str, spec_type: str = None):
        self.spec_type = spec_type
        super().__init__(message, {"spec_type": spec_type})


class SpecGenerationError(SpecError):
    """Spec 生成失败"""
    pass


class SpecValidationError(SpecError):
    """Spec 验证失败"""
    pass


# ============ 持久化相关异常 ============

class PersistenceError(NanoAgentError):
    """持久化失败"""
    
    def __init__(self, message: str, path: str = None):
        self.path = path
        super().__init__(message, {"path": path})


class FileAccessError(PersistenceError):
    """文件访问失败"""
    pass
