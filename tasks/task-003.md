# task-003: 实现登录接口 + JWT 鉴权

## 描述
实现用户登录，返回 JWT token，实现鉴权中间件。

## 具体内容
- 写登录接口测试用例（正确登录 / 密码错误 / 用户不存在）
- 实现 POST /api/login 接口（验证密码，返回 JWT）
- 写鉴权中间件测试用例（带 token 访问 / 不带 token / 过期 token）
- 实现 JWT 鉴权中间件（解析 token，注入当前用户）
- 实现 GET /api/me 接口（返回当前用户信息，用于测试鉴权）
- 跑测试确认通过

## 验收标准
- pytest 测试通过
- 登录返回 JWT token
- 带 token 能访问 /api/me，不带 token 返回 401

## 依赖
task-002
