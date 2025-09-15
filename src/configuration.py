import os
from pydantic import BaseModel, Field, field_validator


class Configuration(BaseModel):
    kbc_token: str = Field(alias="#kbc_token")
    kbc_url: str = Field(alias="kbc_url")
    branch_id: str = Field(alias="branch_id")

    @field_validator('kbc_token', mode='before')
    @classmethod
    def validate_kbc_token(cls, v):
        # Prioritize environment variable over config value
        env_token = os.environ.get('KBC_TOKEN')
        if env_token is not None:
            return env_token
        return v

    @field_validator('kbc_url', mode='before')
    @classmethod
    def validate_kbc_url(cls, v):
        # Prioritize environment variable over config value
        env_url = os.environ.get('KBC_URL')
        if env_url is not None:
            return env_url
        return v

    @field_validator('branch_id', mode='before')
    @classmethod
    def validate_branch_id(cls, v):
        # If parameter exists in config, use it; otherwise set default value
        if v is not None:
            return v
        return "default"
