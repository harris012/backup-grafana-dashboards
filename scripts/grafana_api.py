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
        "[%(asctime)s] %(levelname)s [%(filename)s:%(funcName)s:%(lineno)s] %(message)s",
        datefmt='%Y-%m-%dT%H:%M:%S')
    logger = logging.getLogger("grafana_backup")
    return logger


class GrafanaApi:
    """
    HTTP REST calls with status code checking and common auth/headers
    """
    def __init__(self, grafana_url, user, password) -> None:
        self.grafana_url = grafana_url
        self.user = user
        self.password = password

    def get(self, resource: str) -> Dict:
        """HTTP GET"""
        response = requests.get(f"{self.grafana_url}/api/{resource}",
                                auth=(self.user, self.password))
        return self._check_response(response.status_code,
                                    json.loads(response.text))

    @staticmethod
    def _check_response(status, response) -> Dict:
        """Gives just the response body if response is ok, otherwise fail hard"""
        if status != 200:
            message = response["message"]
            get_logger().warning(
                f"Request failed - 'HTTP error {status}: {message}'",
                file=sys.stderr)
            sys.exit(1)

        return response

    def search_db(self, folder_id):
        response = self.get(f"search?folderIds={folder_id}&type=dash-db")
        return response

    def get_folder_id(self):
        response = self.get(f"folders/")
        folder = list(filter(lambda x: x['title'] == '<your-folder-title>', response))  # edit me
        for k in folder:
            grafana_folder_id = int(k['id'])
            grafana_folder_name = str(k['title'])
        return grafana_folder_id, grafana_folder_name

    def dashboard_details(self, dashboard_uid):
        response = self.get(f"dashboards/uid/{dashboard_uid}")
        return response
