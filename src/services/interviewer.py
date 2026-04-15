"""AI 面试官服务。

负责构建面试 prompt、管理提问策略（新话题 / 追问）。
"""

from typing import Dict, List, Optional

from src.llm.factory import get_llm_client

# 面试风格对应的 prompt 策略
STYLE_PROMPTS = {
    "深度追问": (
        "你的面试风格是深度追问。针对候选人的回答，不断追问底层原理和实现细节。"
        "例如候选人说用了 Redis，你要追问 Redis 的数据结构、持久化机制、集群方案等。"
        "目标是探测候选人知识的深度边界。"
    ),
    "逻辑考察": (
        "你的面试风格是逻辑考察。提出开放性问题，要求候选人分析多种方案的优劣。"
        '例如"如何设计一个高并发秒杀系统"，要求候选人给出至少两种方案并对比。'
        "目标是考察候选人的系统思维和权衡能力。"
    ),
    "综合面试": (
        "你的面试风格是综合面试。结合技术深度和表达能力进行提问。"
        "既有技术细节追问，也有开放性设计问题。"
        "同时关注候选人的沟通表达是否清晰有条理。"
    ),
}

# 追问的最大轮数，超过后自动切换到新话题
MAX_FOLLOW_UP = 3


def build_system_prompt(
    position: str,
    style: str,
    difficulty: str,
    resume_text: str,
) -> str:
    """构建面试官的 system prompt。

    Args:
        position: 面试岗位
        style: 面试风格（深度追问/逻辑考察/综合面试）
        difficulty: 难度
        resume_text: 候选人简历文本

    Returns:
        拼装好的 system prompt
    """
    style_prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["综合面试"])

    return f"""你是一位专业的技术面试官，正在面试一位应聘「{position}」岗位的候选人。
难度等级：{difficulty}

{style_prompt}

候选人的简历信息：
{resume_text}

面试规则：
1. 每次只问一个问题
2. 问题要简洁明确，不超过 2 句话
3. 根据候选人的回答质量决定是追问还是切换话题
4. 追问不超过 3 轮后必须切换新话题
5. 不要评价候选人的回答好坏，直接提问
6. 用中文提问"""


def build_messages(
    system_prompt: str,
    conversation_history: List[Dict],
    user_message: Optional[str] = None,
) -> List[Dict]:
    """构建发给 LLM 的完整消息列表。

    Args:
        system_prompt: 系统 prompt
        conversation_history: 历史对话记录 [{"role": "user/assistant", "content": "..."}]
        user_message: 用户最新消息（可选，首轮提问时为空）

    Returns:
        完整的消息列表
    """
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    if user_message:
        messages.append({"role": "user", "content": user_message})
    return messages


def count_follow_ups(conversation_history: List[Dict]) -> int:
    """统计追问轮数。

    追问轮数 = assistant 消息总数 - 1（减去首次提问）。
    首次提问不算追问，之后每一轮都是追问。

    Args:
        conversation_history: 历史对话记录

    Returns:
        追问轮数
    """
    assistant_count = sum(1 for r in conversation_history if r["role"] == "assistant")
    # 首次提问不算追问，所以减 1
    return max(0, assistant_count - 1)


def generate_question(
    position: str,
    style: str,
    difficulty: str,
    resume_text: str,
    conversation_history: List[Dict],
    user_message: Optional[str] = None,
) -> str:
    """生成面试问题。

    首轮提问时 user_message 为空，AI 根据简历出题。
    后续轮次根据用户回答决定追问还是切换话题。

    Args:
        position: 面试岗位
        style: 面试风格
        difficulty: 难度
        resume_text: 简历文本
        conversation_history: 历史对话
        user_message: 用户最新消息

    Returns:
        AI 生成的面试问题
    """
    system_prompt = build_system_prompt(position, style, difficulty, resume_text)

    # 检查追问轮数，如果超过上限，在 prompt 中加入切换话题指令
    follow_up_count = count_follow_ups(conversation_history)
    if follow_up_count >= MAX_FOLLOW_UP and user_message:
        system_prompt += (
            "\n\n注意：你已经连续追问了 3 轮，现在必须切换到一个全新的话题。"
            "不要再追问当前话题的细节。"
        )

    messages = build_messages(system_prompt, conversation_history, user_message)
    client = get_llm_client()
    return client.chat(messages)
