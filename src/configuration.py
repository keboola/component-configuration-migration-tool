import os
from pydantic import BaseModel, Field, field_validator


class Configuration(BaseModel):
    kbc_token: str = Field(default=None, alias="#kbc_token")
    kbc_url: str = Field(default=None, alias="kbc_url")
    branch_id: str = Field(default="default", alias="branch_id")

    @field_validator('kbc_token', mode='before')
    @classmethod
    def validate_kbc_token(cls, v):
        # Prioritize environment variable over config value
        env_token = os.environ.get('KBC_TOKEN')
        if env_token is not None:
            return env_token
        if v is not None:
            return v
        raise ValueError("KBC_TOKEN environment variable is required")

    @field_validator('kbc_url', mode='before')
    @classmethod
    def validate_kbc_url(cls, v):
        # Prioritize environment variable over config value
        env_url = os.environ.get('KBC_URL')
        if env_url is not None:
            return env_url
        if v is not None:
            return v
        raise ValueError("KBC_URL environment variable is required")

    @field_validator('branch_id', mode='before')
    @classmethod
    def validate_branch_id(cls, v):
        # If parameter exists in config, use it; otherwise set default value
        if v is not None:
            return v
        return "default"
