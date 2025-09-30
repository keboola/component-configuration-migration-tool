from .base_migration import BaseMigration


class MetaMigration(BaseMigration):
    """
    Meta component (ex-facebook, ex-facebook-ads, ex-instagram) migration
    that copies configurations from source to destination component.
    """

    def configuration_update(self, configuration: dict) -> dict:
        """Update configuration."""
        configuration["configuration"]["parameters"]["bucket-id"] = (
            f"in.c-{self.origin_component_id.replace('.', '-')}-{configuration['id']}"
        )
        return configuration
