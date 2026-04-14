"""通义千问适配器（OpenAI 兼容格式）。

通义千问 API 兼容 OpenAI 的接口格式，所以直接用 openai 库调用即可。
如果换其他兼容 OpenAI 格式的模型（如 DeepSeek、Moonshot），只需改配置，不用改代码。
"""

from typing import Dict, Generator, List

from openai import OpenAI

from src.core.config import settings
from src.llm.base import LLMClientBase


class QwenClient(LLMClientBase):
    """通义千问 LLM 客户端。

    使用 OpenAI 兼容的 API 格式调用通义千问。
    通过 settings 配置 API key、base_url、model，方便切换模型。
    """

    def __init__(self) -> None:
        """初始化 OpenAI 客户端，连接通义千问 API。"""
        self.client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.model = settings.LLM_MODEL

    def chat(self, messages: List[Dict]) -> str:
        """普通对话，一次性返回完整响应。

        Args:
            messages: 消息列表 [{"role": "user", "content": "你好"}]

        Returns:
            LLM 返回的完整文本
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content

    def chat_stream(self, messages: List[Dict]) -> Generator[str, None, None]:
        """流式对话，逐块 yield 响应内容。

        Args:
            messages: 消息列表 [{"role": "user", "content": "你好"}]

        Yields:
            响应文本的各个片段
        """
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
