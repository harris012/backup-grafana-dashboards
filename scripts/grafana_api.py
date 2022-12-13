import requests
import sys
import logging
import json
from typing import Dict


def get_logger():
    logging.basicConfig(
        stream=sys.stdout,
        level="INFO",
        format=
        "[%(asctime)s] %(levelname)s [%(threadName)s] [%(filename)s:%(funcName)s:%(lineno)s] %(message)s",
        datefmt='%Y-%m-%dT%H:%M:%S')
    logger = logging.getLogger("grafana_backup")
    return logger


class GrafanaApi:
    """
    HTTP REST calls with status code checking and common auth/headers
    """
    def __init__(self, grafana_url, username, password, verify_ssl) -> None:
        self.grafana_url = grafana_url
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl

    def get(self, resource: str) -> Dict:
        """HTTP GET"""
        response = requests.get(f"{self.grafana_url}/api/{resource}",
                                auth=(self.username, self.password))
        return self._check_response(response.status_code,
                                    json.loads(response.text))

    @staticmethod
    def _check_response(status, response) -> Dict:
        """Gives just the response body if response is ok, otherwise fail hard"""
        if status != 200:
            message = response["message"]
            print(f"Request failed - 'HTTP error {status}: {message}'",
                  file=sys.stderr)
            quit(1)

        return response

    def search_db(self):
        folder_id = 1256
        response = self.get(f"search?folderIds={folder_id}type=dash-db")
        return response

    def search_folder(self, folder_id):
        url = "{}/api/folders/id/{}".format(self.grafana_url, folder_id)
        get_logger().info("Request To : URL {}")
        response = requests.get(url)
        return response

    def dashboard_details(self, dashboard_uid):
        response = self.get(f"dashboards/uid/{dashboard_uid}")
        return response
