from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./app.db"
    
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    api_v1_str: str = "/api/v1"
    project_name: str = "FastAPI Backend"
    
    github_api_url: str = "https://api.github.com"
    jira_api_url: str = "https://your-domain.atlassian.net"

    openrouter_api_key: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()
