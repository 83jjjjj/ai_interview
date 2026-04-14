"""简历解析服务。

调用 LLM 将简历文本解析为结构化信息。
输入：简历的原始文本内容
输出：结构化的 Pydantic 模型（JSON 格式）
"""

import json
from typing import List, Optional

from pydantic import BaseModel

from src.llm.factory import get_llm_client


class WorkExperience(BaseModel):
    """工作经历。"""
    company: str  # 公司名称
    position: str  # 职位
    duration: str  # 时间段
    responsibilities: str  # 主要职责


class Education(BaseModel):
    """教育背景。"""
    school: str  # 学校
    degree: str  # 学位
    major: str  # 专业
    duration: str  # 时间段


class ResumeInfo(BaseModel):
    """简历解析结果，所有字段用结构化 Pydantic 模型定义。"""
    name: str = "未提供"
    email: str = "未提供"
    phone: str = "未提供"
    education: List[Education] = []
    work_experience: List[WorkExperience] = []
    skills: List[str] = []
    summary: str = "未提供"


# 要求 LLM 输出 JSON 格式，配合 ResumeInfo 模型使用
PARSE_SYSTEM_PROMPT = """你是一个简历解析专家。请从用户提供的简历文本中提取结构化信息，严格按照以下 JSON 格式输出：

{
    "name": "姓名",
    "email": "邮箱",
    "phone": "电话",
    "education": [
        {"school": "学校", "degree": "学位", "major": "专业", "duration": "时间段"}
    ],
    "work_experience": [
        {"company": "公司", "position": "职位", "duration": "时间段", "responsibilities": "主要职责"}
    ],
    "skills": ["技能1", "技能2"],
    "summary": "一句话总结"
}

要求：
1. 只输出 JSON，不要输出其他内容
2. 如果简历中没有某项信息，用"未提供"
3. 保持原文信息，不要编造"""


def parse_resume(raw_text: str) -> ResumeInfo:
    """调用 LLM 解析简历文本，返回结构化结果。

    Args:
        raw_text: 简历的原始文本内容

    Returns:
        结构化的 ResumeInfo 模型实例
    """
    client = get_llm_client()

    messages = [
        {"role": "system", "content": PARSE_SYSTEM_PROMPT},
        {"role": "user", "content": f"请解析以下简历内容：\n\n{raw_text}"},
    ]

    raw_response = client.chat(messages)

    # 用 Pydantic 校验 LLM 返回的 JSON，字段缺失或类型错误会自动报错
    try:
        data = json.loads(raw_response)
        return ResumeInfo(**data)
    except (json.JSONDecodeError, ValueError):
        # LLM 输出不是有效 JSON 时，返回默认值
        return ResumeInfo()
