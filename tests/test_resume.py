"""简历模块测试。

测试 Resume 模型字段、上传接口、列表接口。
"""

import io
import os
import shutil

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
        assert resume.parsed_content == ""  # 默认为空字符串
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

    def test_upload_pdf_success(self, client: TestClient):
        """上传 PDF 文件应该成功。"""
        token = self._register_and_login(client)

        # 创建一个假的 PDF 文件（内容无关紧要，只测接口逻辑）
        pdf_content = b"%PDF-1.4 fake content"
        response = client.post(
            "/api/resume/upload",
            files={"file": ("resume.pdf", io.BytesIO(pdf_content), "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "resume.pdf"
        assert data["parsed_content"] == ""

        # 清理上传的文件
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

        # 清理
        if os.path.exists(upload_response.json()["file_path"]):
            os.remove(upload_response.json()["file_path"])

    def test_list_without_auth(self, client: TestClient):
        """未登录查询列表应该返回 401。"""
        response = client.get("/api/resume/list")
        assert response.status_code == 401
