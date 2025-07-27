from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    """Uygulama ayarları"""
    
    # Database
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "talentmatch"
    
    # Security
    secret_key: str = "super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Email
    email_host: str = "smtp.gmail.com"
    email_port: int = 587
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    
    # SMS
    sms_api_key: Optional[str] = None
    sms_password: Optional[str] = None
    sms_api_url: str = "https://api.netgsm.com.tr/sms/send/get"
    sms_sender_name: str = "TalentMatch"
    
    # File upload
    upload_dir: str = "./uploads"
    max_file_size: int = 10485760  # 10MB
    allowed_extensions: list = [".pdf", ".docx", ".doc"]
    
    # NLP Models
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    spacy_model_tr: str = "tr_core_news_lg"
    spacy_model_en: str = "en_core_web_lg"
    
    # FAISS
    faiss_index_path: str = "./data/faiss_index.bin"
    faiss_dimension: int = 384  # MiniLM embedding dimension
    
    # GDPR
    data_retention_days: int = 30
    anonymize_after_days: int = 365
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
