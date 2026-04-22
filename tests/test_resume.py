"""简历模块测试。

测试 Resume 模型字段、上传接口、列表接口。
"""

import io
import json
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


class TestResumeModel:
    """测试 Resume 模型的字段和关系。"""

    def test_resume_fields(self, db):
        """Resume 模型应该有预期的字段。"""
        from src.models.resume import Resume

        resume = Resume(
            user_id=1,
            filename="test.pdf",
            file_path="uploads/test.pdf",
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        assert resume.id is not None
        assert resume.user_id == 1
        assert resume.filename == "test.pdf"
        assert resume.file_path == "uploads/test.pdf"
        assert resume.parsed_content == ""
        assert resume.parse_status == "pending"  # 默认状态
        assert resume.created_at is not None


class TestUploadAPI:
    """测试 POST /api/resume/upload 接口。"""

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

    def test_upload_returns_immediately(self, client: TestClient):
        """上传应该立即返回 201，parse_status 为 pending。"""
        token = self._register_and_login(client)

        pdf_content = b"%PDF-1.4 fake content"
        response = client.post(
            "/api/resume/upload",
            files={"file": ("resume.pdf", io.BytesIO(pdf_content), "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "resume.pdf"
        assert data["parse_status"] == "pending"

        if os.path.exists(data["file_path"]):
            os.remove(data["file_path"])

    def test_upload_image_success(self, client: TestClient):
        """上传图片文件应该成功。"""
        token = self._register_and_login(client)

        img_content = b"\x89PNG fake content"
        response = client.post(
            "/api/resume/upload",
            files={"file": ("resume.png", io.BytesIO(img_content), "image/png")},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "resume.png"
        assert data["parse_status"] == "pending"

        if os.path.exists(data["file_path"]):
            os.remove(data["file_path"])

    def test_upload_unsupported_format(self, client: TestClient):
        """上传不支持的格式应该返回 400。"""
        token = self._register_and_login(client)

        response = client.post(
            "/api/resume/upload",
            files={"file": ("resume.docx", io.BytesIO(b"fake"), "application/msword")},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert "不支持的文件格式" in response.json()["detail"]

    def test_upload_without_auth(self, client: TestClient):
        """未登录上传应该返回 401。"""
        response = client.post(
            "/api/resume/upload",
            files={"file": ("resume.pdf", io.BytesIO(b"fake"), "application/pdf")},
        )

        assert response.status_code == 401

    def test_background_parse_updates_status(self, db, client: TestClient):
        """后台解析完成后 parse_status 应为 done。"""
        from src.api.resume import _parse_resume_background
        from src.models.resume import Resume
        from src.services.resume_parser import ResumeInfo

        resume = Resume(
            user_id=1,
            filename="test.pdf",
            file_path="uploads/test.pdf",
            parse_status="pending",
        )
        db.add(resume)
        db.commit()
        resume_id = resume.id

        # mock parse_resume 和 SessionLocal（让后台函数用测试的 db）
        with patch("src.api.resume.parse_resume") as mock_parse, \
             patch("src.api.resume.SessionLocal", return_value=db):
            mock_parse.return_value = ResumeInfo(name="张三")
            _parse_resume_background(resume_id, "简历内容")

        # 重新查询（因为背景函数关闭了 session）
        updated = db.query(Resume).filter(Resume.id == resume_id).first()
        assert updated.parse_status == "done"
        assert "张三" in updated.parsed_content


class TestListAPI:
    """测试 GET /api/resume/list 接口。"""

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

    def test_list_empty(self, client: TestClient):
        """没有上传过简历时返回空列表。"""
        token = self._register_and_login(client)

        response = client.get(
            "/api/resume/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_list_after_upload(self, client: TestClient):
        """上传后列表应该包含该记录。"""
        token = self._register_and_login(client)

        # 上传一个文件
        upload_response = client.post(
            "/api/resume/upload",
            files={"file": ("resume.pdf", io.BytesIO(b"fake"), "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )

        # 查询列表
        list_response = client.get(
            "/api/resume/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert list_response.status_code == 200
        resumes = list_response.json()
        assert len(resumes) == 1
        assert resumes[0]["id"] == upload_response.json()["id"]
        assert resumes[0]["parse_status"] == "pending"

        # 清理
        if os.path.exists(upload_response.json()["file_path"]):
            os.remove(upload_response.json()["file_path"])

    def test_list_without_auth(self, client: TestClient):
        """未登录查询列表应该返回 401。"""
        response = client.get("/api/resume/list")
        assert response.status_code == 401
