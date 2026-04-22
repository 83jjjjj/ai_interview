"""个人能力分析 API 路由。"""

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.interview import InterviewSession
from src.models.evaluation import Evaluation
from src.models.user import User
from src.api.auth import get_current_user, get_current_user_for_sse
from src.services.analyzer import analyze_user

router = APIRouter(prefix="/api/analysis", tags=["分析"])


@router.get("")
def get_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的能力分析。

    查询该用户所有已完成的面试评价，调 LLM 生成趋势分析和发展建议。
    """
    evaluations = _get_evaluations(current_user.id, db)
    result = analyze_user(evaluations)
    return result.dict()


@router.get("/stream")
def analysis_stream(
    current_user: User = Depends(get_current_user_for_sse),
    db: Session = Depends(get_db),
):
    """SSE 流式生成能力分析。"""
    evaluations = _get_evaluations(current_user.id, db)

    if not evaluations:
        empty = json.dumps({
            "total_interviews": 0,
            "average_score": 0,
            "dimension_trends": {},
            "strength": "暂无数据",
            "weakness": "暂无数据",
            "development_plan": "请先完成至少一次面试",
        }, ensure_ascii=False)
        return StreamingResponse(
            iter([f"data: {json.dumps({'content': empty})}\n\ndata: {json.dumps({'done': True})}\n\n"]),
            media_type="text/event-stream",
        )

    # 计算基础统计
    total = len(evaluations)
    avg_score = sum(e["overall_score"] for e in evaluations) / total

    all_dimension_names = set()
    for e in evaluations:
        all_dimension_names.update(e["dimensions"].keys())
    dimension_trends = {}
    for name in all_dimension_names:
        dimension_trends[name] = [e["dimensions"].get(name, 0) for e in evaluations]

    # 构建 prompt
    stats_text = f"总面试次数：{total}，平均分：{avg_score:.1f}\n\n"
    stats_text += "各维度分数趋势（按时间顺序）：\n"
    for name, scores in dimension_trends.items():
        stats_text += f"- {name}：{' → '.join(str(s) for s in scores)}\n"
    stats_text += "\n各次面试评价：\n"
    for i, e in enumerate(evaluations, 1):
        stats_text += f"第{i}次（{e['overall_score']}分）：{e['summary']}\n"

    from src.services.analyzer import ANALYSIS_SYSTEM_PROMPT
    from src.llm.factory import get_llm_client

    messages = [
        {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
        {"role": "user", "content": stats_text},
    ]

    def generate():
        client = get_llm_client()
        full_response = ""

        try:
            for chunk in client.chat_stream(messages):
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except Exception:
            if not full_response:
                default = json.dumps({
                    "strength": "分析服务暂不可用",
                    "weakness": "分析服务暂不可用",
                    "development_plan": "请稍后再试",
                }, ensure_ascii=False)
                yield f"data: {json.dumps({'content': default})}\n\n"
                full_response = default

        # 发送统计数据和结束信号
        yield f"data: {json.dumps({'stats': {'total_interviews': total, 'average_score': round(avg_score, 1), 'dimension_trends': dimension_trends}})}\n\n"
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


def _get_evaluations(user_id: int, db: Session) -> list:
    """查询用户所有面试评价，返回字典列表。"""
    evaluations = (
        db.query(Evaluation)
        .join(InterviewSession, Evaluation.session_id == InterviewSession.id)
        .filter(InterviewSession.user_id == user_id)
        .order_by(Evaluation.created_at)
        .all()
    )
    return [
        {
            "overall_score": e.overall_score,
            "summary": e.summary,
            "dimensions": json.loads(e.dimensions),
            "improvements": json.loads(e.improvements),
            "suggestions": e.suggestions,
        }
        for e in evaluations
    ]
