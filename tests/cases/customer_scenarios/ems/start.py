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
        self.mqtt_data_source = self.case_config["mqtt_data_source"]
        self.mqtt_processes_per_node = self.case_config["mqtt_processes_per_node"]
        self.toml_file_list = list()
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
            mqtt_client_config = self.tdCom.get_components_setting(self.env_setting["settings"], "mqtt_client")
            edge_config = self.tdCom.get_components_setting(self.env_setting["settings"], "taosd")
            edge_host = edge_config["fqdn"][0]
            mqtt_host = mqtt_client_config["fqdn"][0]
            # mqtt_pub_path = mqtt_client_config["spec"]["config"]
            mqtt_pub_path = mqtt_client_config["spec"]["config_file"]
            #mqtt_pub_interval= mqtt_client_config["spec"]["interval"]
            mqtt_pub_interval = self.case_config["source_interval"]
            exec_time = self.case_config["exec_time"]
            self._remote.cmd(mqtt_host, f"nohup mqtt_pub --schema {mqtt_pub_path} --host {edge_host} --interval {mqtt_pub_interval}ms --exec-duration {exec_time}s > mqtt_pub.log 2>&1 &")

    def start_longbow_datain(self):
        if "edge" in " ".join(sys.argv):
            mqtt_client_config = self.tdCom.get_components_setting(self.env_setting["settings"], "mqtt_client")
            edge_config = self.tdCom.get_components_setting(self.env_setting["settings"], "taosd")
            edge_host = edge_config["fqdn"][0]
            mqtt_host = mqtt_client_config["fqdn"][0]
            print(f"mqtt_host: {mqtt_host}")
            # mqtt_pub_path = mqtt_client_config["spec"]["config"]
            mqtt_pub_path = mqtt_client_config["spec"]["config_file"]
            #mqtt_pub_interval= mqtt_client_config["spec"]["interval"]
            mqtt_pub_interval = self.case_config["source_interval"]
            exec_time = self.case_config["exec_time"]
            self._remote.get(mqtt_host, mqtt_pub_path, mqtt_pub_path)
            self.generate_tomls(mqtt_pub_path)
            cmd_list = list()
            for mqtt_toml in self.toml_file_list:
                self._remote.put(mqtt_host, mqtt_toml, os.path.dirname(mqtt_toml))
                cmd_list.append(f"screen -d -m mqtt_pub --csv-file /opt/longbow_recording_fuzzy.csv --csv-header topic,payload,qos,a,b,c --schema {mqtt_toml} --host {edge_host} --interval {mqtt_pub_interval}ms --exec-duration {exec_time}s > {mqtt_toml}.log")
            self._remote.cmd(mqtt_host, cmd_list)
# ./mqtt_pub  --csv-file longbow_recording.csv --csv-header topic,payload,qos,a,b,c --schema longbow.toml --interval 0s --host ems-edge-2

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
        if self.mqtt_data_source == "longbow-csv":
            self.start_longbow_datain()
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