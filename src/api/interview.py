"""面试相关 API 路由。

包含面试会话创建、消息发送、SSE 流式 AI 回复等接口。
"""

import json

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.interview import InterviewSession, ConversationRecord
from src.models.resume import Resume
from src.models.user import User
from src.api.auth import get_current_user, get_current_user_for_sse
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


@router.post("/{session_id}/end")
def end_interview(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """结束面试。

    立即更新 session 状态。评价通过 SSE 接口单独生成。
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
            detail="面试已结束，无法重复结束",
        )

    # 更新 session 状态为已完成
    from datetime import datetime
    session.status = "已完成"
    session.ended_at = datetime.utcnow()
    db.commit()

    return {"session_status": session.status}


@router.get("/{session_id}/stream")
def stream_response(
    session_id: int,
    current_user: User = Depends(get_current_user_for_sse),
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


@router.get("/list", response_model=List[InterviewSessionResponse])
def list_interviews(
    status_filter: Optional[str] = Query(None, alias="status"),
    position: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询当前用户的面试会话列表。

    支持按 status 和 position 筛选，按 created_at 倒序，支持分页。
    """
    query = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    )

    if status_filter:
        query = query.filter(InterviewSession.status == status_filter)
    if position:
        query = query.filter(InterviewSession.position.contains(position))

    sessions = (
        query.order_by(InterviewSession.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return sessions


@router.get("/{session_id}/evaluation-stream")
def evaluation_stream(
    session_id: int,
    current_user: User = Depends(get_current_user_for_sse),
    db: Session = Depends(get_db),
):
    """SSE 流式生成面试评价。

    前端结束面试后调用此接口，后端调 LLM 流式生成评价，逐字返回。
    生成完毕后将完整评价存入 Evaluation 表。
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
    if session.status != "已完成":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="面试尚未结束，无法生成评价",
        )

    # 检查是否已有评价
    from src.models.evaluation import Evaluation
    existing = db.query(Evaluation).filter(Evaluation.session_id == session_id).first()
    if existing:
        # 已有评价，直接返回
        return StreamingResponse(
            iter([f"data: {json.dumps({'done': True, 'evaluation_id': existing.id})}\n\n"]),
            media_type="text/event-stream",
        )

    # 收集对话记录
    history_records = (
        db.query(ConversationRecord)
        .filter(ConversationRecord.session_id == session_id)
        .order_by(ConversationRecord.timestamp)
        .all()
    )
    history = [{"role": r.role, "content": r.content} for r in history_records]

    # 构建评价 prompt
    from src.services.evaluator import EVALUATE_SYSTEM_PROMPT

    conversation_text = ""
    for i, record in enumerate(history, 1):
        role_name = "面试官" if record["role"] == "assistant" else "候选人"
        conversation_text += f"第{i}轮 {role_name}：{record['content']}\n\n"

    messages = [
        {"role": "system", "content": EVALUATE_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"面试岗位：{session.position}\n"
            f"面试风格：{session.style}\n"
            f"难度：{session.difficulty}\n\n"
            f"对话记录：\n{conversation_text}"
        )},
    ]

    def generate():
        """SSE 生成器，逐 token 返回评价内容。"""
        client = get_llm_client()
        full_response = ""

        try:
            for chunk in client.chat_stream(messages):
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except Exception:
            # LLM 不可用且还没有收到任何回复时，返回默认评价
            if not full_response:
                default = json.dumps({
                    "overall_score": 60.0,
                    "summary": "LLM 服务不可用，无法生成详细评价",
                    "dimensions": {"沟通表达": 60, "技术深度": 60, "逻辑思维": 60, "问题解决": 60},
                    "improvements": [],
                    "suggestions": "请配置 LLM_API_KEY 后重新评价",
                }, ensure_ascii=False)
                yield f"data: {json.dumps({'content': default})}\n\n"
                full_response = default

        # 解析完整响应，存入数据库（先检查是否已有评价，防止重复写入）
        existing = db.query(Evaluation).filter(Evaluation.session_id == session_id).first()
        if existing:
            yield f"data: {json.dumps({'done': True})}\n\n"
            return

        try:
            eval_data = json.loads(full_response)
            evaluation = Evaluation(
                session_id=session_id,
                overall_score=eval_data.get("overall_score", 60),
                summary=eval_data.get("summary", ""),
                dimensions=json.dumps(eval_data.get("dimensions", {}), ensure_ascii=False),
                improvements=json.dumps(eval_data.get("improvements", []), ensure_ascii=False),
                suggestions=eval_data.get("suggestions", ""),
            )
            db.add(evaluation)
            db.commit()
        except (json.JSONDecodeError, Exception):
            pass

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


@router.get("/{session_id}/detail")
def get_interview_detail(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取面试详情，包含对话记录和评价。

    返回会话信息、对话记录列表、评价信息（如果有）。
    """
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    ).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="面试会话不存在",
        )

    # 获取对话记录
    records = (
        db.query(ConversationRecord)
        .filter(ConversationRecord.session_id == session_id)
        .order_by(ConversationRecord.timestamp)
        .all()
    )

    # 获取评价（如果有）
    from src.models.evaluation import Evaluation
    evaluation = db.query(Evaluation).filter(
        Evaluation.session_id == session_id
    ).first()

    # 构建响应
    result = {
        "session": InterviewSessionResponse.from_orm(session).dict(),
        "conversations": [
            {
                "id": r.id,
                "role": r.role,
                "content": r.content,
                "timestamp": str(r.timestamp),
            }
            for r in records
        ],
        "evaluation": None,
    }

    if evaluation:
        result["evaluation"] = {
            "id": evaluation.id,
            "overall_score": evaluation.overall_score,
            "summary": evaluation.summary,
            "dimensions": json.loads(evaluation.dimensions),
            "improvements": json.loads(evaluation.improvements),
            "suggestions": evaluation.suggestions,
        }

    return result
