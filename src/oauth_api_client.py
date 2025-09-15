"""
OAuth API Client for Keboola OAuth service.

Provides methods for managing OAuth credentials.
"""

import json
import logging
import requests
from typing import Dict, Any

from keboola.component.exceptions import UserException


class OAuthApiClient:
    """
    Client for Keboola OAuth API
    Base URL: https://oauth.keboola.com
    """

    def __init__(self, token: str):
        """
        Initialize OAuth API client

        Args:
            token (str): Storage API token for authentication
        """
        self.base_url = "https://oauth.keboola.com"
        self.token = token
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-StorageApi-Token": token,
        }

    def get_credentials_detail(self, component_id: str, name: str) -> Dict[str, Any]:
        """
        Get OAuth credentials detail
        GET /credentials/{componentId}/{name}

        Args:
            component_id (str): Component ID
            name (str): Credentials name (ID)

        Returns:
            dict: Credentials detail response

        Raises:
            UserException: If the API request fails
        """
        try:
            url = f"{self.base_url}/credentials/{component_id}/{name}"

            logging.info(f"Getting OAuth credentials detail for {component_id}/{name}")
            response = requests.get(url, headers=self.headers)

            if response.status_code >= 400:
                error_msg = f"OAuth API request failed with status {response.status_code}: {response.text}"
                logging.error(error_msg)
                response.raise_for_status()

            credentials = response.json()
            logging.info(
                f"Successfully retrieved credentials for {component_id}/{name}"
            )
            return credentials

        except Exception as e:
            logging.error(f"Error getting OAuth credentials: {str(e)}")
            raise UserException(f"Failed to get OAuth credentials: {str(e)}")

    def create_credentials(
        self,
        component_id: str,
        credentials_id: str,
        authorized_for: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create OAuth credentials
        POST /credentials/{componentId}

        Args:
            component_id (str): Component ID
            credentials_id (str): ID/name for the credentials
            authorized_for (str): Email of KBC user who performed authorization
            data (dict): OAuth data (access_token, refresh_token, etc.)

        Returns:
            dict: Created credentials response

        Raises:
            UserException: If the API request fails
        """
        try:
            url = f"{self.base_url}/credentials/{component_id}"

            # Prepare request body according to API documentation
            body = {"id": credentials_id, "authorizedFor": authorized_for, "data": data}

            logging.info(f"Creating OAuth credentials for {component_id}")
            logging.info(f"Request body: {json.dumps(body, indent=2)}")

            response = requests.post(url, json=body, headers=self.headers)

            if response.status_code >= 400:
                error_msg = f"OAuth API request failed with status {response.status_code}: {response.text}"
                logging.error(error_msg)
                response.raise_for_status()

            created_credentials = response.json()
            logging.info(
                f"Successfully created credentials {credentials_id} for {component_id}"
            )
            return created_credentials

        except Exception as e:
            logging.error(f"Error creating OAuth credentials: {str(e)}")
            raise UserException(f"Failed to create OAuth credentials: {str(e)}")
