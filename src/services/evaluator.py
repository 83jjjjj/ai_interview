"""面试评价服务。

调用 LLM 根据对话记录生成结构化评价。
"""

import json
from typing import Dict, List

from pydantic import BaseModel

from src.llm.factory import get_llm_client


class EvaluationResult(BaseModel):
    """评价结果的 Pydantic 模型，用于校验 LLM 输出。"""
    overall_score: float
    summary: str
    dimensions: Dict[str, float]  # {"沟通能力": 80, "技术深度": 75, ...}
    improvements: List[str]  # 最需改进的问答列表
    suggestions: str  # 改进建议


EVALUATE_SYSTEM_PROMPT = """你是一位专业的面试评价专家。请根据以下面试对话记录，对候选人进行综合评价。

请严格按照以下 JSON 格式输出，不要输出其他内容：

{
    "overall_score": 85.0,
    "summary": "一句话总体评价",
    "dimensions": {
        "沟通表达": 80.0,
        "技术深度": 75.0,
        "逻辑思维": 85.0,
        "问题解决": 80.0
    },
    "improvements": [
        "第X轮问答中，候选人对XXX的回答不够深入..."
    ],
    "suggestions": "针对以上不足的改进建议..."
}

评分标准（0-100）：
- 90+：优秀，超出岗位要求
- 70-89：良好，符合岗位要求
- 60-69：合格，基本符合要求
- 60以下：不合格，需要大幅提升

要求：
1. overall_score 是综合评分
2. dimensions 包含 4 个维度：沟通表达、技术深度、逻辑思维、问题解决
3. improvements 列出最需要改进的 1-3 个问答，简要说明问题
4. suggestions 给出具体的改进建议
5. 只输出 JSON，不要输出其他内容"""


def evaluate_interview(
    position: str,
    style: str,
    difficulty: str,
    conversation_history: List[Dict],
) -> EvaluationResult:
    """根据对话记录生成面试评价。

    Args:
        position: 面试岗位
        style: 面试风格
        difficulty: 难度
        conversation_history: 对话记录 [{"role": "user/assistant", "content": "..."}]

    Returns:
        EvaluationResult 结构化评价
    """
    client = get_llm_client()

    # 把对话记录格式化为可读文本
    conversation_text = ""
    for i, record in enumerate(conversation_history, 1):
        role_name = "面试官" if record["role"] == "assistant" else "候选人"
        conversation_text += f"第{i}轮 {role_name}：{record['content']}\n\n"

    messages = [
        {"role": "system", "content": EVALUATE_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"面试岗位：{position}\n"
            f"面试风格：{style}\n"
            f"难度：{difficulty}\n\n"
            f"对话记录：\n{conversation_text}"
        )},
    ]

    raw_response = client.chat(messages)

    try:
        data = json.loads(raw_response)
        return EvaluationResult(**data)
    except (json.JSONDecodeError, ValueError):
        # LLM 输出不是有效 JSON 时，返回默认评价
        return EvaluationResult(
            overall_score=60.0,
            summary="评价生成失败，请联系管理员",
            dimensions={"沟通表达": 60, "技术深度": 60, "逻辑思维": 60, "问题解决": 60},
            improvements=[],
            suggestions="无",
        )
