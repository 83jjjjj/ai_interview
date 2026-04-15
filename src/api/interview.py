"""面试相关 API 路由。

包含面试会话创建、消息发送等接口。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.interview import InterviewSession, ConversationRecord
from src.models.resume import Resume
from src.models.user import User
from src.api.auth import get_current_user
from src.api.schemas import (
    InterviewStartRequest,
    InterviewSessionResponse,
    MessageRequest,
    ConversationRecordResponse,
)

router = APIRouter(prefix="/api/interview", tags=["面试"])


@router.post("/start", response_model=InterviewSessionResponse, status_code=status.HTTP_201_CREATED)
def start_interview(
    request: InterviewStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建面试会话。

    验证简历归属后，创建新的面试会话，状态初始为"进行中"。
    """
    # 验证简历存在且属于当前用户
    resume = db.query(Resume).filter(
        Resume.id == request.resume_id,
        Resume.user_id == current_user.id,
    ).first()
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="简历不存在",
        )

    session = InterviewSession(
        user_id=current_user.id,
        resume_id=request.resume_id,
        position=request.position,
        style=request.style,
        difficulty=request.difficulty,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return session


@router.post("/{session_id}/message", response_model=ConversationRecordResponse)
def send_message(
    session_id: int,
    request: MessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发送用户消息到面试会话。

    验证会话存在且属于当前用户后，将消息存入对话记录。
    """
    # 验证会话存在且属于当前用户
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    ).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="面试会话不存在",
        )

    if session.status != "进行中":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="面试已结束，无法发送消息",
        )

    # 存储用户消息
    record = ConversationRecord(
        session_id=session_id,
        role="user",
        content=request.content,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return record
