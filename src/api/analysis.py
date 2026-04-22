"""个人能力分析 API 路由。"""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.interview import InterviewSession
from src.models.evaluation import Evaluation
from src.models.user import User
from src.api.auth import get_current_user
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
    # 查询该用户所有已评价的面试
    evaluations = (
        db.query(Evaluation)
        .join(InterviewSession, Evaluation.session_id == InterviewSession.id)
        .filter(InterviewSession.user_id == current_user.id)
        .order_by(Evaluation.created_at)
        .all()
    )

    # 转换为字典列表
    eval_list = []
    for e in evaluations:
        eval_list.append({
            "overall_score": e.overall_score,
            "summary": e.summary,
            "dimensions": json.loads(e.dimensions),
            "improvements": json.loads(e.improvements),
            "suggestions": e.suggestions,
        })

    # 调分析服务
    result = analyze_user(eval_list)

    return result.dict()
