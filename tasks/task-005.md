# task-005: 实现 LLM 调用封装层

## 描述
创建统一的 LLM 调用抽象层，支持流式输出，可替换底层实现。

## 具体内容
- 设计 LLMClient 抽象接口（chat / chat_stream）
- 写接口测试用例（模拟调用，验证参数格式）
- 实现通义千问适配器（OpenAI 兼容格式）
- 实现流式输出支持（yield 逐块返回）
- 配置 API key 管理（环境变量）
- 跑测试确认接口可用

## 验收标准
- pytest 测试通过
- 调用 chat_stream 能逐块收到响应
- 换 API key / base_url 即可切换模型

## 依赖
task-001
