"""AI 面试官服务测试。

测试 prompt 构建、追问逻辑、消息列表组装。
用 mock 替代真实 LLM 调用。
"""

from unittest.mock import patch, MagicMock

from src.services.interviewer import (
    build_system_prompt,
    build_messages,
    count_follow_ups,
    generate_question,
    MAX_FOLLOW_UP,
    STYLE_PROMPTS,
)


class TestBuildSystemPrompt:
    """测试 system prompt 构建。"""

    def test_prompt_contains_position(self):
        """prompt 应包含面试岗位。"""
        prompt = build_system_prompt("后端开发", "综合面试", "中等", "简历内容")
        assert "后端开发" in prompt

    def test_prompt_contains_difficulty(self):
        """prompt 应包含难度。"""
        prompt = build_system_prompt("后端开发", "综合面试", "困难", "简历内容")
        assert "困难" in prompt

    def test_prompt_contains_resume(self):
        """prompt 应包含简历内容。"""
        prompt = build_system_prompt("后端开发", "综合面试", "中等", "精通 Python 和 Go")
        assert "精通 Python 和 Go" in prompt

    def test_prompt_contains_style(self):
        """prompt 应包含对应的风格策略。"""
        for style_name, style_text in STYLE_PROMPTS.items():
            prompt = build_system_prompt("后端开发", style_name, "中等", "简历")
            assert style_text in prompt

    def test_unknown_style_falls_back_to_default(self):
        """未知风格应回退到综合面试。"""
        prompt = build_system_prompt("后端开发", "未知风格", "中等", "简历")
        assert STYLE_PROMPTS["综合面试"] in prompt


class TestBuildMessages:
    """测试消息列表组装。"""

    def test_system_prompt_is_first(self):
        """system prompt 应该是第一条消息。"""
        messages = build_messages("你是面试官", [{"role": "user", "content": "你好"}])
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "你是面试官"

    def test_history_is_included(self):
        """历史对话应包含在消息列表中。"""
        history = [
            {"role": "assistant", "content": "第一题"},
            {"role": "user", "content": "我的回答"},
        ]
        messages = build_messages("system", history)
        assert len(messages) == 3  # system + 2 条历史

    def test_user_message_is_appended(self):
        """用户消息应追加到最后。"""
        messages = build_messages("system", [], user_message="新消息")
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "新消息"

    def test_no_user_message_when_none(self):
        """user_message 为空时不追加。"""
        messages = build_messages("system", [])
        assert len(messages) == 1  # 只有 system


class TestCountFollowUps:
    """测试追问轮数统计。"""

    def test_empty_history(self):
        """空历史返回 0。"""
        assert count_follow_ups([]) == 0

    def test_first_question(self):
        """首次提问（只有 assistant）追问为 0。"""
        history = [{"role": "assistant", "content": "第一题"}]
        assert count_follow_ups(history) == 0

    def test_one_follow_up(self):
        """一轮追问后返回 1。"""
        history = [
            {"role": "assistant", "content": "第一题"},
            {"role": "user", "content": "回答1"},
            {"role": "assistant", "content": "追问"},
        ]
        assert count_follow_ups(history) == 1

    def test_three_follow_ups(self):
        """三轮追问返回 3。"""
        history = [
            {"role": "assistant", "content": "第一题"},
            {"role": "user", "content": "回答1"},
            {"role": "assistant", "content": "追问1"},
            {"role": "user", "content": "回答2"},
            {"role": "assistant", "content": "追问2"},
            {"role": "user", "content": "回答3"},
            {"role": "assistant", "content": "追问3"},
        ]
        assert count_follow_ups(history) == 3


class TestGenerateQuestion:
    """测试提问生成函数。"""

    @patch("src.services.interviewer.get_llm_client")
    def test_first_question_without_user_message(self, mock_get_client):
        """首轮提问时 user_message 为空，应该调用 LLM。"""
        mock_client = MagicMock()
        mock_client.chat.return_value = "请介绍一下你自己"
        mock_get_client.return_value = mock_client

        result = generate_question("后端开发", "综合面试", "中等", "简历内容", [])

        mock_client.chat.assert_called_once()
        assert result == "请介绍一下你自己"

    @patch("src.services.interviewer.get_llm_client")
    def test_follow_up_adds_switch_instruction(self, mock_get_client):
        """追问超限时 prompt 中应包含切换话题指令。"""
        mock_client = MagicMock()
        mock_client.chat.return_value = "换个话题"
        mock_get_client.return_value = mock_client

        # 构造 3 轮追问的历史
        history = [
            {"role": "assistant", "content": "第一题"},
            {"role": "user", "content": "回答1"},
            {"role": "assistant", "content": "追问1"},
            {"role": "user", "content": "回答2"},
            {"role": "assistant", "content": "追问2"},
            {"role": "user", "content": "回答3"},
            {"role": "assistant", "content": "追问3"},
        ]

        generate_question("后端开发", "综合面试", "中等", "简历", history, "新回答")

        # 检查 system prompt 中包含了切换话题的指令
        call_args = mock_client.chat.call_args[0][0]
        system_content = call_args[0]["content"]
        assert "切换" in system_content
