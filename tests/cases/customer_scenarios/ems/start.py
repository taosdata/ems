###################################################################
#           Copyright (c) 2020 by TAOS Technologies, Inc.
#                     All rights reserved.
#
#  This file is proprietary and confidential to TAOS Technologies.
#  No part of this file may be reproduced, stored, transmitted,
#  disclosed or used in any form or by any means other than as
#  expressly provided by the written permission from Jianhui Tao
#
###################################################################

# -*- coding: utf-8 -*-

from taostest import TDCase, T
from taostest.util.common import TDCom
from taostest.util.remote import Remote
import os
import sys
from datetime import datetime, timedelta
import json
from pathlib import Path
import toml
import time
class Start(TDCase):
    def init(self):
        # mqtt_data_source: $mqttDataSource,
        # mqtt_processes_per_node: $mqttProcessesPerNode,
        self.yml_name = sys.argv[1].split("=")[1]
        self.numbers_str = ''.join(filter(str.isdigit, self.yml_name))
        self.mqtt_node_idx = int(self.numbers_str) if "edge" in " ".join(sys.argv) else 1
        self.mqtt_start_idx = 1
        self.tdCom = TDCom(self.tdSql)
        self._remote: Remote = Remote(self.logger)
        self.env_root = os.path.join(os.environ["TEST_ROOT"], "env")
        self.case_config = json.load(open(os.path.join(self.env_root, "workflow_config.json")))
        self.start_time = datetime.utcnow() - timedelta(minutes=5)
        self.start_time_str = f"{self.start_time.isoformat(timespec='milliseconds')}Z"
        self.case_config["start_time"] = self.start_time_str
        # self.mqtt_data_source = self.case_config["mqtt_data_source"]
        self.mqtt_data_source = "battery-storage-data"
        self.mqtt_processes_per_node = self.case_config["mqtt_processes_per_node"]
        self.toml_file_list = list()
        if "edge" in " ".join(sys.argv):
            self.mqtt_client_config = self.tdCom.get_components_setting(self.env_setting["settings"], "mqtt_client")
            self.edge_config = self.tdCom.get_components_setting(self.env_setting["settings"], "taosd")
            self.flashmq_config = self.tdCom.get_components_setting(self.env_setting["settings"], "flashmq")
            self.edge_host = self.edge_config["fqdn"][0]
            self.flashmq_host = self.flashmq_config["fqdn"][0]
            self.mqtt_host = self.mqtt_client_config["fqdn"][0]
            self.mqtt_pub_path = self.mqtt_client_config["spec"]["config_file"]
            self.mqtt_pub_interval = self.case_config["source_interval"]
            self.exec_time = self.case_config["exec_time"]
        with open(os.path.join(self.env_root, "workflow_config.json"), "w") as config_file:
            json.dump(self.case_config, config_file, indent=4)
        pass

    def generate_idxs(self, idx, chunk_size):
        start = (idx - 1) * chunk_size + 1
        arr = list(range(start, start + chunk_size))
        return arr

    def generate_tomls(self, config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = toml.load(f)
        if 'parser' not in config or 'delta' not in config['parser']:
            raise ValueError("no parser or delta in toml file")

        idx = self.generate_idxs(self.mqtt_node_idx, int(self.mqtt_processes_per_node))
        original_path = Path(config_path)
        for id in idx:
            new_path = original_path.with_stem(original_path.stem + str(id))
            self.toml_file_list.append(new_path)

            config['parser']['delta'] = f'{id*2}d'
            with open(new_path, 'w', encoding='utf-8') as f:
                toml.dump(config, f)

    def start_mqtt_simulator(self):
        if "edge" in " ".join(sys.argv):
            self._remote.cmd(self.mqtt_host, f"nohup mqtt_pub --schema {self.mqtt_pub_path} --host {self.flashmq_host} --interval {self.mqtt_pub_interval}ms --exec-duration {self.exec_time}s > mqtt_pub.log 2>&1 &")

    def start_battery_storage_datain(self):
        if "edge" in " ".join(sys.argv):
            self._remote.get(self.mqtt_host, self.mqtt_pub_path, self.mqtt_pub_path)
            self.generate_tomls(self.mqtt_pub_path)
            cmd_list = list()
            self._remote.cmd(self.mqtt_host, ['mkdir -p /var/log/taos'])
            for mqtt_toml in self.toml_file_list:
                self._remote.put(self.mqtt_host, mqtt_toml, os.path.dirname(mqtt_toml))
                cmd_list.append(f"screen -L -Logfile /var/log/taos/mqtt_{Path(mqtt_toml).stem}.log -d -m mqtt_pub --csv-file /opt/battery_storage_data.csv --csv-header topic,payload,qos,a,b,c --schema {mqtt_toml} --host {self.flashmq_host} --interval {self.mqtt_pub_interval}ms --exec-duration {self.exec_time}s")
            self._remote.cmd(self.mqtt_host, cmd_list)
            mqtt_start_time = time.time()
            self.case_config["mqtt_start_time"] = mqtt_start_time
            with open(os.path.join(self.env_root, "workflow_config.json"), "w") as config_file:
                json.dump(self.case_config, config_file, indent=4)

    def start_taosx_service(self,host):
        self._remote.cmd(host,"systemctl stop taos-explorer")
        self._remote.cmd(host,"systemctl start taos-explorer")
        # self._remote.cmd(host,"systemctl stop taosx")
        # self._remote.cmd(host,"systemctl start taosx")
    def run(self) -> bool:
        # start taosx service
        taosd_setting = self.tdCom.get_components_setting(self.env_setting["settings"], "taosd")
        taosx_host = taosd_setting["fqdn"][0]
        self.start_taosx_service(taosx_host)
        # start mqtt simulator
        if self.mqtt_data_source == "battery-storage-data":
            self.start_battery_storage_datain()
        else:
            self.start_mqtt_simulator()

    def cleanup(self):
        pass

    def desc(self) -> str:
        case_description = """
            just start env;
        """
        return case_description

    def author(self) -> str:
        return "Jayden"

    def tags(self):
        return T