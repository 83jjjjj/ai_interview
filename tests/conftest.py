"""pytest 公共测试配置。

提供数据库会话和测试客户端的 fixture，所有测试文件共享。
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from src.core.database import Base, get_db
from src.main import app
from src.models.user import User  # 确保模型被 import，create_all 能发现

# 测试用内存数据库，不影响开发数据库
# StaticPool 确保所有连接共享同一个内存数据库（SQLite 内存模式每个连接是独立的）
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture()
def db():
    """每个测试函数用一个独立的数据库会话，测试结束后自动回滚。"""
    Base.metadata.create_all(bind=TEST_ENGINE)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture()
def client(db):
    """测试用 HTTP 客户端，自动注入测试数据库会话。"""
    # 覆盖 get_db，让 API 函数拿到测试数据库的 session
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
