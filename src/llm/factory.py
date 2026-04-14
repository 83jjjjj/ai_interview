"""LLM 客户端工厂。

根据配置创建对应的 LLM 客户端实例。
新增 LLM 适配器时，只需在这里加一个 elif 分支。
"""

from src.llm.base import LLMClientBase
from src.llm.qwen import QwenClient

# 全局单例，避免重复创建连接
_llm_client: LLMClientBase = None


def get_llm_client() -> LLMClientBase:
    """获取 LLM 客户端单例。

    Returns:
        LLMClientBase 的具体实现实例
    """
    global _llm_client
    if _llm_client is None:
        # 目前只支持通义千问，后续可按配置切换
        _llm_client = QwenClient()
    return _llm_client
