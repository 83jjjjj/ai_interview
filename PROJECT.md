# AI 面试器

基于 LLM 的模拟面试平台，用户上传简历后可发起 AI 面试，面试结束后自动生成评价和能力分析。

## 功能

- **用户系统**：注册、登录、JWT 鉴权
- **简历管理**：上传 PDF/图片，AI 自动解析为结构化信息
- **AI 面试**：基于简历和岗位提问，支持流式输出、追问、话题切换
- **面试评价**：面试结束后 AI 生成多维度评分 + 改进建议
- **历史记录**：查看所有面试记录和详情
- **能力分析**：综合多次面试评价，生成能力趋势和发展建议

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Python 3.8 + FastAPI + SQLAlchemy + SQLite |
| 前端 | Vue 3 + Element Plus + ECharts + Vite |
| LLM | OpenAI 兼容格式（通义千问/任意兼容模型） |
| 测试 | pytest（80 个测试） |

## 快速启动

```bash
# 后端
cd ~/ai_interview
# 可选：配置 LLM API
# echo 'LLM_API_KEY=your-key' > .env
# echo 'LLM_BASE_URL=http://your-api-base/v1' >> .env
# echo 'LLM_MODEL=your-model' >> .env
python3 -m uvicorn src.main:app --port 9000 --reload

# 前端（新终端）
cd ~/ai_interview/frontend
npm run dev
```

打开 http://localhost:5173

## 测试

```bash
cd ~/ai_interview
python3 -m pytest tests/ -v
```

## 目录结构

```
ai_interview/
├── src/
│   ├── main.py              # FastAPI 入口
│   ├── core/                # 配置、数据库
│   │   ├── config.py        # Settings（从 .env 读取）
│   │   └── database.py      # SQLAlchemy engine + get_db
│   ├── models/              # ORM 模型
│   │   ├── user.py          # User 表
│   │   ├── resume.py        # Resume 表
│   │   ├── interview.py     # InterviewSession + ConversationRecord 表
│   │   └── evaluation.py    # Evaluation 表
│   ├── api/                 # API 路由
│   │   ├── auth.py          # 注册/登录/鉴权
│   │   ├── resume.py        # 简历上传/列表
│   │   ├── interview.py     # 面试 CRUD + SSE 流式
│   │   ├── analysis.py      # 能力分析
│   │   └── schemas.py       # Pydantic 请求/响应模型
│   ├── services/            # 业务逻辑
│   │   ├── resume_parser.py # 简历解析（调 LLM）
│   │   ├── interviewer.py   # AI 面试官 prompt + 提问策略
│   │   ├── evaluator.py     # 面试评价生成
│   │   └── analyzer.py      # 能力趋势分析
│   └── llm/                 # LLM 抽象层
│       ├── base.py          # LLMClientBase 抽象基类
│       ├── qwen.py          # 通义千问适配器
│       └── factory.py       # 工厂函数（单例）
├── tests/                   # pytest 测试（80 个）
├── frontend/
│   └── src/
│       ├── views/           # 页面组件
│       │   ├── LoginView.vue
│       │   ├── RegisterView.vue
│       │   ├── HomeView.vue
│       │   ├── ResumeView.vue
│       │   ├── InterviewConfigView.vue
│       │   ├── InterviewView.vue
│       │   ├── EvaluationView.vue
│       │   ├── HistoryView.vue
│       │   └── AnalysisView.vue
│       ├── router/index.js  # 路由 + 鉴权守卫
│       └── api/index.js     # axios 封装（自动带 token）
├── plan/                    # 设计文档
├── tasks/                   # 任务拆分（18 个）
└── PROJECT.md
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/register | 注册 |
| POST | /api/login | 登录 |
| GET | /api/me | 当前用户信息 |
| POST | /api/resume/upload | 上传简历 |
| GET | /api/resume/list | 简历列表 |
| POST | /api/interview/start | 创建面试 |
| POST | /api/interview/{id}/message | 发送消息 |
| GET | /api/interview/{id}/stream | AI 回复（SSE） |
| POST | /api/interview/{id}/end | 结束面试 |
| GET | /api/interview/{id}/evaluation-stream | 评价生成（SSE） |
| GET | /api/interview/list | 面试列表 |
| GET | /api/interview/{id}/detail | 面试详情 |
| GET | /api/analysis | 能力分析 |
