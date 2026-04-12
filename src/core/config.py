"""全局配置管理。

所有配置项从环境变量或 .env 文件读取，修改配置只需改 .env，不用改代码。
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """项目配置，优先从环境变量读取，其次从 .env 文件，最后使用默认值。"""

    # 数据库：开发用 SQLite，部署时改为 PostgreSQL 连接串即可
    DATABASE_URL: str = "sqlite:///./ai_interview.db"

    # JWT 配置：生产环境必须替换 SECRET_KEY
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # token 有效期 24 小时

    # LLM 配置：默认通义千问（兼容 OpenAI 格式），切模型只需改这三个值
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "qwen-plus"

    class Config:
        env_file = ".env"


# 全局单例，其他模块直接 from src.core.config import settings 使用
settings = Settings()
