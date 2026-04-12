"""User 数据库模型。

SQLAlchemy ORM 模型，映射到 users 表。
"""

from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class User(Base):
    """用户表，存储注册用户的基本信息。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    # 存 bcrypt 哈希值，不存明文密码
    password_hash: Mapped[str] = mapped_column(String(128))
    # server_default 由数据库自动填充时间，不用应用层手动设置
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
