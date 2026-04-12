"""FastAPI 应用入口。

启动命令：uvicorn src.main:app --reload
API 文档：http://localhost:8000/docs
"""

from fastapi import FastAPI
from src.core.database import engine, Base

app = FastAPI(title="AI 面试器", version="0.1.0")


@app.on_event("startup")
def on_startup():
    """应用启动时自动创建所有数据库表（基于继承 Base 的模型类）。"""
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    """健康检查接口，用于验证服务是否正常运行。"""
    return {"status": "ok"}
