"""LLM 客户端 - 基于 litellm"""

import json
import os
import random
import re
from typing import Dict, List, Optional, Type, TypeVar

import litellm
from dotenv import load_dotenv
from pydantic import BaseModel

from config import get_config

load_dotenv()
litellm.drop_params = True
litellm.telemetry = False

T = TypeVar("T", bound=BaseModel)


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
        if self.mock_mode == "random":
            resp = random.choice(responses)
        else:
            resp = responses[self._mock_idx % len(responses)]
            self._mock_idx += 1
        # 直接返回字符串，不要再次序列化
        return resp if isinstance(resp, str) else json.dumps(resp, ensure_ascii=False)

    def chat(
        self, messages: List[Dict[str, str]], temperature: Optional[float] = None
    ) -> str:
        if self.mock_enabled:
            return self._get_mock()
        resp = litellm.completion(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=self.max_tokens,
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
        response = litellm.completion(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content += content
                if callback:
                    callback(content)

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


def _extract_json(text: str) -> dict:
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        text = m.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return json.loads(text[start : end + 1])
    return json.loads(text)
