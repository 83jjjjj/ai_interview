"""个人能力分析服务。

综合用户所有面试评价，调用 LLM 生成能力趋势分析和发展建议。
"""

import json
from typing import Dict, List

from pydantic import BaseModel

from src.llm.factory import get_llm_client


class AnalysisResult(BaseModel):
    """能力分析结果。"""
    total_interviews: int  # 总面试次数
    average_score: float  # 平均分
    dimension_trends: Dict[str, List[float]]  # 各维度的分数变化趋势
    strength: str  # 优势
    weakness: str  # 不足
    development_plan: str  # 发展建议


ANALYSIS_SYSTEM_PROMPT = """你是一位职业发展顾问。请根据候选人多次面试的评价数据，进行综合能力分析。

请严格按照以下 JSON 格式输出，不要输出其他内容：

{
    "strength": "候选人的核心优势（1-2 句话）",
    "weakness": "候选人最需要提升的方面（1-2 句话）",
    "development_plan": "具体的发展建议和学习路径（3-5 条，必须是字符串，不能是数组）"
}

评分标准：
- 90+：优秀
- 70-89：良好
- 60-69：合格
- 60 以下：不合格

要求：
1. 只输出 JSON，不要输出其他内容
2. 建议要具体可执行，不要泛泛而谈"""


def analyze_user(
    evaluations: List[Dict],
) -> AnalysisResult:
    """根据多次面试评价生成能力分析。

    Args:
        evaluations: 评价列表，每项包含 overall_score、dimensions、summary 等

    Returns:
        AnalysisResult 能力分析结果
    """
    if not evaluations:
        return AnalysisResult(
            total_interviews=0,
            average_score=0,
            dimension_trends={},
            strength="暂无数据",
            weakness="暂无数据",
            development_plan="请先完成至少一次面试",
        )

    # 计算基础统计
    total = len(evaluations)
    avg_score = sum(e["overall_score"] for e in evaluations) / total

    # 提取各维度的趋势数据
    all_dimension_names = set()
    for e in evaluations:
        all_dimension_names.update(e["dimensions"].keys())

    dimension_trends = {}
    for name in all_dimension_names:
        dimension_trends[name] = [
            e["dimensions"].get(name, 0) for e in evaluations
        ]

    # 构建 LLM 输入
    stats_text = f"总面试次数：{total}，平均分：{avg_score:.1f}\n\n"
    stats_text += "各维度分数趋势（按时间顺序）：\n"
    for name, scores in dimension_trends.items():
        stats_text += f"- {name}：{' → '.join(str(s) for s in scores)}\n"

    stats_text += "\n各次面试评价：\n"
    for i, e in enumerate(evaluations, 1):
        stats_text += f"第{i}次（{e['overall_score']}分）：{e['summary']}\n"

    messages = [
        {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
        {"role": "user", "content": stats_text},
    ]

    client = get_llm_client()
    try:
        raw_response = client.chat(messages)
        data = json.loads(raw_response)
        strength = data.get("strength", "暂无分析")
        weakness = data.get("weakness", "暂无分析")
        development_plan = data.get("development_plan", "暂无建议")
        # LLM 有时返回数组而非字符串，统一转成字符串
        if isinstance(development_plan, list):
            development_plan = "; ".join(development_plan)
    except Exception:
        strength = "分析服务暂不可用"
        weakness = "分析服务暂不可用"
        development_plan = "请稍后再试"

    return AnalysisResult(
        total_interviews=total,
        average_score=round(avg_score, 1),
        dimension_trends=dimension_trends,
        strength=strength,
        weakness=weakness,
        development_plan=development_plan,
    )
