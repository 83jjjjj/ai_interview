"""数据库连接和会话管理。

SQLAlchemy 负责 ORM 映射（Python 类 ↔ 数据库表），本模块配置连接和会话。
SQLite 需要 check_same_thread=False 允许多线程访问（FastAPI 是异步框架）。
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from src.core.config import settings

# 数据库引擎：管理底层数据库连接
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})

# 会话工厂：每次调用创建一个独立的数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """所有数据库表模型的基类，继承此类的类会自动映射为数据库表。"""
    pass


def get_db():
    """FastAPI 依赖注入函数：每个请求自动打开一个数据库会话，请求结束自动关闭。

    用法：在 API 函数参数中添加 db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
