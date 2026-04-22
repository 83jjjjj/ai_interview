"""面试评价模块测试。

测试 Evaluation 模型、评价服务、结束面试接口。
"""

import io
import json
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.services.resume_parser import ResumeInfo


class TestEvaluationModel:
    """测试 Evaluation 模型字段。"""

    def test_evaluation_fields(self, db):
        """Evaluation 应该有预期的字段。"""
        from src.models.evaluation import Evaluation

        evaluation = Evaluation(
            session_id=1,
            overall_score=85.0,
            summary="表现良好",
            dimensions='{"沟通表达": 80}',
            improvements='["改进点1"]',
            suggestions="多练习",
        )
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)

        assert evaluation.id is not None
        assert evaluation.session_id == 1
        assert evaluation.overall_score == 85.0
        assert evaluation.summary == "表现良好"
        assert evaluation.created_at is not None


class TestEvaluateInterview:
    """测试评价生成服务。"""

    @patch("src.services.evaluator.get_llm_client")
    def test_evaluate_returns_result(self, mock_get_client):
        """评价函数应返回 EvaluationResult。"""
        from src.services.evaluator import evaluate_interview, EvaluationResult

        mock_client = MagicMock()
        mock_client.chat.return_value = json.dumps({
            "overall_score": 80.0,
            "summary": "技术扎实",
            "dimensions": {"沟通表达": 75, "技术深度": 85, "逻辑思维": 80, "问题解决": 80},
            "improvements": ["表达可以更简洁"],
            "suggestions": "多练习技术分享",
        })
        mock_get_client.return_value = mock_client

        result = evaluate_interview("后端开发", "综合面试", "中等", [
            {"role": "assistant", "content": "请介绍自己"},
            {"role": "user", "content": "我叫张三"},
        ])

        assert isinstance(result, EvaluationResult)
        assert result.overall_score == 80.0
        assert result.summary == "技术扎实"

    @patch("src.services.evaluator.get_llm_client")
    def test_evaluate_invalid_json_returns_default(self, mock_get_client):
        """LLM 输出无效 JSON 时返回默认评价。"""
        from src.services.evaluator import evaluate_interview

        mock_client = MagicMock()
        mock_client.chat.return_value = "不是 JSON"
        mock_get_client.return_value = mock_client

        result = evaluate_interview("后端开发", "综合面试", "中等", [])

        assert result.overall_score == 60.0
        assert "失败" in result.summary


class TestEndInterviewAPI:
    """测试 POST /api/interview/{id}/end 接口。"""

    def _register_and_login(self, client: TestClient) -> str:
        client.post("/api/register", json={
            "username": "testuser", "email": "test@example.com", "password": "123456",
        })
        return client.post("/api/login", json={
            "username": "testuser", "password": "123456",
        }).json()["access_token"]

    def _create_resume(self, client: TestClient, token: str) -> dict:
        with patch("src.api.resume.parse_resume", return_value=ResumeInfo(name="测试")):
            return client.post(
                "/api/resume/upload",
                files={"file": ("r.pdf", io.BytesIO(b"fake"), "application/pdf")},
                headers={"Authorization": f"Bearer {token}"},
            ).json()

    def _start_session(self, client: TestClient, token: str, resume_id: int) -> dict:
        return client.post(
            "/api/interview/start",
            json={"resume_id": resume_id, "position": "后端开发"},
            headers={"Authorization": f"Bearer {token}"},
        ).json()

    @patch("src.services.evaluator.get_llm_client")
    def test_end_success(self, mock_get_client, client: TestClient, db):
        """正常结束面试，session 状态变为已完成。"""
        token = self._register_and_login(client)
        resume = self._create_resume(client, token)
        session = self._start_session(client, token, resume["id"])

        response = client.post(
            f"/api/interview/{session['id']}/end",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_status"] == "已完成"

        # 验证 session 状态已更新
        from src.models.interview import InterviewSession as SessionModel
        session_record = db.query(SessionModel).filter(SessionModel.id == session["id"]).first()
        assert session_record.status == "已完成"
        assert session_record.ended_at is not None

    def test_end_session_not_found(self, client: TestClient):
        """会话不存在返回 404。"""
        token = self._register_and_login(client)
        response = client.post(
            "/api/interview/999/end",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    @patch("src.services.evaluator.get_llm_client")
    def test_end_already_ended(self, mock_get_client, client: TestClient, db):
        """重复结束返回 400。"""
        mock_client = MagicMock()
        mock_client.chat.return_value = json.dumps({
            "overall_score": 85.0, "summary": "测试",
            "dimensions": {"沟通表达": 80, "技术深度": 80, "逻辑思维": 80, "问题解决": 80},
            "improvements": [], "suggestions": "无",
        })
        mock_get_client.return_value = mock_client

        token = self._register_and_login(client)
        resume = self._create_resume(client, token)
        session = self._start_session(client, token, resume["id"])

        # 第一次结束
        client.post(f"/api/interview/{session['id']}/end",
                     headers={"Authorization": f"Bearer {token}"})
        # 第二次结束
        response = client.post(f"/api/interview/{session['id']}/end",
                                headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 400

    def test_end_without_auth(self, client: TestClient):
        """未登录返回 401。"""
        response = client.post("/api/interview/1/end")
        assert response.status_code == 401
