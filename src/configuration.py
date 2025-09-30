import os
import logging
from pydantic import BaseModel, Field, model_validator
from keboola.component.exceptions import UserException


class Configuration(BaseModel):
    kbc_token: str = Field(default=None, alias="#kbc_token")
    kbc_url: str = Field(default=None, alias="kbc_url")
    branch_id: str = Field(default="default", alias="branch_id")

    # Migration parameters
    origin: str = Field(default=None, alias="origin")
    destination: str = Field(default=None, alias="destination")

    @model_validator(mode="before")
    def validate_kbc_credentials(cls, data):
        # Handle kbc_token
        env_token = os.environ.get("KBC_TOKEN")
        if env_token is not None:
            logging.info("Using KBC_TOKEN from environment.")
            data["#kbc_token"] = env_token
        elif data.get("#kbc_token") is not None:
            logging.info("Using KBC_TOKEN from config.")
        else:
            raise UserException("KBC_TOKEN environment variable is required")

        # Handle kbc_url
        env_url = os.environ.get("KBC_URL")
        if env_url is not None:
            logging.info("Using KBC_URL from environment.")
            data["kbc_url"] = env_url
        elif data.get("kbc_url") is not None:
            logging.info("Using KBC_URL from config.")
        else:
            raise UserException("KBC_URL environment variable is required")

        return data
