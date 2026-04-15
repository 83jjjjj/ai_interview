"""面试会话模块测试。

测试 InterviewSession 模型、创建会话接口、发送消息接口。
"""

import io
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.services.resume_parser import ResumeInfo


class TestInterviewSessionModel:
    """测试 InterviewSession 模型字段。"""

    def test_session_fields(self, db):
        """InterviewSession 应该有预期的字段。"""
        from src.models.interview import InterviewSession

        session = InterviewSession(
            user_id=1,
            resume_id=1,
            position="后端开发",
            style="技术面试",
            difficulty="中等",
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        assert session.id is not None
        assert session.user_id == 1
        assert session.resume_id == 1
        assert session.position == "后端开发"
        assert session.status == "进行中"  # 默认值
        assert session.created_at is not None
        assert session.ended_at is None  # 初始未结束


class TestStartInterviewAPI:
    """测试 POST /api/interview/start 接口。"""

    def _register_and_login(self, client: TestClient) -> str:
        """注册用户并登录，返回 token。"""
        client.post("/api/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        })
        response = client.post("/api/login", json={
            "username": "testuser",
            "password": "password123",
        })
        return response.json()["access_token"]

    def _create_resume(self, client: TestClient, token: str) -> dict:
        """创建一个简历，返回简历数据。"""
        with patch("src.api.resume.parse_resume", return_value=ResumeInfo(name="测试")):
            response = client.post(
                "/api/resume/upload",
                files={"file": ("resume.pdf", io.BytesIO(b"fake"), "application/pdf")},
                headers={"Authorization": f"Bearer {token}"},
            )
            return response.json()

    def test_start_success(self, client: TestClient):
        """正常创建面试会话，status 应为进行中。"""
        token = self._register_and_login(client)
        resume = self._create_resume(client, token)

        response = client.post(
            "/api/interview/start",
            json={"resume_id": resume["id"], "position": "后端开发"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "进行中"
        assert data["position"] == "后端开发"
        assert data["resume_id"] == resume["id"]

    def test_start_resume_not_found(self, client: TestClient):
        """简历不存在时返回 404。"""
        token = self._register_and_login(client)

        response = client.post(
            "/api/interview/start",
            json={"resume_id": 999, "position": "后端开发"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        assert "简历不存在" in response.json()["detail"]

    def test_start_resume_not_owned(self, client: TestClient):
        """别人的简历返回 404。"""
        # 用户 A 创建简历
        token_a = self._register_and_login(client)
        resume = self._create_resume(client, token_a)

        # 用户 B 尝试用 A 的简历创建会话
        client.post("/api/register", json={
            "username": "userb",
            "email": "b@example.com",
            "password": "password123",
        })
        token_b = client.post("/api/login", json={
            "username": "userb",
            "password": "password123",
        }).json()["access_token"]

        response = client.post(
            "/api/interview/start",
            json={"resume_id": resume["id"], "position": "后端开发"},
            headers={"Authorization": f"Bearer {token_b}"},
        )

        assert response.status_code == 404

    def test_start_without_auth(self, client: TestClient):
        """未登录创建会话返回 401。"""
        response = client.post(
            "/api/interview/start",
            json={"resume_id": 1, "position": "后端开发"},
        )
        assert response.status_code == 401


class TestSendMessageAPI:
    """测试 POST /api/interview/{id}/message 接口。"""

    def _register_and_login(self, client: TestClient) -> str:
        """注册用户并登录，返回 token。"""
        client.post("/api/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        })
        response = client.post("/api/login", json={
            "username": "testuser",
            "password": "password123",
        })
        return response.json()["access_token"]

    def _create_resume(self, client: TestClient, token: str) -> dict:
        """创建一个简历，返回简历数据。"""
        with patch("src.api.resume.parse_resume", return_value=ResumeInfo(name="测试")):
            response = client.post(
                "/api/resume/upload",
                files={"file": ("resume.pdf", io.BytesIO(b"fake"), "application/pdf")},
                headers={"Authorization": f"Bearer {token}"},
            )
            return response.json()

    def _start_session(self, client: TestClient, token: str, resume_id: int) -> dict:
        """创建面试会话，返回会话数据。"""
        response = client.post(
            "/api/interview/start",
            json={"resume_id": resume_id, "position": "后端开发"},
            headers={"Authorization": f"Bearer {token}"},
        )
        return response.json()

    def test_send_message_success(self, client: TestClient):
        """正常发送消息，记录中 role 应为 user。"""
        token = self._register_and_login(client)
        resume = self._create_resume(client, token)
        session = self._start_session(client, token, resume["id"])

        response = client.post(
            f"/api/interview/{session['id']}/message",
            json={"content": "我叫张三，毕业于清华大学"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "user"
        assert data["content"] == "我叫张三，毕业于清华大学"
        assert data["session_id"] == session["id"]

    def test_send_session_not_found(self, client: TestClient):
        """会话不存在时返回 404。"""
        token = self._register_and_login(client)

        response = client.post(
            "/api/interview/999/message",
            json={"content": "你好"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    def test_send_session_ended(self, client: TestClient, db):
        """已结束的会话发送消息返回 400。"""
        token = self._register_and_login(client)
        resume = self._create_resume(client, token)
        session = self._start_session(client, token, resume["id"])

        # 用测试 db fixture 修改会话状态为已结束
        from src.models.interview import InterviewSession as SessionModel
        db_session = db.query(SessionModel).filter(SessionModel.id == session["id"]).first()
        db_session.status = "已完成"
        db.commit()

        response = client.post(
            f"/api/interview/{session['id']}/message",
            json={"content": "迟到的消息"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert "已结束" in response.json()["detail"]

    def test_send_without_auth(self, client: TestClient):
        """未登录发送消息返回 401。"""
        response = client.post(
            "/api/interview/1/message",
            json={"content": "你好"},
        )
        assert response.status_code == 401
