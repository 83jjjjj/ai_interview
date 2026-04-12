"""用户模型和注册接口测试用例。"""


class TestUserModel:
    """User 模型测试。"""

    def test_user_fields(self, db):
        """测试 User 模型字段完整性。"""
        from src.models.user import User

        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.created_at is not None

    def test_username_unique(self, db):
        """测试用户名唯一约束。"""
        from src.models.user import User
        import pytest

        user1 = User(username="same", email="a@example.com", password_hash="hash1")
        user2 = User(username="same", email="b@example.com", password_hash="hash2")
        db.add(user1)
        db.commit()

        db.add(user2)
        with pytest.raises(Exception):
            db.commit()

    def test_email_unique(self, db):
        """测试邮箱唯一约束。"""
        from src.models.user import User
        import pytest

        user1 = User(username="user1", email="same@example.com", password_hash="hash1")
        user2 = User(username="user2", email="same@example.com", password_hash="hash2")
        db.add(user1)
        db.commit()

        db.add(user2)
        with pytest.raises(Exception):
            db.commit()


class TestRegisterAPI:
    """注册接口测试。"""

    def test_register_success(self, client):
        """测试正常注册。"""
        response = client.post("/api/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert "password" not in data  # 密码不能出现在响应里
        assert "password_hash" not in data

    def test_register_duplicate_username(self, client):
        """测试用户名重复。"""
        client.post("/api/register", json={
            "username": "dupuser",
            "email": "a@example.com",
            "password": "password123",
        })
        response = client.post("/api/register", json={
            "username": "dupuser",
            "email": "b@example.com",
            "password": "password123",
        })
        assert response.status_code == 400

    def test_register_duplicate_email(self, client):
        """测试邮箱重复。"""
        client.post("/api/register", json={
            "username": "user1",
            "email": "dup@example.com",
            "password": "password123",
        })
        response = client.post("/api/register", json={
            "username": "user2",
            "email": "dup@example.com",
            "password": "password123",
        })
        assert response.status_code == 400

    def test_register_missing_fields(self, client):
        """测试缺字段。"""
        response = client.post("/api/register", json={
            "username": "user",
            # 缺 email 和 password
        })
        assert response.status_code == 422
