"""
Enhanced Configurations class with additional update functionality.
"""

import json
from kbcstorage.configurations import Configurations


class EnrichedConfigurations(Configurations):
    """
    Enhanced Configurations class that extends the base Configurations class
    with additional update functionality.
    """

    def update(self, component_id, configuration_id, configuration):
        """
        Update an existing configuration.

        Args:
            component_id (str): ID of the component.
            configuration_id (str): ID of the configuration to update.
            configuration (dict): Configuration parameters.

        Returns:
            response_body: The parsed json from the HTTP response.

        Raises:
            requests.HTTPError: If the API request fails.
        """
        if not isinstance(component_id, str) or component_id == "":
            raise ValueError("Invalid component_id '{}'.".format(component_id))
        if not isinstance(configuration_id, str) or configuration_id == "":
            raise ValueError("Invalid configuration_id '{}'.".format(configuration_id))

        url = "{}/{}/configs/{}".format(self.base_url, component_id, configuration_id)
        return self._put(url, data=json.dumps(configuration), headers={"Content-Type": "application/json"})
