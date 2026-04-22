"""简历相关 API 路由。

包含简历上传、列表查询等接口。
"""

import os
import uuid
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from src.core.database import get_db, SessionLocal
from src.models.resume import Resume
from src.models.user import User
from src.api.auth import get_current_user
from src.api.schemas import ResumeResponse
from src.services.resume_parser import parse_resume

router = APIRouter(prefix="/api/resume", tags=["简历"])

# 允许上传的文件类型
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
# 上传文件存储目录
UPLOAD_DIR = "uploads"


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传简历文件。

    立即保存文件并返回，后台异步调 LLM 解析。
    """
    # 检查文件扩展名
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式 {ext}，仅支持 {ALLOWED_EXTENSIONS}",
        )

    # 确保上传目录存在
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 生成唯一文件名，避免重名覆盖
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # 写入文件
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # 写入数据库（状态=pending，后台异步解析）
    resume = Resume(
        user_id=current_user.id,
        filename=file.filename,
        file_path=file_path,
        parse_status="pending",
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # 后台异步解析
    resume_id = resume.id
    raw_text = content.decode("utf-8", errors="ignore")
    background_tasks.add_task(_parse_resume_background, resume_id, raw_text)

    return resume


def _parse_resume_background(resume_id: int, raw_text: str):
    """后台任务：调 LLM 解析简历，更新数据库。"""
    db = SessionLocal()
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if resume is None:
            return

        resume_info = parse_resume(raw_text)
        resume.parsed_content = resume_info.model_dump_json()
        resume.parse_status = "done"
        db.commit()
    except Exception:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if resume:
            resume.parse_status = "failed"
            db.commit()
    finally:
        db.close()


@router.get("/list", response_model=List[ResumeResponse])
def list_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的简历列表。

    按上传时间倒序排列，最近上传的在前面。
    """
    resumes = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
        .all()
    )
    return resumes
