# task-006: 实现简历上传接口

## 描述
实现简历文件上传和存储。

## 具体内容
- 创建 Resume SQLAlchemy 模型（id / user_id / filename / file_path / parsed_content / created_at）
- 写简历模型测试用例
- 实现 POST /api/resume/upload（文件上传，存本地 uploads/ 目录）
- 写上传接口测试用例（PDF 上传 / 图片上传 / 格式不支持）
- 实现 GET /api/resume/list（当前用户的简历列表）
- 写列表查询测试用例
- 跑测试确认通过

## 验收标准
- pytest 测试通过
- 上传 PDF/图片后能在列表看到记录
- 不支持的格式返回错误

## 依赖
task-003
