"""Resume 数据库模型。

SQLAlchemy ORM 模型，映射到 resumes 表。
存储用户上传的简历文件信息和 AI 解析后的文本内容。
"""

from datetime import datetime

from sqlalchemy import String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Resume(Base):
    """简历表，关联到上传者。"""

    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 外键关联 users 表，删除用户时级联删除其简历
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))  # 用户上传时的原始文件名
    file_path: Mapped[str] = mapped_column(String(500))  # 服务器存储路径
    # AI 解析后的简历文本内容，初始为空，后续 task-007 填充
    parsed_content: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
