"""登录接口和 JWT 鉴权测试用例。"""


class TestLoginAPI:
    """登录接口测试。"""

    def _register_user(self, client, username="loginuser", email="login@example.com", password="pass123"):
        """辅助方法：注册一个用户用于登录测试。"""
        client.post("/api/register", json={
            "username": username,
            "email": email,
            "password": password,
        })

    def test_login_success(self, client):
        """测试正确登录返回 token。"""
        self._register_user(client)
        response = client.post("/api/login", json={
            "username": "loginuser",
            "password": "pass123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        """测试密码错误。"""
        self._register_user(client)
        response = client.post("/api/login", json={
            "username": "loginuser",
            "password": "wrong_password",
        })
        assert response.status_code == 401

    def test_login_user_not_found(self, client):
        """测试用户不存在。"""
        response = client.post("/api/login", json={
            "username": "nonexistent",
            "password": "pass123",
        })
        assert response.status_code == 401


class TestAuthMiddleware:
    """JWT 鉴权中间件测试。"""

    def _get_token(self, client, username="authuser", email="auth@example.com", password="pass123"):
        """辅助方法：注册并登录获取 token。"""
        client.post("/api/register", json={
            "username": username,
            "email": email,
            "password": password,
        })
        response = client.post("/api/login", json={
            "username": username,
            "password": password,
        })
        return response.json()["access_token"]

    def test_access_with_token(self, client):
        """测试带 token 能访问受保护接口。"""
        token = self._get_token(client)
        response = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "authuser"

    def test_access_without_token(self, client):
        """测试不带 token 返回 401。"""
        response = client.get("/api/me")
        assert response.status_code == 401

    def test_access_with_invalid_token(self, client):
        """测试无效 token 返回 401。"""
        response = client.get("/api/me", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401
