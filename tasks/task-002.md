# task-002: 实现 User 模型 + 注册接口

## 描述
创建用户数据模型，实现注册接口。

## 具体内容
- 写 User 模型测试用例（字段完整性、唯一约束）
- 创建 User SQLAlchemy 模型（id / username / email / password_hash / created_at）
- 实现密码加密工具函数（bcrypt）
- 实现 POST /api/register 接口
- 写注册接口测试用例（正常注册 / 用户名重复 / 邮箱重复 / 缺字段）
- 实现注册接口逻辑
- 跑测试确认通过

## 验收标准
- pytest 测试通过
- 调用 /api/register 能创建用户，密码是 bcrypt 哈希
- 重复注册返回错误

## 依赖
task-001
