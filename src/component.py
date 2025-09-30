"""
Component Configuration Migration Tool main class.
"""

import logging

from keboola.component.base import ComponentBase, sync_action
from keboola.component.exceptions import UserException
from kbcstorage.client import Client


from configuration import Configuration
from enriched_configurations import EnrichedConfigurations
from migration.meta_migration import MetaMigration


class Component(ComponentBase):
    """
    Component Configuration Migration Tool.

    Provides migration functionality for Keboola component configurations,
    supporting both generic copy migrations and custom migrations for specific components.

    For easier debugging the data folder is picked up by default from `../data` path,
    relative to working directory.

    If `debug` parameter is present in the `config.json`, the default logger is set to verbose DEBUG mode.
    """

    MIGRATION_REGISTRY = {
        "keboola.ex-facebook": MetaMigration,
        "keboola.ex-facebook-ads": MetaMigration,
        "keboola.ex-instagram": MetaMigration,
    }

    def __init__(self):
        super().__init__()
        self.config = Configuration(**self.configuration.parameters)
        self.storage_api_client = Client(self.config.kbc_url, self.config.kbc_token)

        # Replace configurations with enriched version that includes update method
        self.storage_api_client.configurations = EnrichedConfigurations(
            self.storage_api_client.root_url, self.storage_api_client.token, self.storage_api_client.branch_id
        )

    def run(self):
        """Main entry point for the migration component."""
        migration = self._get_migration_class(self.config.origin)(
            self.storage_api_client,
            self.config.origin,
            self.config.destination,
        )
        migration.execute()

    def _get_migration_class(self, origin: str) -> type:
        try:
            return self.MIGRATION_REGISTRY[origin]
        except KeyError:
            raise UserException(f"Unsupported origin: {origin}")

    @sync_action("supported-migrations")
    def get_supported_migrations(self) -> list:
        """Get list of all supported migrations."""
        return list(self.MIGRATION_REGISTRY.keys())

    @sync_action("status")
    def get_migration_status(self) -> dict:
        """Get migration status for configurations."""
        migration = self._get_migration_class(self.config.origin)(
            self.storage_api_client, self.config.origin, self.config.destination
        )
        return migration.status()


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
