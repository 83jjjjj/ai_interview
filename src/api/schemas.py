"""API 请求和响应的数据模型。

Pydantic 模型用于参数校验和响应序列化，不等于数据库模型。
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    """注册请求体。"""
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    """用户信息响应体，不包含密码相关字段。"""
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True  # 允许从 ORM 对象（User 模型）直接转换


class LoginRequest(BaseModel):
    """登录请求体（task-003 用）。"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """登录成功后的 token 响应（task-003 用）。"""
    access_token: str
    token_type: str = "bearer"


class ResumeResponse(BaseModel):
    """简历信息响应体。"""
    id: int
    user_id: int
    filename: str
    file_path: str
    parsed_content: str
    created_at: datetime
    # 告诉 Pydantic 可以从 ORM 模型（Resume）直接转换
    class Config:
        from_attributes = True


class InterviewStartRequest(BaseModel):
    """创建面试会话的请求体。"""
    resume_id: int
    position: str  # 面试岗位
    style: str = "综合面试"  # 面试风格：深度追问/逻辑考察/综合面试
    difficulty: str = "中等"  # 难度，默认中等


class InterviewSessionResponse(BaseModel):
    """面试会话响应体。"""
    id: int
    user_id: int
    resume_id: int
    position: str
    style: str
    difficulty: str
    status: str
    created_at: datetime
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageRequest(BaseModel):
    """发送消息的请求体。"""
    content: str


class ConversationRecordResponse(BaseModel):
    """单条对话记录响应体。"""
    id: int
    session_id: int
    role: str
    content: str
    topic_index: int
    question_order: int
    timestamp: datetime

    class Config:
        from_attributes = True
