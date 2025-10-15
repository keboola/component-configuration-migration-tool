import unittest
from unittest.mock import Mock

from src.migration.meta_migration import MetaMigration


class TestMetaMigration(unittest.TestCase):
    """Test cases for MetaMigration class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_storage_client = Mock()
        self.migration = MetaMigration(
            storage_client=self.mock_storage_client,
            origin="ex-facebook",
            destination="ex-facebook-ads",
        )

    def test_configuration_update_with_existing_parameters(self):
        """Test configuration_update when parameters section already exists."""
        configuration = {
            "id": "test-config-1",
            "name": "Test Configuration",
            "configuration": {"parameters": {"existing_param": "existing_value", "other_param": "other_value"}},
        }

        result = self.migration.configuration_update(configuration)

        expected_configuration = {
            "id": "test-config-1",
            "name": "Test Configuration",
            "configuration": {
                "parameters": {
                    "existing_param": "existing_value",
                    "other_param": "other_value",
                    "bucket-id": "in.c-ex-facebook-test-config-1",
                }
            },
        }

        self.assertEqual(result, expected_configuration)

    def test_configuration_update_without_parameters_section(self):
        """Test configuration_update when parameters section does not exist."""
        configuration = {
            "id": "test-config-2",
            "name": "Test Configuration",
            "configuration": {"other_section": "some_value"},
        }

        result = self.migration.configuration_update(configuration)

        expected_configuration = {
            "id": "test-config-2",
            "name": "Test Configuration",
            "configuration": {
                "other_section": "some_value",
                "parameters": {"bucket-id": "in.c-ex-facebook-test-config-2"},
            },
        }

        self.assertEqual(result, expected_configuration)

    def test_configuration_update_with_empty_parameters(self):
        """Test configuration_update when parameters section exists but is empty."""
        configuration = {"id": "test-config-3", "name": "Test Configuration", "configuration": {"parameters": {}}}

        result = self.migration.configuration_update(configuration)

        expected_configuration = {
            "id": "test-config-3",
            "name": "Test Configuration",
            "configuration": {"parameters": {"bucket-id": "in.c-ex-facebook-test-config-3"}},
        }

        self.assertEqual(result, expected_configuration)

    def test_configuration_update_with_none_parameters(self):
        """Test configuration_update when parameters is None."""
        configuration = {"id": "test-config-4", "name": "Test Configuration", "configuration": {"parameters": None}}

        result = self.migration.configuration_update(configuration)

        expected_configuration = {
            "id": "test-config-4",
            "name": "Test Configuration",
            "configuration": {"parameters": {"bucket-id": "in.c-ex-facebook-test-config-4"}},
        }

        self.assertEqual(result, expected_configuration)

    def test_bucket_id_generation_with_dots_in_component_id(self):
        """Test bucket-id generation when component ID contains dots."""
        migration = MetaMigration(
            storage_client=self.mock_storage_client,
            origin="ex.facebook.ads",
            destination="ex-facebook-ads",
        )

        configuration = {"id": "test-config-5", "name": "Test Configuration", "configuration": {}}

        result = migration.configuration_update(configuration)

        expected_configuration = {
            "id": "test-config-5",
            "name": "Test Configuration",
            "configuration": {"parameters": {"bucket-id": "in.c-ex-facebook-ads-test-config-5"}},
        }

        self.assertEqual(result, expected_configuration)

    def test_bucket_id_generation_with_different_component_ids(self):
        """Test bucket-id generation with various component ID formats."""
        test_cases = [
            ("ex-facebook", "in.c-ex-facebook-test-config"),
            ("ex.facebook", "in.c-ex-facebook-test-config"),
            ("ex.facebook.ads", "in.c-ex-facebook-ads-test-config"),
            ("ex-instagram", "in.c-ex-instagram-test-config"),
            ("ex.instagram", "in.c-ex-instagram-test-config"),
        ]

        for origin_component, expected_bucket_id in test_cases:
            with self.subTest(origin_component=origin_component):
                migration = MetaMigration(
                    storage_client=self.mock_storage_client,
                    origin=origin_component,
                    destination="test-destination",
                )

                configuration = {"id": "test-config", "name": "Test Configuration", "configuration": {}}

                result = migration.configuration_update(configuration)

                expected_configuration = {
                    "id": "test-config",
                    "name": "Test Configuration",
                    "configuration": {"parameters": {"bucket-id": expected_bucket_id}},
                }

                self.assertEqual(result, expected_configuration)

    def test_configuration_update_preserves_original_structure(self):
        """Test that configuration_update preserves the original configuration structure."""
        original_configuration = {
            "id": "test-config-6",
            "name": "Test Configuration",
            "description": "Test Description",
            "configuration": {"parameters": {"existing_param": "existing_value"}, "other_section": {"nested": "value"}},
            "extra_field": "extra_value",
        }

        result = self.migration.configuration_update(original_configuration)

        expected_configuration = {
            "id": "test-config-6",
            "name": "Test Configuration",
            "description": "Test Description",
            "configuration": {
                "parameters": {"existing_param": "existing_value", "bucket-id": "in.c-ex-facebook-test-config-6"},
                "other_section": {"nested": "value"},
            },
            "extra_field": "extra_value",
        }

        self.assertEqual(result, expected_configuration)

    def test_bucket_id_generation_with_special_characters_in_config_id(self):
        """Test bucket-id generation with special characters in configuration ID."""
        configuration = {"id": "test-config-with-special_chars.123", "name": "Test Configuration", "configuration": {}}

        result = self.migration.configuration_update(configuration)

        expected_configuration = {
            "id": "test-config-with-special_chars.123",
            "name": "Test Configuration",
            "configuration": {"parameters": {"bucket-id": "in.c-ex-facebook-test-config-with-special_chars.123"}},
        }

        self.assertEqual(result, expected_configuration)


if __name__ == "__main__":
    unittest.main()
