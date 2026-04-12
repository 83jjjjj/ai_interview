"""认证相关 API 路由。

包含注册、登录等接口。登录接口在 task-003 实现。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.user import User
from src.api.schemas import UserRegister, UserResponse
from src.utils.security import hash_password

router = APIRouter(prefix="/api", tags=["认证"])


@router.post("/register", response_model=UserResponse)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    """用户注册。

    检查用户名和邮箱是否重复，通过后创建用户并返回用户信息（不含密码）。
    """
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    # 创建用户，密码加密后存储
    user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user
