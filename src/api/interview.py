"""面试相关 API 路由。

包含面试会话创建、消息发送、SSE 流式 AI 回复等接口。
"""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
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
from src.services.interviewer import (
    build_system_prompt,
    build_messages,
    count_follow_ups,
    MAX_FOLLOW_UP,
)
from src.llm.factory import get_llm_client

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


@router.get("/{session_id}/stream")
def stream_response(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """SSE 流式返回 AI 面试官的回复。

    读取会话历史，构建 prompt，调 LLM 流式输出，逐 token 返回。
    完成后将完整 AI 回复存入 ConversationRecord。
    """
    # 验证会话
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
            detail="面试已结束，无法获取回复",
        )

    # 获取简历文本
    resume = db.query(Resume).filter(Resume.id == session.resume_id).first()

    # 获取历史对话，构建消息列表
    history_records = (
        db.query(ConversationRecord)
        .filter(ConversationRecord.session_id == session_id)
        .order_by(ConversationRecord.timestamp)
        .all()
    )
    history = [{"role": r.role, "content": r.content} for r in history_records]

    # 获取最后一条 assistant 消息的 question_order，用于判断追问轮数
    last_assistant = None
    for r in reversed(history_records):
        if r.role == "assistant":
            last_assistant = r
            break
    last_question_order = last_assistant.question_order if last_assistant else None

    # 构建 system prompt
    system_prompt = build_system_prompt(
        session.position, session.style, session.difficulty, resume.parsed_content
    )
    follow_up_count = count_follow_ups(last_question_order)
    if follow_up_count >= MAX_FOLLOW_UP:
        system_prompt += (
            "\n\n注意：你已经连续追问了 3 轮，现在必须切换到一个全新的话题。"
            "不要再追问当前话题的细节。"
        )

    messages = build_messages(system_prompt, history)

    # 计算新 assistant 消息的 topic_index 和 question_order
    if last_assistant is None:
        # 首次提问
        new_topic_index = 1
        new_question_order = 0
    elif last_question_order >= MAX_FOLLOW_UP:
        # 追问超限，切换话题
        new_topic_index = last_assistant.topic_index + 1
        new_question_order = 0
    else:
        # 继续追问
        new_topic_index = last_assistant.topic_index
        new_question_order = last_question_order + 1

    def generate():
        """SSE 生成器，逐 token 返回 AI 回复。"""
        client = get_llm_client()
        full_response = ""

        for chunk in client.chat_stream(messages):
            full_response += chunk
            yield f"data: {json.dumps({'content': chunk})}\n\n"

        # 存储完整 AI 回复
        record = ConversationRecord(
            session_id=session_id,
            role="assistant",
            content=full_response,
            topic_index=new_topic_index,
            question_order=new_question_order,
        )
        db.add(record)
        db.commit()

        # 发送结束信号
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
