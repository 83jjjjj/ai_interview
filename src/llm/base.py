"""LLM 客户端抽象基类。

定义统一接口，所有 LLM 适配器必须实现这些方法。
使用 ABC（Abstract Base Class）强制子类实现，不实现就报错。
"""

from abc import ABC, abstractmethod
from typing import Dict, Generator, List


class LLMClientBase(ABC):
    """LLM 客户端抽象基类。

    所有 LLM 适配器（通义千问、OpenAI 等）都必须实现这两个方法。
    """

    @abstractmethod
    def chat(self, messages: List[Dict]) -> str:
        """普通对话，返回完整响应文本。

        Args:
            messages: 消息列表，每项格式 {"role": "user/assistant/system", "content": "..."}

        Returns:
            LLM 返回的完整文本
        """

    @abstractmethod
    def chat_stream(self, messages: List[Dict]) -> Generator[str, None, None]:
        """流式对话，逐块 yield 响应内容。

        Args:
            messages: 消息列表，格式同上

        Yields:
            响应文本的各个片段（token 级别）
        """
