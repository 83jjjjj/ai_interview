# task-009: 实现面试会话创建 + 消息发送

## 描述
实现面试会话的创建和用户消息的接收存储。

## 具体内容
- 创建 InterviewSession 模型（id / user_id / resume_id / position / style / difficulty / status / created_at / ended_at）
- 创建 ConversationRecord 模型（id / session_id / role / content / timestamp）
- 写模型测试用例
- 实现 POST /api/interview/start（创建会话，关联简历和岗位配置）
- 写创建会话测试用例（正常创建 / 简历不存在 / 缺字段）
- 实现 POST /api/interview/{id}/message（接收用户消息，存入 ConversationRecord）
- 写消息发送测试用例（正常发送 / 会话不存在 / 会话已结束）
- 跑测试确认通过

## 验收标准
- pytest 测试通过
- 创建会话后 status=进行中
- 发送消息后 ConversationRecord 中有 user 角色记录

## 依赖
task-003, task-006
