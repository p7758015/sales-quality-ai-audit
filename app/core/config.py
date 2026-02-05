from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    model_name: str = "gpt-4o-mini"
    chunk_size: int = 512   # было 1024
    chunk_overlap: int = 0
    temperature: float = 0.0
    num_fragment: int = 3   # было 6

    class Config:
        env_file = ".env"

settings = Settings()
