# AI面试器 - 架构设计

## 系统架构

```
前端（Vue 3 + Element Plus）
    ↓ HTTP / SSE
后端（FastAPI）
    ├── 用户管理模块
    ├── 面试功能模块
    ├── 面试通信模块（SSE 流式输出）
    ├── AI面试官模块（调 LLM API）
    ├── 面试记录与评价模块
    └── 个人能力分析模块
    ↓
数据库（SQLite 开发 / PostgreSQL 部署）
文件存储（本地开发 / 云存储部署）
LLM API（抽象层封装，可替换）
```

## 数据库表结构

### User
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| username | VARCHAR | 用户名，唯一 |
| email | VARCHAR | 邮箱，唯一 |
| password_hash | VARCHAR | bcrypt 加密后的密码 |
| created_at | DATETIME | 注册时间 |

### Resume
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| user_id | INTEGER FK | 关联 User |
| filename | VARCHAR | 原始文件名 |
| file_path | VARCHAR | 存储路径 |
| parsed_content | TEXT | AI 解析后的简历文本 |
| created_at | DATETIME | 上传时间 |

### InterviewSession
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| user_id | INTEGER FK | 关联 User |
| resume_id | INTEGER FK | 关联 Resume |
| position | VARCHAR | 面试岗位 |
| style | VARCHAR | 面试风格 |
| difficulty | VARCHAR | 难度 |
| status | VARCHAR | 进行中/已完成/中断 |
| created_at | DATETIME | 开始时间 |
| ended_at | DATETIME | 结束时间 |

### ConversationRecord
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| session_id | INTEGER FK | 关联 InterviewSession |
| role | VARCHAR | user / assistant |
| content | TEXT | 对话内容 |
| timestamp | DATETIME | 发送时间 |

### Evaluation
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| session_id | INTEGER FK | 关联 InterviewSession，一对一 |
| overall_score | FLOAT | 总体评分 |
| summary | TEXT | 总体评价 |
| dimensions | JSON | 各维度评分（沟通/技术/逻辑等） |
| improvements | JSON | 最需改进的 3 条问答 |
| suggestions | TEXT | 改进建议 |
| created_at | DATETIME | 生成时间 |

## 模块间数据流

```
用户上传简历
    → 面试功能模块 接收文件 → 存入文件系统 + 写入 Resume 表
    → AI面试官模块 解析简历 → 更新 Resume.parsed_content

用户发起面试
    → 面试功能模块 创建 InterviewSession（状态=进行中）

面试对话（循环）
    → 面试通信模块 接收用户文字
    → AI面试官模块 读取上下文（简历+岗位+历史对话）→ 调 LLM → 返回问题
    → 面试通信模块 流式返回给前端
    → 面试记录与评价模块 写入 ConversationRecord（user + assistant 各一条）

面试结束
    → 面试记录与评价模块 收集全部对话 → 调 LLM 生成评价
    → 写入 Evaluation 表 + 更新 InterviewSession.status=已完成

用户查看历史
    → 面试功能模块 查询 InterviewSession 列表
    → 需要评价时关联 Evaluation 表

个人能力分析
    → 个人能力分析模块 查某用户所有 Evaluation
    → 调 LLM 生成趋势分析 + 发展建议
```

## 前后端 API 接口

| 方法 | 路径 | 说明 | 模块 |
|------|------|------|------|
| POST | /api/register | 注册 | 用户管理 |
| POST | /api/login | 登录 | 用户管理 |
| POST | /api/resume/upload | 上传简历 | 面试功能 |
| GET | /api/resume/list | 简历列表 | 面试功能 |
| POST | /api/interview/start | 发起面试 | 面试功能 |
| POST | /api/interview/{id}/message | 发送消息 | 面试通信 |
| GET | /api/interview/{id}/stream | AI 流式回复（SSE） | 面试通信 |
| POST | /api/interview/{id}/end | 结束面试 | 面试记录与评价 |
| GET | /api/interview/list | 历史记录列表 | 面试功能 |
| GET | /api/interview/{id}/detail | 面试详情（含评价） | 面试功能 |
| GET | /api/analysis/{user_id} | 个人能力分析 | 个人能力分析 |
