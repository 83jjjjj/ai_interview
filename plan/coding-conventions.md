# AI面试器 - 编码规范

## 命名规范

- 变量/函数：蛇形命名 `user_name`、`get_user_by_id`
- 类名：大驼峰 `UserService`、`InterviewSession`
- 常量：全大写下划线 `MAX_RETRY_COUNT`
- 私有成员：前导下划线 `_internal_method`
- 名字要表达意图，`active_sessions` 优于 `data`

## 注释原则

### 不要写的注释
- 显而易见的代码不要注释（如 `user.name = name  # 设置用户名`）

### 必须写的注释
- "为什么这么做"而不是"做了什么"
  ```python
  # 追问最多 3 轮后必须切换话题，防止 AI 陷入死循环追问
  if follow_up_count >= MAX_FOLLOW_UP:
  ```
- 复杂逻辑或非直觉决策
  ```python
  # 用消息列表而不是单条 prompt，因为 API 要求区分 system/user/assistant 角色
  messages = [{"role": "system", "content": system_prompt}, ...]
  ```
- 函数/类必须有 docstring（说明功能、参数、返回值）

## 类型标注

所有函数参数和返回值必须有类型标注：
```python
from typing import Optional

def get_user(db: Session, user_id: int) -> Optional[User]:
```

## 代码组织

- 一个文件只做一件事
- 函数不超过 30 行，超过就拆
- import 顺序：标准库 → 第三方 → 项目内部，组间空行分隔

## 代码格式

- Python 用 black 格式化
- 前端用 ESLint
- 缩进统一 4 空格（Python）/ 2 空格（Vue/CSS）

## 测试规范

- 测试基础设施（conftest.py、fixture）写完后先跑一个 trivial 测试验证能工作，再写正式测试用例
- SQLite 内存数据库测试必须用 `StaticPool`，否则每个连接看到的是独立的空数据库：
  ```python
  from sqlalchemy.pool import StaticPool
  TEST_ENGINE = create_engine("sqlite:///:memory:", poolclass=StaticPool, ...)
  ```
- 测试数据库用内存模式（`:memory:`），不污染开发数据库
