"""异常体系"""


class NanoAgentError(Exception):
    pass


class LLMError(NanoAgentError):
    pass


class ToolError(NanoAgentError):
    def __init__(self, tool_name: str = "", message: str = ""):
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' failed: {message}")


class ConfigError(NanoAgentError):
    pass
