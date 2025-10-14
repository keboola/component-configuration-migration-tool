import unittest
from unittest.mock import Mock, patch

from src.migration.base_migration import BaseMigration


class TestBaseMigration(unittest.TestCase):
    """Test cases for BaseMigration class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_storage_client = Mock()
        self.migration = BaseMigration(
            storage_client=self.mock_storage_client,
            origin="test-origin-component",
            destination="test-destination-component",
        )

    def test_is_configuration_migrated_success_status(self):
        """Test _is_configuration_migrated returns True when migrationStatus is 'success'."""
        config = {
            "id": "test-config-1",
            "name": "Test Configuration",
            "configuration": {"runtime": {"migrationStatus": "success"}},
        }

        result = self.migration._is_configuration_migrated(config)
        self.assertTrue(result)

    def test_is_configuration_migrated_error_status(self):
        """Test _is_configuration_migrated returns False when migrationStatus is 'error'."""
        config = {
            "id": "test-config-2",
            "name": "Test Configuration",
            "configuration": {"runtime": {"migrationStatus": "error: Some error message"}},
        }

        result = self.migration._is_configuration_migrated(config)
        self.assertFalse(result)

    def test_is_configuration_migrated_empty_status(self):
        """Test _is_configuration_migrated returns False when migrationStatus is empty string."""
        config = {
            "id": "test-config-3",
            "name": "Test Configuration",
            "configuration": {"runtime": {"migrationStatus": ""}},
        }

        result = self.migration._is_configuration_migrated(config)
        self.assertFalse(result)

    def test_is_configuration_migrated_missing_migration_status(self):
        """Test _is_configuration_migrated returns False when migrationStatus key is missing."""
        config = {
            "id": "test-config-4",
            "name": "Test Configuration",
            "configuration": {"runtime": {"otherProperty": "some value"}},
        }

        result = self.migration._is_configuration_migrated(config)
        self.assertFalse(result)

    def test_is_configuration_migrated_missing_runtime(self):
        """Test _is_configuration_migrated returns False when runtime section is missing."""
        config = {"id": "test-config-5", "name": "Test Configuration", "configuration": {"otherProperty": "some value"}}

        result = self.migration._is_configuration_migrated(config)
        self.assertFalse(result)

    def test_is_configuration_migrated_missing_configuration(self):
        """Test _is_configuration_migrated returns False when configuration section is missing."""
        config = {"id": "test-config-6", "name": "Test Configuration"}

        result = self.migration._is_configuration_migrated(config)
        self.assertFalse(result)

    def test_is_configuration_migrated_empty_config(self):
        """Test _is_configuration_migrated returns False when config is empty dict."""
        config = {}

        result = self.migration._is_configuration_migrated(config)
        self.assertFalse(result)

    def test_update_configuration_status_with_existing_runtime(self):
        """Test _update_configuration_status when runtime section already exists."""
        config = {
            "id": "test-config-1",
            "name": "Test Configuration",
            "description": "Test Description",
            "configuration": {"runtime": {"otherProperty": "existing value"}, "otherConfig": "some data"},
        }

        # Call the method
        self.migration._update_configuration_status(config, "success")

        # Verify the storage client was called with correct parameters
        self.mock_storage_client.configurations.update.assert_called_once_with(
            component_id="test-origin-component",
            configuration_id="test-config-1",
            configuration={
                "name": "Test Configuration",
                "description": "Test Description",
                "configuration": {
                    "runtime": {"otherProperty": "existing value", "migrationStatus": "success"},
                    "otherConfig": "some data",
                },
            },
        )

    def test_update_configuration_status_without_runtime(self):
        """Test _update_configuration_status when runtime section does not exist."""
        config = {
            "id": "test-config-2",
            "name": "Test Configuration",
            "description": "Test Description",
            "configuration": {"otherConfig": "some data"},
        }

        # Call the method
        self.migration._update_configuration_status(config, "error: Test error")

        # Verify the storage client was called with correct parameters
        self.mock_storage_client.configurations.update.assert_called_once_with(
            component_id="test-origin-component",
            configuration_id="test-config-2",
            configuration={
                "name": "Test Configuration",
                "description": "Test Description",
                "configuration": {"otherConfig": "some data", "runtime": {"migrationStatus": "error: Test error"}},
            },
        )

    def test_update_configuration_status_without_configuration_section(self):
        """Test _update_configuration_status when configuration section is missing."""
        config = {"id": "test-config-3", "name": "Test Configuration", "description": "Test Description"}

        # Call the method
        self.migration._update_configuration_status(config, "success")

        # Verify the storage client was called with correct parameters
        self.mock_storage_client.configurations.update.assert_called_once_with(
            component_id="test-origin-component",
            configuration_id="test-config-3",
            configuration={
                "name": "Test Configuration",
                "description": "Test Description",
                "configuration": {"runtime": {"migrationStatus": "success"}},
            },
        )

    def test_update_configuration_status_without_description(self):
        """Test _update_configuration_status when description is missing."""
        config = {"id": "test-config-4", "name": "Test Configuration", "configuration": {"someConfig": "data"}}

        # Call the method
        self.migration._update_configuration_status(config, "pending")

        # Verify the storage client was called with correct parameters
        self.mock_storage_client.configurations.update.assert_called_once_with(
            component_id="test-origin-component",
            configuration_id="test-config-4",
            configuration={
                "name": "Test Configuration",
                "description": "",
                "configuration": {"someConfig": "data", "runtime": {"migrationStatus": "pending"}},
            },
        )

    def test_update_configuration_status_preserves_existing_runtime_data(self):
        """Test _update_configuration_status preserves existing runtime data."""
        config = {
            "id": "test-config-5",
            "name": "Test Configuration",
            "description": "Test Description",
            "configuration": {"runtime": {"existingStatus": "old_status", "otherRuntimeData": "preserved"}},
        }

        # Call the method
        self.migration._update_configuration_status(config, "success")

        # Verify the storage client was called with correct parameters
        self.mock_storage_client.configurations.update.assert_called_once_with(
            component_id="test-origin-component",
            configuration_id="test-config-5",
            configuration={
                "name": "Test Configuration",
                "description": "Test Description",
                "configuration": {
                    "runtime": {
                        "existingStatus": "old_status",
                        "otherRuntimeData": "preserved",
                        "migrationStatus": "success",
                    }
                },
            },
        )

    def test_update_configuration_status_with_empty_status(self):
        """Test _update_configuration_status with empty status string."""
        config = {
            "id": "test-config-6",
            "name": "Test Configuration",
            "description": "Test Description",
            "configuration": {"someConfig": "data"},
        }

        # Call the method
        self.migration._update_configuration_status(config, "")

        # Verify the storage client was called with correct parameters
        self.mock_storage_client.configurations.update.assert_called_once_with(
            component_id="test-origin-component",
            configuration_id="test-config-6",
            configuration={
                "name": "Test Configuration",
                "description": "Test Description",
                "configuration": {"someConfig": "data", "runtime": {"migrationStatus": ""}},
            },
        )

    @patch("src.migration.base_migration.logging")
    def test_do_execute_successful_migration(self, mock_logging):
        """Test _do_execute with successful migration scenario."""
        # Mock source configurations
        source_configs = [
            {
                "id": "config-1",
                "name": "Test Config 1",
                "description": "Test Description 1",
                "configuration": {"param1": "value1"},
            },
            {
                "id": "config-2",
                "name": "Test Config 2",
                "description": "Test Description 2",
                "configuration": {"param2": "value2"},
            },
        ]

        # Mock created configuration response
        created_config = {"id": "new-config-1", "name": "Test Config 1"}

        # Setup mocks
        self.mock_storage_client.configurations.list.return_value = source_configs
        self.mock_storage_client.configurations.create.return_value = created_config

        # Mock the helper methods
        with (
            patch.object(self.migration, "_is_configuration_migrated", return_value=False),
            patch.object(self.migration, "_mark_migration_success"),
        ):
            result = self.migration._do_execute()

        # Verify results
        self.assertEqual(result["summary"]["total"], 2)
        self.assertEqual(result["summary"]["migrated"], 2)
        self.assertEqual(result["summary"]["failed"], 0)
        self.assertEqual(result["summary"]["skipped"], 0)
        self.assertEqual(len(result["created_configurations"]), 2)
        self.assertEqual(len(result["failed_configurations"]), 0)

    @patch("src.migration.base_migration.logging")
    def test_do_execute_with_skipped_configurations(self, mock_logging):
        """Test _do_execute with some configurations already migrated."""
        source_configs = [
            {
                "id": "config-1",
                "name": "Test Config 1",
                "description": "Test Description 1",
                "configuration": {"runtime": {"migrationStatus": "success"}},
            },
            {"id": "config-2", "name": "Test Config 2", "description": "Test Description 2", "configuration": {}},
        ]

        created_config = {"id": "new-config-2", "name": "Test Config 2"}

        # Setup mocks
        self.mock_storage_client.configurations.list.return_value = source_configs
        self.mock_storage_client.configurations.create.return_value = created_config

        # Mock _is_configuration_migrated to return True for first config, False for second
        def mock_is_migrated(config):
            return config["id"] == "config-1"

        with (
            patch.object(self.migration, "_is_configuration_migrated", side_effect=mock_is_migrated),
            patch.object(self.migration, "_mark_migration_success"),
        ):
            result = self.migration._do_execute()

        # Verify results
        self.assertEqual(result["summary"]["total"], 2)
        self.assertEqual(result["summary"]["migrated"], 1)
        self.assertEqual(result["summary"]["failed"], 0)
        self.assertEqual(result["summary"]["skipped"], 1)

    @patch("src.migration.base_migration.logging")
    def test_do_execute_removes_authorization(self, mock_logging):
        """Test _do_execute removes authorization section when remove_authorization is True."""
        source_configs = [
            {
                "id": "config-1",
                "name": "Test Config",
                "description": "Test Description",
                "configuration": {"param1": "value1", "authorization": {"token": "secret"}},
            }
        ]

        created_config = {"id": "new-config-1", "name": "Test Config"}

        # Setup mocks
        self.mock_storage_client.configurations.list.return_value = source_configs
        self.mock_storage_client.configurations.create.return_value = created_config

        with (
            patch.object(self.migration, "_is_configuration_migrated", return_value=False),
            patch.object(self.migration, "_mark_migration_success"),
        ):
            self.migration._do_execute()

        # Verify that create was called without authorization
        call_args = self.mock_storage_client.configurations.create.call_args
        config_data = call_args[1]["configuration"]
        self.assertNotIn("authorization", config_data)
        self.assertIn("param1", config_data)


if __name__ == "__main__":
    unittest.main()
