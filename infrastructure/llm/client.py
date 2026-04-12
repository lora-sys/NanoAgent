from dotenv import load_dotenv
from typing import Optional, List, Dict, Any, Generator, Type, TypeVar, Union
from pydantic import BaseModel
import json
import litellm
from loguru import logger
from infrastructure.config.manager import get_config_manager
from domain.interfaces.interfaces import ILLMClient

load_dotenv()

# 启用自动删除不支持的参数（如 gpt-5 不支持的 temperature）
litellm.drop_params = True

T = TypeVar("T", bound=BaseModel)


class NanoLLMClient(ILLMClient):
    """轻量级 LLM 客户端，支持结构化输出、流式调用、工具调用

    支持 OpenAI Responses API 和 Chat Completions API
    自动从环境变量读取 API 配置
    支持从 TOML 配置文件读取参数
    """

    def __init__(
        self, model: str = None, temperature: float = None, max_tokens: int = None
    ):
        # 从配置文件读取参数
        config = get_config_manager()
        llm_config = config.get_module_config("llm")

        # 优先使用传入参数，其次使用配置文件，最后使用默认值
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

        # 读取重试配置
        retry_config = llm_config.get("retry", {})
        self.max_attempts = retry_config.get("max_attempts", 3)
        self.backoff_factor = retry_config.get("backoff_factor", 2.0)
        self.initial_delay = retry_config.get("initial_delay", 1.0)

        # 读取日志配置
        logging_config = llm_config.get("logging", {})
        self.enable_trace = logging_config.get("enable_trace", True)
        self.log_requests = logging_config.get("log_requests", True)
        self.log_responses = logging_config.get("log_responses", False)
        self.log_latency = logging_config.get("log_latency", True)

        logger.info(
            f"Initialized LLM client with model: {model}, temperature: {temperature}, max_tokens: {max_tokens}"
        )

    def _is_gpt5_model(self) -> bool:
        """检查是否是 gpt-5 模型"""
        return "gpt-5" in self.model.lower()

    def _get_temperature(
        self, override_temp: Optional[float] = None
    ) -> Optional[float]:
        """获取适合当前模型的温度参数"""
        if self._is_gpt5_model():
            # gpt-5 只支持 temperature=1
            return 1.0
        return override_temp or self.temperature

    def _extract_text_from_responses_api(self, response: Any) -> str:
        """从 Responses API 格式中提取文本内容"""
        try:
            # Responses API 格式: response.output[0].content[0].text
            if hasattr(response, "output") and response.output:
                for output_item in response.output:
                    if hasattr(output_item, "content") and output_item.content:
                        for content_item in output_item.content:
                            if hasattr(content_item, "text"):
                                return content_item.text
            return ""
        except Exception as e:
            logger.error(f"Error extracting text from responses API: {e}")
            return ""

    def _extract_usage_from_responses_api(self, response: Any) -> Dict[str, int]:
        """从 Responses API 响应中提取使用统计信息"""
        try:
            if hasattr(response, "usage"):
                return {
                    "input_tokens": getattr(response.usage, "input_tokens", 0),
                    "output_tokens": getattr(response.usage, "output_tokens", 0),
                    "total_tokens": getattr(response.usage, "total_tokens", 0),
                }
            return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        except Exception as e:
            logger.debug(f"Could not extract usage info: {e}")
            return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    def _messages_to_input_array(
        self, messages: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """将 messages 格式转换为 Responses API 的 input 数组格式"""
        input_array = []
        for msg in messages:
            if msg["role"] == "system":
                input_array.append({"type": "system", "content": msg["content"]})
            elif msg["role"] == "user":
                input_array.append({"type": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                input_array.append({"type": "assistant", "content": msg["content"]})
        return input_array

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        return_usage: bool = False,
    ) -> Union[str, Dict[str, Any]]:
        """基础聊天调用（非流式）

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大输出 token 数
            return_usage: 是否返回使用统计信息

        Returns:
            如果 return_usage=False，返回文本内容
            如果 return_usage=True，返回 {"content": str, "usage": dict}
        """
        try:
            # 使用 Chat Completions API
            response = litellm.completion(
                model=self.model,
                messages=messages,
                temperature=self._get_temperature(temperature),
                max_tokens=max_tokens or self.max_tokens,
            )

            content = response.choices[0].message.content or ""
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

            logger.info(
                f"Chat completed - Input: {usage['input_tokens']}, "
                f"Output: {usage['output_tokens']}, Total: {usage['total_tokens']}"
            )

            if return_usage:
                return {"content": content, "usage": usage}
            return content

        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            raise

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_responses_api: bool = False,
    ) -> Generator[Dict[str, Any], None, None]:
        """流式聊天调用

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大输出 token 数
            use_responses_api: 是否使用 Responses API（默认 False）

        Yields:
            流式事件，格式为 {"type": "delta"|"done"|"error", "content": str, "usage": dict}
        """
        try:
            actual_temp = self._get_temperature(temperature)

            if use_responses_api:
                # 使用 Responses API 流式
                input_array = self._messages_to_input_array(messages)
                response = litellm.responses(
                    model=self.model,
                    input=input_array,
                    temperature=actual_temp,
                    max_output_tokens=max_tokens or self.max_tokens,
                    stream=True,
                )

                for event in response:
                    if hasattr(event, "type"):
                        if event.type == "response.output_text.delta":
                            if hasattr(event, "delta"):
                                yield {"type": "delta", "content": event.delta}
                        elif event.type == "response.done":
                            usage = self._extract_usage_from_responses_api(event)
                            yield {"type": "done", "content": "", "usage": usage}
                            break
            else:
                # 使用 Chat Completions API 流式
                response = litellm.completion(
                    model=self.model,
                    messages=messages,
                    temperature=actual_temp,
                    max_tokens=max_tokens or self.max_tokens,
                    stream=True,
                )

                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield {
                            "type": "delta",
                            "content": chunk.choices[0].delta.content,
                        }

                yield {"type": "done", "content": "", "usage": {"total_tokens": 0}}

        except Exception as e:
            logger.error(f"LLM stream error: {e}")
            yield {"type": "error", "content": str(e)}

    def structured_chat(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        temperature: Optional[float] = None,
    ) -> T:
        """结构化输出（返回 Pydantic 模型）

        Args:
            messages: 消息列表
            response_model: 目标 Pydantic 模型类型
            temperature: 温度参数

        Returns:
            解析后的 Pydantic 模型实例
        """
        try:
            # 使用 Chat Completions API
            response = litellm.completion(
                model=self.model,
                messages=messages,
                temperature=self._get_temperature(temperature),
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content or ""
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

            logger.debug(f"Structured response: {content[:200]}...")
            logger.info(
                f"Structured chat completed - Total tokens: {usage['total_tokens']}"
            )

            # 解析 JSON
            data = json.loads(content)

            # 处理嵌套的 JSON 结构（例如 {"TaskSpec": {...}}）
            if isinstance(data, dict):
                keys = list(data.keys())
                if len(keys) == 1 and isinstance(data[keys[0]], dict):
                    model_name = response_model.__name__
                    if keys[0] == model_name or model_name.lower() in keys[0].lower():
                        logger.info(
                            f"Detected nested JSON structure, extracting data from '{keys[0]}' key"
                        )
                        data = data[keys[0]]

            # 自动类型转换容错
            if isinstance(data, dict):
                # 处理 boundaries 字段：如果有非标准键名，尝试映射
                if "boundaries" in data and isinstance(data["boundaries"], dict):
                    boundaries = data["boundaries"]
                    # 检查是否有非标准键名，尝试映射到 always/ask_first/never
                    standard_keys = {"always", "ask_first", "never"}
                    if not standard_keys.issubset(boundaries.keys()):
                        # 如果没有标准键，但只有一个键，可能是嵌套结构
                        if len(boundaries) == 1 and isinstance(
                            list(boundaries.values())[0], dict
                        ):
                            nested_boundaries = list(boundaries.values())[0]
                            if standard_keys.issubset(nested_boundaries.keys()):
                                logger.info("Auto-fixing nested boundaries structure")
                                data["boundaries"] = nested_boundaries

                # 处理 progress_tracking 字段：如果是 list，转换为 dict
                if "progress_tracking" in data and isinstance(
                    data["progress_tracking"], list
                ):
                    logger.info("Auto-fixing progress_tracking from list to dict")
                    data["progress_tracking"] = {
                        "current_progress": "进行中",
                        "completed_steps": [],
                        "remaining": data["progress_tracking"],
                    }

            # 转换为 Pydantic 模型
            return response_model.model_validate(data)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {e}")
            logger.error(f"Response content: {content}")
            raise ValueError(f"Invalid JSON response: {e}")
        except Exception as e:
            logger.error(f"Structured chat error: {e}")
            raise

    def structured_chat_with_validation(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        temperature: Optional[float] = None,
        max_retries: int = 3,
    ) -> T:
        """
        带多层防御验证的结构化输出

        使用多层防御策略：
        Layer 1: Prompt Engineering（基础层）
        Layer 2: JSON Mode（增强层，如果支持）
        Layer 3: 验证 + 修复（保证层）
        Layer 4: 重试机制（最终保证）

        Args:
            messages: 消息列表
            response_model: 目标 Pydantic 模型类型
            temperature: 温度参数
            max_retries: 最大重试次数

        Returns:
            验证后的 Pydantic 模型实例

        Raises:
            ValueError: 如果重试后仍然失败
        """
        from .output_validator import validate_with_retry

        for attempt in range(max_retries):
            try:
                # 使用 Chat Completions API
                response = litellm.completion(
                    model=self.model,
                    messages=messages,
                    temperature=self._get_temperature(temperature),
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"},
                )

                content = response.choices[0].message.content or ""
                usage = {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

                logger.debug(f"Structured response: {content[:200]}...")
                logger.info(
                    f"Structured chat completed - Total tokens: {usage['total_tokens']}"
                )

                # 使用多层防御验证输出
                return validate_with_retry(content, response_model, max_retries=1)

            except Exception as e:
                logger.warning(f"尝试 {attempt + 1}/{max_retries} 失败: {e}")

                if attempt == max_retries - 1:
                    logger.error(f"所有尝试都失败: {e}")
                    raise ValueError(f"无法获取有效的结构化输出: {e}")

        # 理论上不会到达这里
        raise ValueError("无法获取有效的结构化输出")

    def tool_chat(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        tool_choice: str = "auto",
    ) -> Dict[str, Any]:
        """工具调用支持

        注意：工具调用使用 Chat Completions API

        Args:
            messages: 消息列表
            tools: 工具定义列表
            temperature: 温度参数
            tool_choice: 工具选择策略

        Returns:
            {"content": str, "tool_calls": list, "usage": dict}
        """
        try:
            actual_temp = self._get_temperature(temperature)

            response = litellm.completion(
                model=self.model,
                messages=messages,
                temperature=actual_temp,
                max_tokens=self.max_tokens,
                tools=tools,
                tool_choice=tool_choice,
            )

            message = response.choices[0].message
            result = {
                "content": message.content or "",
                "tool_calls": [],
                "usage": {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
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

            logger.info(
                f"Tool chat completed - Tool calls: {len(result['tool_calls'])}"
            )
            return result

        except Exception as e:
            logger.error(f"Tool chat error: {e}")
            raise

    def generate_with_context(
        self,
        system_prompt: str,
        user_prompt: str,
        context: str = "",
        temperature: Optional[float] = None,
    ) -> str:
        """带上下文的生成助手方法

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            context: 额外上下文
            temperature: 温度参数

        Returns:
            生成的文本内容
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"{context}\n\n{user_prompt}" if context else user_prompt,
            },
        ]
        return self.chat(messages, temperature)

    def simple_response(
        self,
        input_text: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """简单的单轮对话

        Args:
            input_text: 输入文本
            temperature: 温度参数
            max_tokens: 最大输出 token 数

        Returns:
            生成的文本内容
        """
        try:
            # 使用 Chat Completions API
            messages = [{"role": "user", "content": input_text}]
            response = litellm.completion(
                model=self.model,
                messages=messages,
                temperature=self._get_temperature(temperature),
                max_tokens=max_tokens or self.max_tokens,
            )

            content = response.choices[0].message.content or ""
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

            logger.info(
                f"Simple response completed - Total tokens: {usage['total_tokens']}"
            )
            return content

        except Exception as e:
            logger.error(f"Simple response error: {e}")
            raise
