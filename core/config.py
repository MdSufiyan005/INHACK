from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_PREFIX:str = "/api"
    DEBUG: bool = False
    DATABASE_URL: str = Field(default="", validation_alias="DATABASE_URL")
    ALLOWED_ORIGINS: str = ""
    OPENAI_API_KEY: str = Field(default="", validation_alias="OPENAI_API_KEY")
    TWILIO_SID: str = Field(default="", validation_alias="TWILIO_SID")
    TWILIO_AUTH_TOKEN: str = Field(default="", validation_alias="TWILIO_AUTH_TOKEN")
    CELERY_BROKER_URL: str = Field(default="", validation_alias="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="", validation_alias="CELERY_RESULT_BACKEND")
    PHONE_NUMBER: str = Field(default="",validation_alias="PHONE_NUMBER")
    TIMEZONE:str = Field(default="UTC", validation_alias="TIMEZONE")
    GOOGLE_APPLICATION_CREDENTIALS: str = Field(default='', validation_alias="GOOGLE_APPLICATION_CREDENTIALS")
    GROQ_API_KEY:str = Field(default="", validation_alias="GROQ_API_KEY")
    
    @field_validator("ALLOWED_ORIGINS")
    def parse_allowed_origins(cls, v: str) -> List[str]:
        return v.split(',') if v else []

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

