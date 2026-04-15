"""异常层次单元测试"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from exceptions import NanoAgentError, LLMError, ToolError, ConfigError


class TestExceptionHierarchy:
    """测试异常层次结构"""

    def test_base_exception(self):
        error = NanoAgentError("Test error")
        assert str(error) == "Test error"

    def test_llm_exception_inheritance(self):
        assert issubclass(LLMError, NanoAgentError)

    def test_tool_exception_inheritance(self):
        assert issubclass(ToolError, NanoAgentError)

    def test_tool_error_with_details(self):
        error = ToolError("write_file", "Permission denied")
        assert error.tool_name == "write_file"
        assert "write_file" in str(error)

    def test_config_exception_inheritance(self):
        assert issubclass(ConfigError, NanoAgentError)
