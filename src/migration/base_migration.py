"""
Base migration classes and interfaces for component configuration migration.
"""

import copy
import logging
from abc import ABC
from typing import Any

from keboola.component.exceptions import UserException

from enriched_api_client import EnrichedClient


class BaseMigration(ABC):
    """Base class for all migrations providing common functionality."""

    def __init__(self, storage_client: EnrichedClient, origin: str, destination: str):
        self.storage_client = storage_client
        self.origin_component_id: str = origin
        self.destination_component_id: str = destination
        if not self.destination_component_id:
            raise UserException("Destination component ID not set.")

        logging.info(
            f"Set components: origin {self.origin_component_id} to destination {self.destination_component_id}"
        )
        self.remove_authorization = True

    def execute(self):
        self._do_execute()

    def set_components(self, origin: str, destination: str) -> "BaseMigration":
        """Set origin and destination component IDs."""
        self.origin_component_id = origin
        self.destination_component_id = destination
        logging.info(
            f"Set components: origin {self.origin_component_id} to destination {self.destination_component_id}"
        )
        return self

    def _get_source_configurations(self) -> list[dict]:
        """Get all configurations from source component."""
        if not self.origin_component_id:
            raise ValueError("Origin component ID not set.")

        return self.storage_client.configurations.list(component_id=self.origin_component_id)

    def _is_configuration_migrated(self, config: dict) -> bool:
        """Check if configuration has already been migrated successfully."""
        configuration = config.get("configuration", {})

        # Check runtime migrationStatus
        runtime_status = configuration.get("runtime", {}).get("migrationStatus", "")
        if runtime_status == "success":
            return True

        return False

    def _get_configuration_status(self, config: dict[str, Any]) -> str:
        """Get migration status of a configuration."""
        configuration = config.get("configuration", {})

        # Check runtime migrationStatus first
        runtime_status = configuration.get("runtime", {}).get("migrationStatus")
        if runtime_status:
            return runtime_status

        return "n/a"

    def _mark_migration_success(self, config: dict) -> None:
        """Mark configuration as successfully migrated."""
        try:
            self._update_configuration_status(config, "success")
        except Exception as e:
            logging.warning(f"Failed to mark migration success for config {config['id']}: {e}")

    def _mark_migration_error(self, config: dict, error_message: str) -> None:
        """Mark configuration migration as failed with error message."""
        try:
            self._update_configuration_status(config, f"error: {error_message}")
        except Exception as e:
            logging.warning(f"Failed to mark migration error for config {config['id']}: {e}")

    def _update_configuration_status(self, config: dict, status: str) -> None:
        """Update migration status in configuration."""
        # Get the current configuration data
        configuration_data = config.get("configuration", {}).copy()

        # Add runtime section if it doesn't exist
        if "runtime" not in configuration_data:
            configuration_data["runtime"] = {}

        configuration_data["runtime"]["migrationStatus"] = status

        # Prepare the update payload according to API documentation
        update_data = {
            "name": config["name"],
            "description": config.get("description", ""),
            "configuration": configuration_data,
        }

        # Update the configuration
        self.storage_client.configurations.update(
            component_id=self.origin_component_id, configuration_id=config["id"], configuration=update_data
        )

    def configuration_update(self, configuration: dict) -> dict:
        """Update configuration."""
        return configuration

    def _do_execute(self) -> dict[str, Any]:
        """
        Internal method that performs the actual migration work.

        Args:
            configuration_update: Optional callback to modify configuration data

        Returns:
            Dict with created configurations and summary
        """

        created_configurations = []
        failed_configurations = []

        logging.info(f"Starting migration from {self.origin_component_id} to {self.destination_component_id}")

        source_configs = self._get_source_configurations()
        logging.info(f"Found {len(source_configs)} configurations to process")

        for source_config in source_configs:
            config_id = source_config["id"]
            config_name = source_config["name"]

            if self._is_configuration_migrated(source_config):
                logging.info(f"Configuration '{config_name}' ({config_id}) already migrated, skipping")
                continue

            try:
                logging.info(f"Migrating configuration '{config_name}' ({config_id})")

                target_config_data = copy.deepcopy(source_config)

                target_config_data = self.configuration_update(target_config_data)

                # Remove authorization section
                if self.remove_authorization and "authorization" in target_config_data["configuration"]:
                    del target_config_data["configuration"]["authorization"]

                # Create new configuration in target component
                new_config = self.storage_client.configurations.create(
                    component_id=self.destination_component_id,
                    name=target_config_data["name"],
                    description=target_config_data["description"],
                    configuration=target_config_data["configuration"],
                )

                # Mark original configuration as successfully migrated
                self._mark_migration_success(source_config)

                created_configurations.append(
                    {
                        "id": new_config["id"],
                        "name": new_config["name"],
                        "sourceId": config_id,
                        "sourceName": config_name,
                    }
                )

                logging.info(
                    f"Successfully migrated configuration \
                        '{config_name}' -> '{new_config['name']}' \
                        ({new_config['id']})"
                )

            except Exception as e:
                error_msg = str(e)
                logging.error(f"Failed to migrate configuration '{config_name}' ({config_id}): {error_msg}")

                # Mark configuration as failed
                self._mark_migration_error(source_config, error_msg)

                failed_configurations.append({"id": config_id, "name": config_name, "error": error_msg})

                # Re-raise UserException for user errors, wrap others
                if isinstance(e, UserException):
                    raise
                else:
                    raise UserException(f"Migration failed for configuration '{config_name}': {error_msg}")

        result = {
            "summary": {
                "total": len(source_configs),
                "migrated": len(created_configurations),
                "failed": len(failed_configurations),
                "skipped": len(source_configs) - len(created_configurations) - len(failed_configurations),
            },
            "created_configurations": created_configurations,
            "failed_configurations": failed_configurations,
        }

        logging.info(f"Migration completed: {result['summary']}")
        return result

    def status(self) -> dict[str, Any]:
        """
        Get migration status for all configurations in the source component.

        Returns:
            Dict containing status information for each configuration
        """

        configurations = self._get_source_configurations()

        status_list = []
        for config in configurations:
            status_list.append(
                {
                    "configId": config["id"],
                    "configName": config["name"],
                    "componentId": self.origin_component_id,
                    "status": self._get_configuration_status(config),
                }
            )

        return {"configurations": status_list}
