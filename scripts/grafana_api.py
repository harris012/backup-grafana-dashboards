"""
Requests related to communicate with grafana API search for folders & dashboards etc.
"""

import requests
import sys
import logging
import json
from typing import Dict

# locations of the local ca certificates_bundle
CA_BUNDLES = [
    "ca-certificates.crt",
    "erts/ca-bundle.crt",
]
# force ssl verification otherwise script will fail
ssl_verify = "True"


def get_logger():
    logging.basicConfig(
        stream=sys.stdout,
        level="INFO",
        format=
        "[%(asctime)s] %(levelname)s [%(filename)s:%(funcName)s:%(lineno)s] %(message)s",
        datefmt='%Y-%m-%dT%H:%M:%S')
    logger = logging.getLogger("grafana_backup")
    return logger


class GrafanaApi:
    """
    HTTP REST calls with status code checking and common auth/headers
    """
    def __init__(self, grafana_url, user, password, verify_ssl,
                 client_cert) -> None:
        self.grafana_url = grafana_url
        self.user = user
        self.password = password
        self.ssl_verify = verify_ssl
        self.CA_BUNDLES = client_cert

    def get(self, resource: str) -> Dict:
        """HTTP GET"""
        response = requests.get(f"{self.grafana_url}/api/{resource}",
                                auth=(self.user, self.password))
        return self._check_response(response.status_code,
                                    json.loads(response.text))

    @staticmethod
    def _check_response(status, response) -> Dict:
        """
        Gives just the response body if response is ok, otherwise fail hard
        """
        if status != 200:
            message = response["message"]
            get_logger().warning(
                f"Request failed - 'HTTP error {status}: {message}'",
                file=sys.stderr)
            sys.exit(1)

        return response

    def search_db(self, folder_id):
        """
        Gives the present dashboards in a certain folder
        """
        response = self.get(f"search?folderIds={folder_id}&type=dash-db")
        return response

    def get_folder_id(self):
        """
        Gives the folder id and folder name
        """
        response = self.get(f"folders/")
        folder = list(
            filter(lambda x: x['title'] == '<your-folder-in-grafana-instance>',
                   response))  # edit me
        for k in folder:
            grafana_folder_id = int(k['id'])
            grafana_folder_name = str(k['title'])
        return grafana_folder_id, grafana_folder_name

    def dashboard_details(self, dashboard_uid):
        """
        Gives the required dashboard
        """
        response = self.get(f"dashboards/uid/{dashboard_uid}")
        return response
