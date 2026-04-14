"""简历相关 API 路由。

包含简历上传、列表查询等接口。
"""

import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.resume import Resume
from src.models.user import User
from src.api.auth import get_current_user
from src.api.schemas import ResumeResponse

router = APIRouter(prefix="/api/resume", tags=["简历"])

# 允许上传的文件类型
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
# 上传文件存储目录
UPLOAD_DIR = "uploads"


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传简历文件。

    支持 PDF 和图片格式，文件存入 uploads/ 目录，记录写入数据库。
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

    # 写入数据库
    resume = Resume(
        user_id=current_user.id,
        filename=file.filename,
        file_path=file_path,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return resume


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
