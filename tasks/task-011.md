# task-011: 实现 SSE 流式回复接口

## 描述
实现面试对话的 SSE 流式输出，将 AI 回复存储到对话记录。

## 具体内容
- 实现 GET /api/interview/{id}/stream（SSE 流式返回 AI 回复）
- 集成面试官提问逻辑，调 LLM 流式输出
- 将完整 AI 回复存入 ConversationRecord（role=assistant）
- 写 SSE 接口测试用例（验证返回 event-stream 格式）
- 跑测试确认通过

## 验收标准
- pytest 测试通过
- stream 接口返回 SSE 格式数据
- AI 回复完整存入 ConversationRecord

## 依赖
task-010
