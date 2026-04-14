# task-013: 实现面试评价生成

## 描述
面试结束后调 LLM 生成评价，存储并关联到会话。

## 具体内容
- 创建 Evaluation 模型（id / session_id / overall_score / summary / dimensions / improvements / suggestions / created_at）
- 写评价 prompt 构建服务（总体评价 + 维度评分 + 改进建议，结构化 JSON 输出）
- 写评价 prompt 测试用例（输入模拟对话，输出格式为 JSON 且包含必填字段）
- 实现 POST /api/interview/{id}/end（收集对话 → 调 LLM 生成评价 → 写入 Evaluation → 更新 session status=已完成）
- 写结束面试测试用例（正常结束 / 会话不存在 / 重复结束）
- 跑测试确认通过

## 验收标准
- pytest 测试通过
- 结束面试后 Evaluation 表有记录，包含 overall_score / summary / dimensions / improvements
- session status 变为已完成

## 依赖
task-005, task-009
