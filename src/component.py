"""
Component Configuration Migration Tool main class.
"""

import logging

from keboola.component.base import ComponentBase, sync_action
from keboola.component.exceptions import UserException
from kbcstorage.client import Client


from configuration import Configuration, ComponentMigration, ComponentMigrationList
from enriched_api_client import EnrichedConfigurations, EnrichedComponents
from migration.meta_migration import MetaMigration
from migration.base_migration import BaseMigration


class Component(ComponentBase):
    """
    Component Configuration Migration Tool.

    Provides migration functionality for Keboola component configurations,
    supporting both generic copy migrations and custom migrations for specific components.

    For easier debugging the data folder is picked up by default from `../data` path,
    relative to working directory.

    If `debug` parameter is present in the `config.json`, the default logger is set to verbose DEBUG mode.
    """

    MIGRATION_REGISTRY = ComponentMigrationList(
        migrations=[
            ComponentMigration(
                origin="keboola.ex-facebook",
                destination="keboola.ex-facebook-pages",
                migration_class=MetaMigration,
            ),
            ComponentMigration(
                origin="keboola.ex-facebook-ads",
                destination="keboola.ex-facebook-ads-v2",
                migration_class=MetaMigration,
            ),
            ComponentMigration(
                origin="keboola.ex-instagram",
                destination="keboola.ex-instagram-v2",
                migration_class=MetaMigration,
            ),
        ]
    )

    def __init__(self):
        super().__init__()
        self.config = Configuration(**self.configuration.parameters)
        self.storage_api_client = Client(self.config.kbc_url, self.config.kbc_token)

        # Replace configurations with enriched version that includes update method
        self.storage_api_client.configurations = EnrichedConfigurations(
            self.storage_api_client.root_url, self.storage_api_client.token, self.storage_api_client.branch_id
        )
        self.storage_api_client.components = EnrichedComponents(
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

    def _get_migration_class(self, origin: str) -> type[BaseMigration]:
        if not origin:
            raise UserException("Origin component ID not set.")
        if not self.MIGRATION_REGISTRY.get_migration_class(origin):
            raise UserException(f"Unsupported origin: {origin}")
        return self.MIGRATION_REGISTRY.get_migration_class(origin)

    @sync_action("supported-migrations")
    def get_supported_migrations(self) -> list:
        """Get list of all supported migrations."""
        origin_ids = self.MIGRATION_REGISTRY.get_origin_ids()
        result = []

        for origin_id in origin_ids:
            try:
                component_info = self.storage_api_client.components.get_component(origin_id)
                component_name = component_info.get("name", origin_id)
                result.append({"label": component_name, "value": origin_id})
            except Exception as e:
                logging.warning(f"Failed to get component info for {origin_id}: {e}")
                # Fallback to using origin_id as label if API call fails
                result.append({"label": origin_id, "value": origin_id})

        return result

    @sync_action("load-destination")
    def load_destination(self) -> dict:
        """Get destination component information for the given origin."""
        if not self.config.origin:
            raise UserException("Origin component ID is required for load-destination action.")

        # Get destination ID from migration registry
        destination_id = self.MIGRATION_REGISTRY.get_destination_id(self.config.origin)
        if not destination_id:
            raise UserException(f"No destination found for origin: {self.config.origin}")

        try:
            component_info = self.storage_api_client.components.get_component(destination_id)
            component_name = component_info.get("name", destination_id)
            return {"label": component_name, "value": destination_id}
        except Exception as e:
            logging.warning(f"Failed to get component info for destination {destination_id}: {e}")
            # Fallback to using destination_id as label if API call fails
            return {"label": destination_id, "value": destination_id}

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
