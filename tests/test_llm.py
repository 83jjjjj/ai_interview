"""LLM 封装层测试。

测试 LLMClient 的接口契约和抽象基类约束。
不调用真实 API（用 mock 替代），只验证接口定义正确。
"""

import pytest

from src.llm.base import LLMClientBase
from src.llm.qwen import QwenClient
from src.llm.factory import get_llm_client


class TestLLMClientBase:
    """测试抽象基类的接口约束。"""

    def test_cannot_instantiate_abstract_class(self):
        """抽象基类不能直接实例化，必须子类实现所有抽象方法。"""
        with pytest.raises(TypeError):
            LLMClientBase()

    def test_incomplete_subclass_raises_error(self):
        """只实现部分抽象方法的子类也不能实例化。"""

        class IncompleteClient(LLMClientBase):
            """只实现了 chat，没实现 chat_stream。"""

            def chat(self, messages):
                return "hello"

        with pytest.raises(TypeError):
            IncompleteClient()

    def test_complete_subclass_can_instantiate(self):
        """实现了所有抽象方法的子类可以正常实例化。"""

        class MockClient(LLMClientBase):
            """完整实现所有抽象方法的 mock 客户端。"""

            def chat(self, messages):
                return "mock response"

            def chat_stream(self, messages):
                yield "mock "
                yield "response"

        client = MockClient()
        assert client.chat([{"role": "user", "content": "hi"}]) == "mock response"
        chunks = list(client.chat_stream([{"role": "user", "content": "hi"}]))
        assert chunks == ["mock ", "response"]


class TestQwenClient:
    """测试通义千问适配器。"""

    def test_implements_base_interface(self):
        """QwenClient 必须继承 LLMClientBase。"""
        assert issubclass(QwenClient, LLMClientBase)


class TestFactory:
    """测试工厂函数。"""

    def test_get_llm_client_returns_client(self):
        """工厂函数返回 LLMClientBase 实例。"""
        # 重置单例，避免其他测试影响
        import src.llm.factory as factory_module
        factory_module._llm_client = None

        client = get_llm_client()
        assert isinstance(client, LLMClientBase)

    def test_get_llm_client_returns_singleton(self):
        """多次调用返回同一个实例。"""
        import src.llm.factory as factory_module
        factory_module._llm_client = None

        client1 = get_llm_client()
        client2 = get_llm_client()
        assert client1 is client2
