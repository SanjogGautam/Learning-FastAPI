from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict( # model_conifg tells to automatcially load values from .env file(.env file is for storing secret key which should not go inside source control)
        env_file=".env",
        env_file_encoding="utf-8"
    )

    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    max_upload_size_bytes: int = 5*1024*1024

settings = Settings()#loaded from the .env file 
#field names match environment variables name and is case insensitive 