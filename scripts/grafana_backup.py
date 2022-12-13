#!/usr/bin/env python3

import sys
import os
import json
import grafana_api
import argparse
import multiprocessing
from datetime import datetime
from multiprocessing.pool import ThreadPool

daily_backup_type = "daily"
pool = ThreadPool(processes=multiprocessing.cpu_count() - 1)

# Possible locations of the local ca certificates_bundle
CA_BUNDLES = [
    "/etc/ssl/certs/ca-certificates.crt",
    "/etc/ssl/certs/ca-bundle.crt",
]


class GrafanaBackupManager:

    grafana_config = "grafana_urls.json"
    config_path = "/config/"

    def __init__(self, name, grafana_url, username, password, verify_ssl):
        self.name = name
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        current_date = datetime.now().strftime("%d-%m-%Y")
        self.daily_folder = "/{}/".format(current_date) + self.name + "/"
        self.grafana_api = grafana_api.GrafanaApi(grafana_url, username,
                                                  password, verify_ssl)
        if os.path.exists(GrafanaBackupManager.grafana_config):
            grafana_config_content = GrafanaBackupManager.get_grafana_content(
                GrafanaBackupManager.grafana_config)
            local_backup_content = grafana_config_content['backup'].get(
                'local', dict())
            self.local = local_backup_content.get('enabled', True) == True
            if self.local:
                self.backup_folder = local_backup_content.get(
                    'backup_folder', '')
                grafana_api.get_logger().info(
                    "Local backup is enabled and storing under : {} ".format(
                        self.backup_folder))

    def dashboard_backup(self, folder_name):
        try:
            dashboards = self.grafana_api.search_db()
            if len(dashboards) == 0:
                grafana_api.get_logger().error(
                    "Could not find any data for backup under {}".format(
                        folder_name))
            else:
                grafana_api.get_logger().info(
                    "Scanned data for backup - {}".format(len(dashboards)))
            for dashboard in dashboards:
                dashboard_uri = dashboard['uid']
                dashboard_title = dashboard['title'].lower().replace(" ", "_")
                dashboard_definition = self.grafana_api.dashboard_details(
                    dashboard_uri)
                self.__store(
                    folder_name,
                    "{}.json".format(dashboard_title).replace("/", "_"),
                    dashboard_definition["dashboard"])
        except Exception as exc:
            grafana_api.get_logger().error(
                "Error taking backup {}, error : {}".format(
                    folder_name, str(exc)))

    def daily_backup(self):
        self._store_meta_info(daily_backup_type)
        self.dashboard_backup(self.daily_folder)

    def _store_meta_info(self, backup_type, mode="Auto"):
        meta_data = {
            'time': datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            'type': backup_type,
            'mode': mode
        }
        if backup_type == daily_backup_type:
            folder_name = self.daily_folder
        else:
            folder_name = self.hourly_folder
        self.__store(folder_name, ".meta_data", meta_data)
        grafana_api.get_logger().info(
            "Taking {} Grafana JSON file Backup for host {}.".format(
                backup_type.title(), self.name.title()))

    def __store(self, folder_name, file_name, response):
        try:
            if self.local:
                folder_name = self.backup_folder + folder_name
                grafana_api.get_logger().info(
                    "Storing data on folder : {}".format(folder_name))
                os.makedirs(folder_name, exist_ok=True)
                with open(folder_name + file_name, 'w') as fp:
                    json.dump(response, fp, indent=4, sort_keys=True)
                fp.close()
        except Exception as exc:
            grafana_api.get_logger().error(
                "Error storing backup locally error : {}".format(str(exc)))

    @staticmethod
    def get_grafana_content(file_name):
        try:
            grafana_url_file = open(file_name)
            grafana_url_data = json.load(grafana_url_file)
            grafana_url_file.close()
            return grafana_url_data
        except Exception as exc:
            grafana_api.get_logger().error(
                "error reading file {} , error {}".format(file_name, str(exc)))


def get_grafana_mapper(grafana_url):
    try:
        name = grafana_url['name']
        url = grafana_url['url']
        username = grafana_url['username']
        password = grafana_url['password']
        verify_ssl = grafana_url['verify_ssl']
        return name, url, username, password, verify_ssl
    except Exception as exc:
        grafana_api.get_logger().error(
            "error mapping grafana host config file, {}".format(str(exc)))
        sys.exit(0)


def backup_grafana_dashboard(backup_type):
    grafana_api.get_logger().info("Running Grafana Backup script!")
    for grafana_url in GrafanaBackupManager.get_grafana_content(
            GrafanaBackupManager.grafana_config)['grafana_urls']:
        name, url, username, password, verify_ssl = get_grafana_mapper(
            grafana_url)
        gbm = GrafanaBackupManager(name, url, username, password, verify_ssl)
        try:
            if backup_type == daily_backup_type:
                pool.apply_async(gbm.daily_backup, ())
        except Exception as e:
            grafana_api.get_logger().error(
                "Error running backup tasks : {}".format(str(e)))
    pool.close()
    pool.join()
    grafana_api.get_logger().info("Completed taking Grafana JSON Backup!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Grafana backup script.')
    parser.add_argument('-b',
                        '--backup',
                        type=str,
                        choices=['daily'],
                        help="backup type needed for script to invoke backup.")
    parser.add_argument('-conf',
                        '--config_file',
                        type=str,
                        default=GrafanaBackupManager.grafana_config,
                        help="full path to grafana config file.")
    params = parser.parse_args()
    backup = params.backup
    config_file = params.config_file

    # set configuration file from params
    if config_file:
        GrafanaBackupManager.grafana_config = config_file
    elif not os.path.exists(GrafanaBackupManager.grafana_config):
        GrafanaBackupManager.grafana_config = GrafanaBackupManager.config_path + GrafanaBackupManager.grafana_config

    if backup:
        backup_grafana_dashboard(backup.lower())
    else:
        parser.print_help()
        sys.exit(0)
