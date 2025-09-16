"""
Template Component main class.

"""

import logging

from keboola.component.base import ComponentBase
from keboola.component.exceptions import UserException
from kbcstorage.client import Client

from configuration import Configuration
from oauth_api_client import OAuthApiClient


class Component(ComponentBase):
    """
    Extends base class for general Python components. Initializes the CommonInterface
    and performs configuration validation.

    For easier debugging the data folder is picked up by default from `../data` path,
    relative to working directory.

    If `debug` parameter is present in the `config.json`, the default logger is set to verbose DEBUG mode.
    """

    def __init__(self):
        super().__init__()
        self.config = Configuration(**self.configuration.parameters)
        logging.info(f"KBC URL: {self.config.kbc_url}")
        self.storage_api_client = Client(
            self.config.kbc_url, self.config.kbc_token, branch_id=self.config.branch_id
        )
        self.oauth_api_client = OAuthApiClient(self.config.kbc_token)

    def copy_configuration(
        self,
        source_component_id,
        source_config_id,
        target_component_id,
        target_config_name=None,
    ):
        """
        Copy configuration from source component to target component

        Args:
            source_component_id (str): Source component ID
            source_config_id (str): Source configuration ID
            target_component_id (str): Target component ID
            target_config_name (str, optional): Name for new configuration.
                If None, uses source config name with suffix

        Returns:
            dict: Created configuration details
        """
        try:
            # Get source configuration
            logging.info(
                f"Getting configuration {source_config_id} from component {source_component_id}"
            )
            source_config = self.storage_api_client.configurations.detail(
                component_id=source_component_id, configuration_id=source_config_id
            )

            # Step 1: Prepare configuration with replaced authorization
            target_configuration = source_config.get("configuration", {}).copy()

            # Replace oauth_api section with oauth_credentials from current configuration
            if (
                hasattr(self.configuration, "oauth_credentials")
                and self.configuration.oauth_credentials
            ):
                # Convert OauthCredentials object to dict for JSON serialization
                oauth_creds = self.configuration.oauth_credentials
                if hasattr(oauth_creds, "dict"):
                    # If it's a Pydantic model, use .dict() method
                    oauth_dict = oauth_creds.dict()
                elif hasattr(oauth_creds, "__dict__"):
                    # If it's a regular object, use __dict__
                    oauth_dict = oauth_creds.__dict__
                else:
                    # If it's already a dict
                    oauth_dict = oauth_creds

                # Ensure # prefixes are preserved for sensitive fields and convert to strings
                if isinstance(oauth_dict, dict):
                    oauth_dict_fixed = {}
                    for key, value in oauth_dict.items():
                        if key in ["data", "appSecret"] and not key.startswith("#"):
                            # Add # prefix for sensitive fields and ensure it's a string
                            oauth_dict_fixed[f"#{key}"] = (
                                str(value) if value is not None else ""
                            )
                        else:
                            oauth_dict_fixed[key] = value
                    oauth_dict = oauth_dict_fixed

                # Ensure authorization section exists
                if "authorization" not in target_configuration:
                    target_configuration["authorization"] = {}

                # Replace only oauth_api section
                target_configuration["authorization"]["oauth_api"] = oauth_dict

                logging.info(
                    "Replaced oauth_api section with oauth_credentials from current configuration"
                )
            else:
                logging.warning("No oauth_credentials found in current configuration")

            # Step 2: Encrypt configuration using Keboola Encryption API
            encrypted_config = self.encrypt_configuration(
                target_configuration, target_component_id
            )

            # Step 3: Create new configuration with encrypted data
            logging.info(f"Creating configuration in component {target_component_id}")
            new_config = self.storage_api_client.configurations.create(
                component_id=target_component_id,
                name=target_config_name or f"{source_config['name']}_migrated",
                description=source_config.get("description", ""),
                configuration=encrypted_config,
            )

            logging.info(
                f"Successfully created configuration {new_config['id']} in component {target_component_id}"
            )
            return new_config

        except Exception as e:
            logging.error(f"Error copying configuration: {str(e)}")
            raise UserException(f"Failed to copy configuration: {str(e)}")

    def migrate_configuration_with_oauth(self):
        """
        Main migration workflow:
        1. Load current config from source component
        2. Create new OAuth credentials for target component
        3. Replace OAuth ID in config and save as new config
        """
        try:
            # Target component ID as constant
            TARGET_COMPONENT_ID = "keboola.ex-facebook-pages"

            # Get parameters from environment variables
            source_component_id = self.environment_variables.component_id
            source_config_id = self.environment_variables.config_id

            # Validate required parameters
            if not source_component_id or not source_config_id:
                raise UserException("COMPONENT_ID and SOURCE_CONFIG_ID environment variables are required")

            logging.info(f"Starting migration from {source_component_id}/{source_config_id}")
            logging.info(f"Target component: {TARGET_COMPONENT_ID}")

            # Step 1: Load source configuration
            logging.info("Loading source configuration...")
            source_config = self.storage_api_client.configurations.detail(
                component_id=source_component_id,
                configuration_id=source_config_id
            )

            # Step 2: Extract current OAuth credentials info
            current_oauth = self.configuration.oauth_credentials
            if not current_oauth:
                raise UserException("No oauth_credentials found in current configuration")

            logging.info(f"Current OAuth credentials: {current_oauth}")

            # Step 3: Create new OAuth credentials for target component
            logging.info("Creating new OAuth credentials for target component...")

            # Get the OAuth credentials data
            oauth_data = {}
            if hasattr(current_oauth, "dict"):
                oauth_data = current_oauth.dict()
            elif hasattr(current_oauth, "__dict__"):
                oauth_data = current_oauth.__dict__
            else:
                oauth_data = current_oauth

            # Extract necessary data for new OAuth credentials
            authorized_for = oauth_data.get('authorizedFor', 'migrated@user.com')
            credentials_data = oauth_data.get('data', {})

            # Create new OAuth credentials via OAuth API
            new_oauth_id = f"migrated-{current_oauth.id}" if hasattr(current_oauth, 'id') else "migrated-oauth"
            new_oauth = self.oauth_api_client.create_credentials(
                component_id=TARGET_COMPONENT_ID,
                credentials_id=new_oauth_id,
                authorized_for=authorized_for,
                data=credentials_data
            )

            logging.info(f"Created new OAuth credentials with ID: {new_oauth['id']}")

            # Step 4: Prepare target configuration with new OAuth ID
            target_configuration = source_config.get("configuration", {}).copy()

            # Replace OAuth API ID in authorization section
            if "authorization" in target_configuration and "oauth_api" in target_configuration["authorization"]:
                target_configuration["authorization"]["oauth_api"]["id"] = new_oauth["id"]
                logging.info(f"Replaced OAuth ID: {current_oauth.id} -> {new_oauth['id']}")
            else:
                # Create authorization section if it doesn't exist
                target_configuration["authorization"] = {
                    "oauth_api": {"id": new_oauth["id"]}
                }

            # Step 5: Create new configuration in target component
            logging.info(f"Creating new configuration in component {TARGET_COMPONENT_ID}")
            new_config = self.storage_api_client.configurations.create(
                component_id=TARGET_COMPONENT_ID,
                name=f"{source_config['name']}_migrated",
                description=source_config.get("description", ""),
                configuration=target_configuration,
            )

            logging.info("Migration completed successfully!")
            logging.info(f"New configuration ID: {new_config['id']}")
            logging.info(f"New OAuth credentials ID: {new_oauth['id']}")

            return {
                'config': new_config,
                'oauth': new_oauth
            }

        except Exception as e:
            logging.error(f"Migration failed: {str(e)}")
            raise UserException(f"Migration failed: {str(e)}")

    def run(self):
        """Main entry point"""
        result = self.migrate_configuration_with_oauth()
        print("Migration completed successfully!")
        print(f"New config ID: {result['config']['id']}")
        print(f"New OAuth ID: {result['oauth']['id']}")


"""
        Main entrypoint
"""
if __name__ == "__main__":
    try:
        comp = Component()
        # this triggers the run method by default and is controlled by the configuration.action parameter
        comp.execute_action()
    except UserException as exc:
        logging.exception(exc)
        exit(1)
    except Exception as exc:
        logging.exception(exc)
        exit(2)
