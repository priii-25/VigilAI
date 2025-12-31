"""
Configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Application
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str
    REDIS_URL: str
    
    # AI APIs
    GOOGLE_API_KEY: str
    
    # Vector Database
    # Vector Database
    VECTOR_DB_PATH: str = "./data/chromadb"
    
    # Integrations
    NOTION_API_KEY: str = ""
    NOTION_DATABASE_ID: str = ""
    SLACK_BOT_TOKEN: str = ""
    SLACK_SIGNING_SECRET: str = ""
    SLACK_CHANNEL_ID: str = ""
    SALESFORCE_CLIENT_ID: str = ""
    SALESFORCE_CLIENT_SECRET: str = ""
    SALESFORCE_USERNAME: str = ""
    SALESFORCE_PASSWORD: str = ""
    SALESFORCE_SECURITY_TOKEN: str = ""
    
    # Social Media APIs
    TWITTER_BEARER_TOKEN: str = ""
    LINKEDIN_ACCESS_TOKEN: str = ""
    
    # Review Data APIs (Optional)
    SERPAPI_KEY: str = ""
    
    # N8N
    N8N_HOST: str = "localhost"
    N8N_PORT: int = 5678
    N8N_WEBHOOK_URL: str = "http://localhost:5678/webhook"
    
    # Kafka (Optional)
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_SCRAPER_DATA: str = "scraper-data"
    KAFKA_TOPIC_SYSTEM_LOGS: str = "system-logs"
    
    # Proxy
    PROXY_POOL_ENABLED: bool = False
    PROXY_POOL_API_KEY: str = ""
    
    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Model Settings
    LOGBERT_MODEL_PATH: str = "./models/trained/logbert.pt"
    ANOMALY_THRESHOLD: float = 0.85
    
    # Monitoring
    SENTRY_DSN: str = ""
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        return [
            self.FRONTEND_URL,
            "http://localhost:3000",
            "http://localhost:8000",
        ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
