# AI面试器 - 执行计划

## 开发阶段

### 阶段 1：项目骨架 + 用户管理（Day 1）
**目标**：后端能跑起来，用户能注册登录

- 初始化 FastAPI 项目结构
- 配置 SQLAlchemy + SQLite
- 实现 User 表模型
- 实现注册 /api/register
- 实现登录 /api/login（JWT 鉴权）
- 初始化 Vue 3 + Element Plus 前端项目
- 前端：登录页面 + 注册页面

**交付物**：浏览器打开能注册、能登录、能拿到 token

### 阶段 2：简历管理（Day 2）
**目标**：用户能上传和查看简历

- 实现 Resume 表模型
- 实现 /api/resume/upload（文件上传 + 存本地）
- 实现 /api/resume/list（简历列表）
- 实现 LLM 封装层（LLMClient 抽象类）
- 实现简历解析（调 LLM 提取结构化信息）
- 前端：简历上传页面 + 简历列表

**交付物**：上传 PDF/图片，能看到列表，后端能解析简历内容

### 阶段 3：面试核心流程（Day 3-4）
**目标**：用户能完成一次完整的 AI 面试

- 实现 InterviewSession 表模型
- 实现 /api/interview/start（创建会话）
- 实现 /api/interview/{id}/message（发送用户消息）
- 实现 /api/interview/{id}/stream（SSE 流式返回 AI 回复）
- 实现 AI 面试官核心逻辑：
  - prompt 构建（简历+岗位+风格+难度+对话历史）
  - 0 式提问（新话题）和 1 式追问（基于上一回答，最多 3 轮）
- 实现 ConversationRecord 写入
- 前端：面试对话界面（聊天窗口 + 流式显示）

**交付物**：能发起面试、AI 提问、用户回答、AI 追问，完整走一轮

### 阶段 4：面试评价 + 历史记录（Day 5）
**目标**：面试结束后能看评价，能查历史

- 实现 /api/interview/{id}/end（结束面试 + 生成评价）
- 实现 Evaluation 表模型
- 实现评价生成 prompt（总体评价 + 维度评分 + 改进建议）
- 实现 /api/interview/list（历史记录列表，支持排序/搜索）
- 实现 /api/interview/{id}/detail（面试详情 + 评价）
- 前端：评价展示页面 + 历史记录列表页

**交付物**：面试结束后能看到评分和建议，历史记录可查

### 阶段 5：个人能力分析 + 收尾（Day 6-7）
**目标**：完整 MVP 上线

- 实现 /api/analysis/{user_id}（能力分析 + 趋势图 + 发展建议）
- 前端：个人能力分析页面（趋势图用 ECharts 或 Chart.js）
- 全流程联调测试
- 写 README.md
- 整理 Git 提交历史

**交付物**：完整可演示的 MVP

## 开发规范

- **TDD**：每个模块先写测试用例，再写实现（核心业务逻辑必须有测试）
- **Git 提交**：每个功能点一个 commit，message 写清楚做了什么
- **代码规范**：Python 用 black 格式化，前端用 ESLint
- **Commit message 格式**：`feat: 功能描述` / `fix: 修复描述` / `test: 测试描述`
