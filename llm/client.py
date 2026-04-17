"""LLM 客户端 - 基于 litellm"""

import asyncio
import json
import os
import random
import re
import time
from typing import Dict, List, Optional, Type, TypeVar

import litellm
from dotenv import load_dotenv

from config import get_config

try:
    from core.observability import get_tracer, calculate_cost
    _HAS_OBSERVABILITY = True
except ImportError:
    _HAS_OBSERVABILITY = False

load_dotenv()
litellm.drop_params = True
litellm.telemetry = False

T = TypeVar("T")

# 防止无限循环的配置
litellm.REPEATED_STREAMING_CHUNK_LIMIT = 100


class NanoLLMClient:
    def __init__(self, model: Optional[str] = None):
        cfg = get_config()
        llm_cfg = cfg.get("llm", {})
        self.model = model or llm_cfg.get("model", "openai/gpt-4o")
        self.temperature = llm_cfg.get("temperature", 0.7)
        self.max_tokens = llm_cfg.get("max_tokens", 4096)

        retry_cfg = llm_cfg.get("retry", {})
        self.max_attempts = retry_cfg.get("max_attempts", 3)

        mock_cfg = llm_cfg.get("mock", {})
        self.mock_enabled = mock_cfg.get("enabled", True)
        self.mock_mode = mock_cfg.get("mode", "random")
        self.mock_file = mock_cfg.get(
            "responses_file", "tests/fixtures/llm_mock_simple.json"
        )
        self._mock_idx = 0

    def _get_mock(self) -> str:
        if not os.path.exists(self.mock_file):
            return '{"action": "complete", "reason": "Mock file missing"}'

        with open(self.mock_file, "r", encoding="utf-8") as f:
            responses = json.load(f)

        resp = (
            random.choice(responses)
            if self.mock_mode == "random"
            else responses[self._mock_idx % len(responses)]
        )

        if self.mock_mode != "random":
            self._mock_idx += 1

        # 直接返回字符串，不要再次序列化
        return resp if isinstance(resp, str) else json.dumps(resp, ensure_ascii=False)

    def chat(
        self, messages: List[Dict[str, str]], temperature: Optional[float] = None
    ) -> str:
        if self.mock_enabled:
            return self._get_mock()

        start_time = time.time()
        resp = litellm.completion(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=self.max_tokens,
        )
        duration_ms = int((time.time() - start_time) * 1000)

        # 记录 LLM 调用
        if _HAS_OBSERVABILITY and resp.usage is not None:
            tracer = get_tracer()
            usage = resp.usage
            input_tokens = usage.prompt_tokens if hasattr(usage, 'prompt_tokens') else 0
            output_tokens = usage.completion_tokens if hasattr(usage, 'completion_tokens') else 0
            cost = calculate_cost(self.model, input_tokens, output_tokens)
            tracer.record_llm(
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=duration_ms,
                input_messages=messages,
                output_message=resp.choices[0].message.content or "",
                cost=cost,
            )

        return resp.choices[0].message.content or ""

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        callback=None,
    ) -> str:
        """流式聊天，支持实时输出

        Args:
            messages: 消息列表
            temperature: 温度参数
            callback: 回调函数，接收每个 token

        Returns:
            完整的响应内容
        """
        if self.mock_enabled:
            content = self._get_mock()
            if callback:
                # 模拟流式输出
                for char in content:
                    callback(char)
            return content

        full_content = ""
        chunks = []
        response = litellm.completion(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )

        try:
            for chunk in response:
                chunks.append(chunk)
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    if callback:
                        callback(content)
        except litellm.InternalServerError as e:
            # 处理无限循环错误
            if "repeated chunk" in str(e).lower():
                print("⚠️ 检测到模型进入无限循环，使用已接收的 chunks 重建响应")
                # 使用 stream_chunk_builder 重建响应
                return self.stream_chunk_builder(chunks, messages)
            raise

        return full_content

    def stream_chunk_builder(self, chunks: List, messages: List[Dict[str, str]]) -> str:
        """从 chunks 列表重建完整的流式响应

        Args:
            chunks: 流式传输的 chunk 列表
            messages: 原始消息列表

        Returns:
            完整的响应内容
        """
        return "".join(
            chunk.choices[0].delta.content
            for chunk in chunks
            if chunk.choices and chunk.choices[0].delta.content
        )

    async def achat(
        self, messages: List[Dict[str, str]], temperature: Optional[float] = None
    ) -> str:
        """异步聊天

        Args:
            messages: 消息列表
            temperature: 温度参数

        Returns:
            完整的响应内容
        """
        if self.mock_enabled:
            return self._get_mock()

        start_time = time.time()
        resp = await litellm.acompletion(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=self.max_tokens,
        )
        duration_ms = int((time.time() - start_time) * 1000)

        # 记录 LLM 调用
        if _HAS_OBSERVABILITY and resp.usage is not None:
            tracer = get_tracer()
            usage = resp.usage
            input_tokens = usage.prompt_tokens if hasattr(usage, 'prompt_tokens') else 0
            output_tokens = usage.completion_tokens if hasattr(usage, 'completion_tokens') else 0
            cost = calculate_cost(self.model, input_tokens, output_tokens)
            tracer.record_llm(
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=duration_ms,
                input_messages=messages,
                output_message=resp.choices[0].message.content or "",
                cost=cost,
            )

        return resp.choices[0].message.content or ""

    async def astream_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        callback=None,
    ) -> str:
        """异步流式聊天

        Args:
            messages: 消息列表
            temperature: 温度参数
            callback: 回调函数，接收每个 token

        Returns:
            完整的响应内容
        """
        if self.mock_enabled:
            content = self._get_mock()
            if callback:
                # 模拟流式输出
                for char in content:
                    callback(char)
                    await asyncio.sleep(0.01)  # 模拟异步
            return content

        full_content = ""
        chunks = []
        response = await litellm.acompletion(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )

        try:
            async for chunk in response:
                chunks.append(chunk)
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    if callback:
                        callback(content)
        except litellm.InternalServerError as e:
            # 处理无限循环错误
            if "repeated chunk" in str(e).lower():
                print("⚠️ 检测到模型进入无限循环，使用已接收的 chunks 重建响应")
                # 使用 stream_chunk_builder 重建响应
                return self.stream_chunk_builder(chunks, messages)
            raise

        return full_content

    def structured_chat(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        temperature: Optional[float] = None,
    ) -> T:
        if self.mock_enabled:
            try:
                return response_model.model_validate(json.loads(self._get_mock()))
            except Exception:
                return response_model()
        raw = litellm.completion(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"},
        )
        content = raw.choices[0].message.content or ""
        data = _extract_json(content)
        if isinstance(data, dict) and len(data) == 1:
            key = list(data.keys())[0]
            model_name = response_model.__name__
            if key == model_name or model_name.lower() in key.lower():
                data = data[key]
        return response_model.model_validate(data)

    async def astructured_chat(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        temperature: Optional[float] = None,
    ) -> T:
        """异步结构化聊天

        Args:
            messages: 消息列表
            response_model: 响应模型类型
            temperature: 温度参数

        Returns:
            结构化的响应对象
        """
        if self.mock_enabled:
            try:
                return response_model.model_validate(json.loads(self._get_mock()))
            except Exception:
                return response_model()

        raw = await litellm.acompletion(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"},
        )
        content = raw.choices[0].message.content or ""
        data = _extract_json(content)
        if isinstance(data, dict) and len(data) == 1:
            key = list(data.keys())[0]
            model_name = response_model.__name__
            if key == model_name or model_name.lower() in key.lower():
                data = data[key]
        return response_model.model_validate(data)


def _extract_json(text: str) -> dict:
    # 提取 markdown 代码块中的 JSON
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()

    # 查找 JSON 对象的起始和结束位置
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return json.loads(text[start : end + 1])

    return json.loads(text)
