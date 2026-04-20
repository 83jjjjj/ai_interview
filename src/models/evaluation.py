"""Evaluation 数据库模型。

SQLAlchemy ORM 模型，映射到 evaluations 表。
存储面试结束后的 AI 评价结果。
"""

from datetime import datetime

from sqlalchemy import String, DateTime, Text, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Evaluation(Base):
    """评价表，与 InterviewSession 一对一关联。"""

    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 一对一关联 interview_sessions
    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id", ondelete="CASCADE"), unique=True
    )
    overall_score: Mapped[float] = mapped_column(Float)  # 总体评分（0-100）
    summary: Mapped[str] = mapped_column(Text)  # 总体评价
    # 各维度评分（JSON 字符串），如 '{"沟通能力": 80, "技术深度": 75}'
    dimensions: Mapped[str] = mapped_column(Text)
    # 最需改进的问答（JSON 字符串列表）
    improvements: Mapped[str] = mapped_column(Text)
    suggestions: Mapped[str] = mapped_column(Text)  # 改进建议
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
