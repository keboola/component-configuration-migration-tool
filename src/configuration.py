from pydantic import BaseModel, Field


class Configuration(BaseModel):
    kbc_token: str = Field(default=None, alias="#kbc_token")
    kbc_url: str = Field(default=None, alias="kbc_url")
    branch_id: str = Field(default="default", alias="branch_id")
