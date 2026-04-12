# AI面试器 - 技术选型

## 技术栈总览

| 组件 | 选型 | 备注 |
|------|------|------|
| 后端框架 | FastAPI | async + SSE 原生支持 |
| 前端框架 | Vue 3 | 上手快，中文生态好 |
| UI 组件库 | Element Plus | Vue 3 生态最成熟 |
| 数据库 | SQLite（开发）→ PostgreSQL（部署） | SQLAlchemy 兼容，改配置即可 |
| ORM | SQLAlchemy | Python 数据库操作标准，FastAPI 推荐搭配 |
| 大模型 | 抽象层封装，随时切换 | 开发阶段用通义千问（便宜直连） |
| 实时通信 | SSE | 流式输出，FastAPI 原生支持 |
| 文件存储 | 本地文件系统（开发）→ 云存储（部署） | 存路径到数据库 |
| 密码加密 | bcrypt | 用户密码安全存储 |

## 选型理由

### 后端：FastAPI
- 原生 async，适合"用户发消息 → 调 LLM → 流式返回"场景
- 自带 SSE 支持，不需要额外引入库
- 自动生成 Swagger API 文档，方便调试

### 前端：Vue 3 + Element Plus
- Vue 模板语法接近 HTML，上手成本低
- Element Plus 提供现成的登录表单、表格、对话框等组件
- 一周 MVP 不在前端 CSS 上花时间

### 数据库：SQLite → PostgreSQL
- 开发阶段用 SQLite，零配置，文件即数据库
- 部署时切 PostgreSQL，只改连接配置，代码不用动
- SQLAlchemy ORM 同时兼容两者

### 大模型：抽象层封装
- 统一接口 `LLMClient.chat(messages, stream=True)`，底层实现可替换
- 开发阶段用通义千问：国内直连、中文最好、价格便宜
- 不绑定具体模型，后续可随时切换

### 实时通信：SSE
- 项目通信模式是"用户发消息（POST）→ AI 流式回复（SSE）"，不需要双向 WebSocket
- FastAPI 原生支持，浏览器 EventSource API 自动处理断线重连
- 后续扩展视频通话时再引入 WebSocket

### 文件存储：本地 → 云存储
- MVP 阶段文件存本地 `uploads/` 目录，数据库存路径
- 上线时切云存储，只改文件读写封装层

## 未选型（后续扩展）

- WebSocket（语音/视频通话需要时引入）
- 云存储服务（部署时确定具体服务商）
