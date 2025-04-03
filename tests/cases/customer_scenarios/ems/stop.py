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

import json
from taostest import TDCase, T
from taostest.util.common import TDCom
from taostest.util.remote import Remote
import os
import sys
from datetime import datetime
from taostest.util.rest import TDRest

class Start(TDCase):
    def init(self):
        self.tdCom = TDCom(self.tdSql)
        self._remote: Remote = Remote(self.logger)
        self.workflow_config = self.tdCom.load_workflow_json(self._remote, f'{os.environ["TEST_ROOT"]}/env/workflow_config.json')
        self.taosd_setting = self.tdCom.get_components_setting(self.env_setting["settings"], "taosd")
        self.taospy_setting = self.tdCom.get_components_setting(self.env_setting["settings"], "taospy")
        self.start_time = self.workflow_config["start_time"]
        self.tdRest = TDRest(env_setting=self.env_setting)
        self.test_start_time = self.workflow_config["test_start_time"]
        self.host = self.taosd_setting["fqdn"][0]
        self.log_path = f'{os.environ["TEST_ROOT"]}/run/workflow_logs/{self.workflow_config["test_start_time"]}'
        pass

    def get_role(self):
        if "edge" in " ".join(sys.argv):
            return "edge"
        else:
            return "center"

    def stop_mqtt_simulator(self):
        if "edge" in " ".join(sys.argv):
            mqtt_client_config = self.tdCom.get_components_setting(self.env_setting["settings"], "mqtt_client")
            mqtt_host = mqtt_client_config["fqdn"][0]
            self._remote.cmd(mqtt_host,f"killall mqtt_pub")
        else:
            return
    def stop_tasks_get_metrics(self,task_url=None,headers=None):
        # get task list
        response = self.tdRest.request(data=None, method='GET', url=task_url,header=headers)
        task_list = response.json()
        task_metrics_dict = {}

        for task_info in task_list:
            task_id = task_info["id"]
            # stop task
            self.tdRest.request(data=None, method='POST', url=f'http://{self.host}:6060/api/x/tasks/{task_id}/stop',header=headers)
            # get task metrics
            task_metrics = self.tdRest.request(data=None, method='GET', url=f'http://{self.host}:6060/api/x/tasks/{task_id}/metrics',header=headers)
            task_metrics_dict[task_id] = task_metrics.json()

        return task_metrics_dict
    def run(self) -> bool:

        # stop mqtt simulator
        self.stop_mqtt_simulator()
        headers = {"Content-Type": "application/json"}
        task_url = f'http://{self.host}:6060/api/x/tasks'
        metrics_dict = self.stop_tasks_get_metrics(task_url=task_url,headers=headers)
        summary_metrics = {
            "role": self.get_role(),
            "host": self.host,
            "total_rows_per_second":0,
            "total_points_per_second":0,
            "total_written_rows":0,
            "total_written_points":0
        }
        for task_id,metrics in metrics_dict.items():
            # summary_metrics["total_inserted_sqls"] += metrics_dict[task_id]["total"]["total_inserted_sqls"]
            summary_metrics["total_points_per_second"] += metrics_dict[task_id]["total"]["total_points_per_second"]
            summary_metrics["total_written_points"] += metrics_dict[task_id]["total"]["total_written_points"]
            summary_metrics["total_written_rows"] += metrics_dict[task_id]["total"]["total_written_rows"]
            summary_metrics["total_rows_per_second"] += metrics_dict[task_id]["total"]["total_rows_per_second"]
        with open(f'{self.log_path}/details/{self.host}.json', "w") as result_file:
            json.dump(metrics_dict, result_file, indent=4)
        with open(f'{self.log_path}/summary/{self.host}-mqtt-perf-result.json', "w") as result_file:
            json.dump(summary_metrics, result_file, indent=4)
        end_time = datetime.utcnow()
        url = (
            f'http://grafana.tdengine.net:3000/d/{self.workflow_config["grafana_datasource_name"]}/tdengine-process-exporter'
            f"?var-interval=10m&orgId=1&from={self.start_time}&to={end_time.isoformat(timespec='milliseconds')}Z"
            f"&timezone=browser&var-processes=$__all&refresh=5s"
        )
        self.workflow_config["end_time"] = end_time.isoformat(timespec='milliseconds')
        self.workflow_config["grafana_url"] = url
        with open(f'{os.environ["TEST_ROOT"]}/env/workflow_config.json', "w") as config_file:
            json.dump(self.workflow_config, config_file, indent=4)


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