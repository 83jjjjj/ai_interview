"""LLM 调用封装层。

提供统一的 LLMClient 接口，屏蔽底层 API 差异。
当前实现：通义千问（OpenAI 兼容格式）。
切换模型：只需修改 config.py 中的 LLM_BASE_URL、LLM_MODEL、LLM_API_KEY。
"""
