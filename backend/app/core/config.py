"""Application configuration management"""

from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # ===== Service Configuration =====
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    PROJECT_NAME: str = "AI Travel Planner API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "基于AG-UI协议的AI旅行规划师后端服务"
    
    # ===== Database Configuration =====
    DATABASE_URL: str
    
    # ===== Redis Configuration =====
    REDIS_URL: str
    
    # ===== JWT Configuration =====
    SECRET_KEY: str  # 至少32字符，生产环境必须更改
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days
    
    # ===== Third-party APIs =====
    # 阿里云百炼平台
    ALIYUN_LLM_API_KEY: str = ""
    ALIYUN_LLM_ENDPOINT: str = "https://dashscope.aliyuncs.com/api/v1"
    
    # 科大讯飞
    XFYUN_APP_ID: str = ""
    XFYUN_API_KEY: str = ""
    XFYUN_API_SECRET: str = ""
    
    # 百度地图
    BAIDU_MAP_AK: str = ""
    BAIDU_MAP_SK: str = ""
    
    # ===== CORS Configuration =====
    CORS_ORIGINS: str = '["http://localhost:5173","http://localhost:3000"]'
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from JSON string"""
        try:
            return json.loads(self.CORS_ORIGINS)
        except json.JSONDecodeError:
            return ["http://localhost:5173"]
    
    # ===== Logging Configuration =====
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()

