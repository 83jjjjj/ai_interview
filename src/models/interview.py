"""面试会话和对话记录的数据库模型。

SQLAlchemy ORM 模型，映射到 interview_sessions 表和 conversation_records 表。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class InterviewSession(Base):
    """面试会话表，记录一次面试的基本信息。"""

    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"))
    position: Mapped[str] = mapped_column(String(100))  # 面试岗位，如 "后端开发"
    style: Mapped[str] = mapped_column(String(50))  # 面试风格：深度追问/逻辑考察/综合面试
    difficulty: Mapped[str] = mapped_column(String(50))  # 难度，如 "中等"
    # 状态：进行中/已完成/中断
    status: Mapped[str] = mapped_column(String(20), default="进行中")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # 结束时间，面试结束时才设置
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)


class ConversationRecord(Base):
    """对话记录表，存储面试过程中每一条消息。"""

    __tablename__ = "conversation_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id", ondelete="CASCADE"), index=True
    )
    # 角色：user（用户回答）或 assistant（AI 提问）
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    # 话题编号：从 1 开始，每次开启新话题时 +1
    topic_index: Mapped[int] = mapped_column(default=1)
    # 话题内提问序号：0 = 0式提问（新话题首题），1/2/3 = 1式追问
    question_order: Mapped[int] = mapped_column(default=0)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
