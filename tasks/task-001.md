# task-001: 初始化后端项目结构

## 描述
搭建 FastAPI 项目骨架，配置目录结构、依赖、数据库连接。

## 具体内容
- 创建项目目录结构（api / models / services / core / tests）
- 创建 requirements.txt（fastapi / uvicorn / sqlalchemy / pydantic / python-jose / passlib / bcrypt / pytest）
- 创建 FastAPI 入口 main.py
- 配置 SQLAlchemy 数据库连接（SQLite）
- 创建数据库初始化脚本（create_all）
- 配置 .gitignore

## 验收标准
- `pip install -r requirements.txt` 成功
- `uvicorn main:app` 能启动，/docs 能看到 Swagger 页面
- 数据库文件自动创建

## 依赖
无
