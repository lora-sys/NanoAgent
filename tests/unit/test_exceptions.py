"""
异常层次单元测试
"""

from core.exceptions import (
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


class TestExceptionHierarchy:
    """测试异常层次结构"""

    def test_base_exception(self):
        """测试基础异常类"""
        error = NanoAgentError("Test error", {"key": "value"})
        assert error.message == "Test error"
        assert error.details == {"key": "value"}
        assert str(error) == "Test error"

    def test_llm_exception_inheritance(self):
        """测试 LLM 异常继承"""
        assert issubclass(LLMError, NanoAgentError)
        assert issubclass(LLMRateLimitError, LLMError)
        assert issubclass(LLMTimeoutError, LLMError)
        assert issubclass(LLMValidationError, LLMError)

    def test_llm_error_with_details(self):
        """测试 LLMError 详细信息"""
        error = LLMError("Chat failed", response="Bad output", model="gpt-4")
        assert error.response == "Bad output"
        assert error.model == "gpt-4"
        assert "Chat failed" in str(error)

    def test_tool_exception_inheritance(self):
        """测试工具异常继承"""
        assert issubclass(ToolError, NanoAgentError)
        assert issubclass(ToolNotFoundError, ToolError)
        assert issubclass(ToolSecurityError, ToolError)

    def test_tool_error_with_details(self):
        """测试 ToolError 详细信息"""
        error = ToolError(
            "write_file", "Permission denied", {"filepath": "/etc/passwd"}
        )
        assert error.tool_name == "write_file"
        assert error.arguments == {"filepath": "/etc/passwd"}
        assert "write_file" in str(error)

    def test_tool_not_found_error(self):
        """测试 ToolNotFoundError"""
        error = ToolNotFoundError("unknown_tool")
        assert error.tool_name == "unknown_tool"
        assert "not found" in str(error).lower()

    def test_tool_security_error(self):
        """测试 ToolSecurityError"""
        error = ToolSecurityError("shell_exec", "Shell commands blocked")
        assert "security policy" in str(error).lower()

    def test_phase_exception_inheritance(self):
        """测试阶段异常继承"""
        assert issubclass(PhaseError, NanoAgentError)
        assert issubclass(PhaseTimeoutError, PhaseError)

    def test_phase_error(self):
        """测试 PhaseError"""
        error = PhaseError("thinking", "LLM timeout", {"step": 5})
        assert error.phase_name == "thinking"
        assert "thinking" in str(error)

    def test_config_exception_inheritance(self):
        """测试配置异常继承"""
        assert issubclass(ConfigError, NanoAgentError)
        assert issubclass(ConfigNotFoundError, ConfigError)
        assert issubclass(ConfigValidationError, ConfigError)

    def test_config_error(self):
        """测试 ConfigError"""
        error = ConfigError("llm.api_key", "Missing required key")
        assert error.key == "llm.api_key"
        assert "llm.api_key" in str(error)

    def test_state_exception_inheritance(self):
        """测试状态机异常继承"""
        assert issubclass(StateError, NanoAgentError)
        assert issubclass(InvalidStateTransitionError, StateError)

    def test_invalid_state_transition(self):
        """测试无效状态转换异常"""
        error = InvalidStateTransitionError(
            "Cannot transition from completed to planning",
            current_state="completed",
            target_state="planning",
        )
        assert error.current_state == "completed"
        assert error.target_state == "planning"

    def test_spec_exception_inheritance(self):
        """测试 Spec 异常继承"""
        assert issubclass(SpecError, NanoAgentError)
        assert issubclass(SpecGenerationError, SpecError)
        assert issubclass(SpecValidationError, SpecError)

    def test_persistence_exception_inheritance(self):
        """测试持久化异常继承"""
        assert issubclass(PersistenceError, NanoAgentError)
        assert issubclass(FileAccessError, PersistenceError)
