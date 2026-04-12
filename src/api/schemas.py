"""API 请求和响应的数据模型。

Pydantic 模型用于参数校验和响应序列化，不等于数据库模型。
"""

from datetime import datetime
from typing import Optional

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
