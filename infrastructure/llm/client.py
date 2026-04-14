"""
NanoLLMClient - 轻量级 LLM 客户端

支持结构化输出、工具调用、Mock 模式
"""

from typing import Optional, List, Dict, Any, Type, TypeVar
from pydantic import BaseModel
import json
import os
import litellm
from dotenv import load_dotenv
from loguru import logger
from infrastructure.config.manager import get_config_manager

load_dotenv()

litellm.drop_params = True
litellm.telemetry = False

T = TypeVar("T", bound=BaseModel)


class NanoLLMClient:
    """轻量级 LLM 客户端"""

    def __init__(
        self, model: str = None, temperature: float = None, max_tokens: int = None
    ):
        config = get_config_manager()
        llm_config = config.get_module_config("llm")

        if model is None:
            provider_config = llm_config.get("provider", {})
            clients_config = llm_config.get("clients", {})
            provider_name = provider_config.get("name", "openai")
            client_config = clients_config.get(provider_name, {})
            model = client_config.get("model", "groq/llama-3.3-70b")

        if temperature is None:
            clients_config = llm_config.get("clients", {})
            provider_name = model.split("/")[0] if "/" in model else "openai"
            client_config = clients_config.get(provider_name, {})
            temperature = client_config.get("temperature", 0.7)

        if max_tokens is None:
            clients_config = llm_config.get("clients", {})
            provider_name = model.split("/")[0] if "/" in model else "openai"
            client_config = clients_config.get(provider_name, {})
            max_tokens = client_config.get("max_tokens", 4096)

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 重试配置
        retry_config = llm_config.get("retry", {})
        self.max_attempts = retry_config.get("max_attempts", 3)
        self.backoff_factor = retry_config.get("backoff_factor", 2.0)
        self.initial_delay = retry_config.get("initial_delay", 1.0)

        # Mock 配置
        mock_config = llm_config.get("mock", {})
        self.mock_enabled = mock_config.get("enabled", False)
        self.mock_mode = mock_config.get("mode", "random")
        self.mock_responses_file = mock_config.get("responses_file", "tests/fixtures/llm_mock_responses.json")
        self._mock_index = 0

        if self.mock_enabled:
            logger.warning(f"⚠️ LLM Mock Mode Enabled: {self.mock_mode}")

        logger.info(f"LLM client initialized: {model}")

    def _get_mock_response(self) -> str:
        """获取 Mock 响应"""
        import os
        import random

        file_path = self.mock_responses_file
        if not os.path.exists(file_path):
            logger.error(f"Mock responses file not found: {file_path}")
            return '{"action": "complete", "reason": "Mock file missing"}'

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                responses = json.load(f)

            if self.mock_mode == "random":
                response = random.choice(responses)
            else:
                response = responses[self._mock_index % len(responses)]
                self._mock_index += 1

            logger.info(f"🎭 Mock Response: {response.get('action', 'unknown')}")
            return json.dumps(response, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error reading mock responses: {e}")
            return '{"action": "complete", "reason": "Mock error"}'

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """基础聊天调用"""
        if self.mock_enabled:
            return self._get_mock_response()

        response = litellm.completion(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
        )

        content = response.choices[0].message.content or ""
        logger.info(f"Chat completed: {len(content)} chars")
        return content

    def structured_chat(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        temperature: Optional[float] = None,
    ) -> T:
        """结构化输出（返回 Pydantic 模型）"""
        if self.mock_enabled:
            mock_str = self._get_mock_response()
            try:
                data = json.loads(mock_str)
                return response_model.model_validate(data)
            except Exception as e:
                logger.warning(f"Mock validation failed: {e}")
                return response_model()

        response = litellm.completion(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or ""

        # 解析 JSON
        data = json.loads(content)

        # 解包嵌套结构 (如 {"TaskSpec": {...}})
        if isinstance(data, dict):
            keys = list(data.keys())
            if len(keys) == 1 and isinstance(data[keys[0]], dict):
                model_name = response_model.__name__
                if keys[0] == model_name or model_name.lower() in keys[0].lower():
                    logger.info(f"Unwrapping nested JSON: {keys[0]}")
                    data = data[keys[0]]

        return response_model.model_validate(data)

    def tool_chat(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        tool_choice: str = "auto",
    ) -> Dict[str, Any]:
        """工具调用支持"""
        if self.mock_enabled:
            mock_str = self._get_mock_response()
            try:
                data = json.loads(mock_str)
                if data.get("action") == "tool_call":
                    return {
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "mock_call_123",
                                "type": "function",
                                "function": {
                                    "name": data.get("tool", "unknown"),
                                    "arguments": json.dumps(data.get("arguments", {})),
                                },
                            }
                        ],
                        "usage": {},
                    }
                return {"content": mock_str, "tool_calls": [], "usage": {}}
            except Exception:
                return {"content": mock_str, "tool_calls": [], "usage": {}}

        response = litellm.completion(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=self.max_tokens,
            tools=tools,
            tool_choice=tool_choice,
        )

        message = response.choices[0].message
        result = {
            "content": message.content or "",
            "tool_calls": [],
            "usage": {},
        }

        if hasattr(message, "tool_calls") and message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ]

        return result
