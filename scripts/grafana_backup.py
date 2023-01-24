#!/usr/bin/env python3

import sys
import os
import json
import argparse
import tarfile
import shutil
import grafana_api
from datetime import datetime

current_date = datetime.now().strftime("%d-%m-%Y")


class GrafanaBackupManager:

    grafana_config = "config.json"
    config_path = "/vault/secrets/config.json"

    def __init__(self, name, grafana_url, user, password):
        self.name = name
        self.user = user
        self.password = password
        self.backup_dir = "/{}/".format(current_date) + self.name + "/"
        self.grafana_api = grafana_api.GrafanaApi(grafana_url, user, password)
        self.backup_folder = "backup"

    def dashboard_backup(self, folder_name):
        try:
            grafana_folder_id, grafana_folder_name = self.grafana_api.get_folder_id(
            )
            dashboards = self.grafana_api.search_db(grafana_folder_id)
            if len(dashboards) == 0:
                grafana_api.get_logger().error(
                    "Could not find any data for backup under {}".format(
                        grafana_folder_name))
            else:
                grafana_api.get_logger().info(
                    f"Scanned data for backup - Found {len(dashboards)} dashboards in {grafana_folder_name}"
                )
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
        self._store_meta_info()
        self.dashboard_backup(self.backup_dir)
        self.make_tarfile()

    def _store_meta_info(self, mode="Auto"):
        meta_data = {
            'time': datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            'type': "daily",
            'mode': mode
        }
        try:
            self.__store(self.backup_dir, ".meta_data", meta_data)
            grafana_api.get_logger().info(
                "Taking Grafana JSON file Backup for host {}.".format(
                    self.name.title()))
        except Exception as exc:
            grafana_api.get_logger().error(
                "Error creating meteadata : {}".format(str(exc)))

    def __store(self, folder_name, file_name, response):
        try:
            if self.backup_dir is not None:
                folder_name = self.backup_folder + folder_name
                grafana_api.get_logger().info(
                    "Storing data on folder : {}".format(folder_name))
                os.makedirs(folder_name, exist_ok=True)
                with open(folder_name + file_name, 'w') as fp:
                    json.dump(response, fp, indent=4, sort_keys=True)
                fp.close()
        except Exception as exc:
            grafana_api.get_logger().error("Error storing backup : {}".format(
                str(exc)))

    def make_tarfile(self):
        source_dir = self.backup_folder + "/{}".format(current_date)
        archive_file = f'{source_dir}.tar.gz'
        try:
            if os.path.exists(archive_file):
                os.remove(archive_file)
            with tarfile.open(archive_file, "w:gz") as tar:
                tar.add(source_dir, arcname=os.path.basename(source_dir))
                shutil.rmtree(
                    os.path.join(self.backup_folder,
                                 "{}".format(current_date)))
            tar.close()
            grafana_api.get_logger().info(
                'created archive at: {0}'.format(archive_file))
        except Exception as exc:
            grafana_api.get_logger().error("Error making tarfile : {}".format(
                str(exc)))

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


def backup_grafana_dashboard():
    grafana_api.get_logger().info("Running Grafana Backup script!")
    grafana_secrets = GrafanaBackupManager.get_grafana_content(
        GrafanaBackupManager.grafana_config)
    user = grafana_secrets['user']
    password = grafana_secrets['pw']
    gbm = GrafanaBackupManager(name, url, user, password)
    try:
        gbm.daily_backup()
    except Exception as e:
        grafana_api.get_logger().error(
            "Error running backup tasks : {}".format(str(e)))
    grafana_api.get_logger().info("Completed taking Grafana JSON Backup!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Grafana backup script.')
    parser.add_argument(
        '-name',
        '--dir_name',
        type=str,
        help="folder name of the backup directory in pvc it will be created")
    parser.add_argument('-url',
                        '--grafana_url',
                        type=str,
                        help="Url of the grafana source")
    parser.add_argument('-conf',
                        '--config_file',
                        type=str,
                        help="full path to grafana config file.")

    params = parser.parse_args()
    name = params.name
    url = params.grafana_url
    config_file = params.config_file

    if config_file:
        GrafanaBackupManager.grafana_config = config_file
    elif os.path.exists(GrafanaBackupManager.grafana_config) == False:
        GrafanaBackupManager.grafana_config = GrafanaBackupManager.config_path + GrafanaBackupManager.grafana_config

    if name != ' ':
        backup_grafana_dashboard()
    else:
        parser.print_help()
        sys.exit(0)
