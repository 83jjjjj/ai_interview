"""个人能力分析模块测试。

测试分析服务和 API 接口。
"""

import io
import json
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.services.resume_parser import ResumeInfo


class TestAnalyzeUser:
    """测试分析服务。"""

    def test_empty_evaluations(self):
        """无评价数据时返回默认结果。"""
        from src.services.analyzer import analyze_user

        result = analyze_user([])

        assert result.total_interviews == 0
        assert result.average_score == 0
        assert "请先完成" in result.development_plan

    @patch("src.services.analyzer.get_llm_client")
    def test_with_evaluations(self, mock_get_client):
        """有评价数据时返回分析结果。"""
        from src.services.analyzer import analyze_user, AnalysisResult

        mock_client = MagicMock()
        mock_client.chat.return_value = json.dumps({
            "strength": "技术扎实",
            "weakness": "沟通表达需提升",
            "development_plan": "多练习技术分享",
        })
        mock_get_client.return_value = mock_client

        evaluations = [
            {
                "overall_score": 80,
                "summary": "良好",
                "dimensions": {"沟通表达": 70, "技术深度": 85},
                "improvements": [],
                "suggestions": "无",
            },
            {
                "overall_score": 75,
                "summary": "还行",
                "dimensions": {"沟通表达": 75, "技术深度": 80},
                "improvements": [],
                "suggestions": "无",
            },
        ]

        result = analyze_user(evaluations)

        assert isinstance(result, AnalysisResult)
        assert result.total_interviews == 2
        assert result.average_score == 77.5
        assert "技术扎实" in result.strength
        assert "沟通表达" in result.dimension_trends
        assert result.dimension_trends["沟通表达"] == [70, 75]

    @patch("src.services.analyzer.get_llm_client")
    def test_llm_error_returns_default(self, mock_get_client):
        """LLM 异常时返回默认信息。"""
        from src.services.analyzer import analyze_user

        mock_client = MagicMock()
        mock_client.chat.side_effect = Exception("连接失败")
        mock_get_client.return_value = mock_client

        result = analyze_user([{"overall_score": 80, "summary": "test", "dimensions": {}, "improvements": [], "suggestions": ""}])

        assert "不可用" in result.strength


class TestAnalysisAPI:
    """测试 GET /api/analysis 接口。"""

    def _register_and_login(self, client: TestClient) -> str:
        client.post("/api/register", json={
            "username": "testuser", "email": "test@example.com", "password": "123456",
        })
        return client.post("/api/login", json={
            "username": "testuser", "password": "123456",
        }).json()["access_token"]

    def _create_resume(self, client: TestClient, token: str) -> dict:
        with patch("src.api.resume.parse_resume", return_value=ResumeInfo(name="测试")):
            return client.post("/api/resume/upload",
                files={"file": ("r.pdf", io.BytesIO(b"fake"), "application/pdf")},
                headers={"Authorization": f"Bearer {token}"}).json()

    def _start_session(self, client: TestClient, token: str, resume_id: int) -> dict:
        return client.post("/api/interview/start",
            json={"resume_id": resume_id, "position": "后端开发"},
            headers={"Authorization": f"Bearer {token}"}).json()

    def _end_session(self, client: TestClient, token: str, session_id: int):
        client.post(f"/api/interview/{session_id}/end",
                    headers={"Authorization": f"Bearer {token}"})

    def _create_evaluation(self, client: TestClient, token: str, session_id: int):
        self._end_session(client, token, session_id)
        with patch("src.services.evaluator.get_llm_client") as mock_eval_client:
            mock_client = MagicMock()
            mock_client.chat.return_value = json.dumps({
                "overall_score": 80,
                "summary": "表现良好",
                "dimensions": {"沟通表达": 75, "技术深度": 85, "逻辑思维": 80, "问题解决": 80},
                "improvements": [],
                "suggestions": "继续努力",
            })
            mock_eval_client.return_value = mock_client
            # 通过 evaluation-stream 写入评价
            client.get(
                f"/api/interview/{session_id}/evaluation-stream?access_token={token}",
            )

    @patch("src.services.analyzer.get_llm_client")
    def test_analysis_with_data(self, mock_analyzer_client, client: TestClient):
        """有面试评价时返回分析结果。"""
        mock_client = MagicMock()
        mock_client.chat.return_value = json.dumps({
            "strength": "技术扎实",
            "weakness": "沟通需提升",
            "development_plan": "多练习",
        })
        mock_analyzer_client.return_value = mock_client

        token = self._register_and_login(client)
        resume = self._create_resume(client, token)
        session = self._start_session(client, token, resume["id"])
        self._create_evaluation(client, token, session["id"])

        response = client.get("/api/analysis",
                              headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["total_interviews"] == 1
        assert data["average_score"] == 80.0

    def test_analysis_no_data(self, client: TestClient):
        """无面试记录时返回空分析。"""
        token = self._register_and_login(client)
        response = client.get("/api/analysis",
                              headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["total_interviews"] == 0

    def test_analysis_without_auth(self, client: TestClient):
        """未登录返回 401。"""
        response = client.get("/api/analysis")
        assert response.status_code == 401
