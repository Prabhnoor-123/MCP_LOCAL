from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_KEY_LLM: str
    AZURE_OPENAI_API_VERSION_LLM: str

    model_config = ConfigDict(env_file=".env")

settings = Settings()