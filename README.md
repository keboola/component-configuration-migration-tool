# Configuration Migration Tool

A Keboola component designed to automatically migrate user configurations from one component to another, where the former one is old or even deprecated and the latter one replaces it. This tool ensures seamless transitions in such cases.

## Overview

The Configuration Migration Tool is primarily used during component deprecation workflows. When a component is being deprecated in favor of a newer version, this tool:

1. **Copies configurations** from the deprecated (origin) component to the replacement (destination) component
2. **Transforms configuration data** as needed using custom migration logic
3. **Tracks migration status** to prevent duplicate migrations

## How to use this tool

### Option 1
Create the configuration for this tool. Select which component you want to migrate. Run the component. In the log, you can see the state of the migration.

### Option 2
In the deprecated component detail, click on `PROCEED WITH MIGRATION`. You will see a list of your configurations and the migration state of each one. Clicking the `MIGRATE` button will migrate all configurations whose migration status is N/A or Error.

### Migration Status Tracking

Each configuration tracks its migration status in the `runtime.migrationStatus` field:
- `"success"` - Successfully migrated
- `"error: <message>"` - Migration failed with error details
- `"n/a"` or if `runtime.migrationStatus` does not exist - Not yet migrated

## Supported Components

Currently supported migrations:

| Origin Component | Destination Component | Migration Type |
|------------------|----------------------|----------------|
| `keboola.ex-facebook` | `keboola.ex-facebook-pages` | MetaMigration |
| `keboola.ex-facebook-ads` | `keboola.ex-facebook-ads-v2` | MetaMigration |
| `keboola.ex-instagram` | `keboola.ex-instagram-v2` | MetaMigration |

## Configuration

The tool requires the following parameters:

### Parameters

- `origin` - Component ID of the deprecated component (source)
- `destination` - Component ID of the replacement component (target)
- `branch_id`- [Optional] Migrate configuration in specific branch

### Authentication

The tool uses Keboola Storage API credentials:
- `KBC_TOKEN` - Storage API token (from environment or config)
- `KBC_URL` - Keboola instance URL (from environment or config)

### Example Configuration

```json
{
  "parameters": {
    "origin": "keboola.ex-facebook",
    "destination": "keboola.ex-facebook-v2"
  }
}
```

## Development
### Adding New Migrations

To add support for migrating a new component pair, follow these steps:

#### 1. Create a Migration Class

Create a new migration class that inherits from `BaseMigration`:

```python
from migration.base_migration import BaseMigration

class YourCustomMigration(BaseMigration):
    """
    Custom migration for your component.
    """
    
    def configuration_update(self, configuration: dict) -> dict:
        """
        Override this method to transform configuration data.
        
        Args:
            configuration: The source configuration dict
            
        Returns:
            dict: The transformed configuration for the destination component
        """
        
        # Example: Transform parameter names
        if "old_parameter" in configuration["configuration"]["parameters"]:
            configuration["configuration"]["parameters"]["new_parameter"] = (
                configuration["configuration"]["parameters"].pop("old_parameter")
            )
        
        return configuration
```

#### 2. Register the Migration

Add your migration class to the `MIGRATION_REGISTRY` in `src/component.py`:

```python
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
        ComponentMigration(
            origin="your.component.id",
            destination="your.new.component.id",
            migration_class=YourCustomMigration,  # Add this migration
        ),
    ]
)
```

#### 3. Migration Class Methods

The `BaseMigration` class provides these key methods you can override:

##### `configuration_update(self, configuration: dict) -> dict`
- **Purpose**: Transform configuration data during migration
- **Default behavior**: Returns configuration unchanged
- **Override when**: You need to modify parameters, update structure, or transform data

### Show Migration button in deprectaed component
The button is automatically shown in the old component when:
- A component is marked as deprecated in the Keboola Developer Portal.
- The deprecated component has the `replacementApp` UI option set to the ID of the new component.

### Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/keboola/component-configuration-migration-tool
cd component-configuration-migration-tool
```

2. Build and run the development environment:
```bash
docker-compose build
docker-compose run --rm dev
```

3. Run tests:
```bash
docker-compose run --rm test
```

### Directory Structure

```
src/
├── component.py              # Main component class and migration registry
├── configuration.py          # Configuration validation and parsing
├── enriched_api_client.py    # Enhanced Storage API client
└── migration/
    ├── __init__.py
    ├── base_migration.py     # Base migration class
    └── meta_migration.py     # Meta Components migration class
```

For deployment and integration details, refer to the [Keboola Developer Documentation](https://developers.keboola.com/extend/component/deployment/).

## License

MIT licensed, see [LICENSE](./LICENSE.md) file.
