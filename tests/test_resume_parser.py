"""简历解析服务测试。

用 mock 替代真实 LLM 调用，验证解析逻辑和 Pydantic 校验。
"""

import json
from unittest.mock import patch, MagicMock

from src.services.resume_parser import parse_resume, ResumeInfo


class TestParseResume:
    """测试简历解析函数。"""

    @patch("src.services.resume_parser.get_llm_client")
    def test_parse_resume_returns_resume_info(self, mock_get_client):
        """parse_resume 应该返回 ResumeInfo 模型实例。"""
        mock_client = MagicMock()
        mock_client.chat.return_value = json.dumps({
            "name": "张三",
            "email": "zhangsan@example.com",
            "phone": "13800138000",
            "education": [{"school": "清华", "degree": "本科", "major": "CS", "duration": "2018-2022"}],
            "work_experience": [],
            "skills": ["Python", "Java"],
            "summary": "优秀的工程师",
        })
        mock_get_client.return_value = mock_client

        result = parse_resume("张三，毕业于清华大学")

        # 验证返回的是 ResumeInfo 实例
        assert isinstance(result, ResumeInfo)
        assert result.name == "张三"
        assert result.email == "zhangsan@example.com"
        assert len(result.education) == 1
        assert result.education[0].school == "清华"
        assert result.skills == ["Python", "Java"]

    @patch("src.services.resume_parser.get_llm_client")
    def test_parse_resume_invalid_json_returns_default(self, mock_get_client):
        """LLM 输出不是有效 JSON 时，返回默认 ResumeInfo。"""
        mock_client = MagicMock()
        mock_client.chat.return_value = "这不是 JSON"
        mock_get_client.return_value = mock_client

        result = parse_resume("随便什么文本")

        assert isinstance(result, ResumeInfo)
        assert result.name == "未提供"
        assert result.education == []
        assert result.skills == []

    @patch("src.services.resume_parser.get_llm_client")
    def test_parse_resume_passes_messages(self, mock_get_client):
        """parse_resume 应该把简历文本放进 user 消息中。"""
        mock_client = MagicMock()
        mock_client.chat.return_value = json.dumps({"name": "李四"})
        mock_get_client.return_value = mock_client

        raw_text = "我叫李四，毕业于清华大学"
        parse_resume(raw_text)

        call_args = mock_client.chat.call_args[0][0]
        assert len(call_args) == 2
        assert call_args[0]["role"] == "system"
        assert call_args[1]["role"] == "user"
        assert "李四" in call_args[1]["content"]
