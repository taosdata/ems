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
import os
import requests

class Stop():
    def __init__(self):
        self.case_config = json.load(open(os.path.join(os.environ["WORKDIR"], "test_env.json")))
        self.log_path = f'/report/{self.case_config["test_start_time"]}'
        # self.log_path = f'{os.environ["TEST_ROOT"]}/run/workflow_logs/20250228_215853'
        self.detail_log_path = f'{self.log_path}/details'
        self.summary_log_path = f'{self.log_path}/summary'
        os.makedirs(self.detail_log_path, exist_ok=True)
        os.makedirs(self.summary_log_path, exist_ok=True)

        self.test_start_time = self.case_config["test_start_time"]
        self.api_type = 0

    def get_role(self, host):
        if "edge" in host.lower():
            return "edge"
        else:
            return "center"

    # def stop_mqtt_simulator(self):
    #     if "edge" in " ".join(sys.argv):
    #         mqtt_client_config = self.tdCom.get_components_setting(self.env_setting["settings"], "mqtt_client")
    #         mqtt_host = mqtt_client_config["fqdn"][0]
    #         self._remote.cmd(mqtt_host,f"killall mqtt_pub")
    #     else:
    #         return
    def stop_tasks_get_metrics(self, task_url=None, headers=None, host=None):
        # get task list
        response = requests.get(task_url, headers=headers)
        task_list = response.json()
        task_metrics_dict = {}

        for task_info in task_list:
            task_id = task_info["id"]
            # stop task
            # requests.post(data=None, url=f'http://{host}:6060/api/x/tasks/{task_id}/stop', headers=headers)
            # get task metrics
            task_metrics = requests.get(data=None, url=f'http://{host}:6060/api/x/tasks/{task_id}/metrics',headers=headers)
            task_metrics_dict[task_id] = task_metrics.json()

        return task_metrics_dict

    def run(self) -> bool:
        # stop mqtt simulator
        # self.stop_mqtt_simulator()
        headers = {"Content-Type": "application/json"}
        query_summary_metrics = {
            "role": "edge",
            "host": "edge_host",
            "total_rows_per_second":0,
            "total_points_per_second":0,
            "total_written_rows":0,
            "total_written_points":0
        }
        tmq_summary_metrics = {
            "role": "center",
            "host": "center_host",
            "total_messages":0,
            "total_execute_time":0,
            "total_consume_cost_ms":0,
            "total_messages_of_data":0,
            "total_messages_of_meta":0,
            "total_out_of_range_rows":0,
            "total_success_messages":0,
            "total_write_cost_ms":0,
            "total_write_raw_cost_ms":0
        }
        for host in os.environ["EDGE_HOST"].split(",") + [os.environ["CENTER_HOST"].split(",")[0]]:
            task_url = f'http://{host}:6060/api/x/tasks'
            metrics_dict = self.stop_tasks_get_metrics(task_url=task_url, headers=headers, host=host)

            for task_id, _ in metrics_dict.items():
                # query_summary_metrics["total_inserted_sqls"] += metrics_dict[task_id]["total"]["total_inserted_sqls"]
                if "total_points_per_second" in metrics_dict[task_id]["total"]:
                    self.api_type = 0
                    query_summary_metrics["role"] = self.get_role(host)
                    query_summary_metrics["host"] = host

                    query_summary_metrics["total_points_per_second"] += metrics_dict[task_id]["total"]["total_points_per_second"]
                    query_summary_metrics["total_written_points"] += metrics_dict[task_id]["total"]["total_written_points"]
                    query_summary_metrics["total_written_rows"] += metrics_dict[task_id]["total"]["total_written_rows"]
                    query_summary_metrics["total_rows_per_second"] += metrics_dict[task_id]["total"]["total_rows_per_second"]
                else:
                    self.api_type = 1
                    tmq_summary_metrics["role"] = self.get_role(host)
                    tmq_summary_metrics["host"] = host
                    tmq_summary_metrics["total_messages"] += metrics_dict[task_id]["total"]["total_messages"]
                    tmq_summary_metrics["total_execute_time"] += metrics_dict[task_id]["total"]["total_execute_time"]
                    tmq_summary_metrics["total_consume_cost_ms"] += metrics_dict[task_id]["total"]["total_consume_cost_ms"]
                    tmq_summary_metrics["total_messages_of_data"] += metrics_dict[task_id]["total"]["total_messages_of_data"]
                    tmq_summary_metrics["total_messages_of_meta"] += metrics_dict[task_id]["total"]["total_messages_of_meta"]
                    tmq_summary_metrics["total_out_of_range_rows"] += metrics_dict[task_id]["total"]["total_out_of_range_rows"]
                    tmq_summary_metrics["total_success_messages"] += metrics_dict[task_id]["total"]["total_success_messages"]
                    tmq_summary_metrics["total_write_cost_ms"] += metrics_dict[task_id]["total"]["total_write_cost_ms"]
                    tmq_summary_metrics["total_write_raw_cost_ms"] += metrics_dict[task_id]["total"]["total_write_raw_cost_ms"]

            with open(f'{self.log_path}/details/{host}.json', "w") as result_file:
                json.dump(metrics_dict, result_file, indent=4)
            with open(f'{self.log_path}/summary/{host}-mqtt-perf-result.json', "w") as result_file:
                json.dump(query_summary_metrics, result_file, indent=4) if self.api_type ==0 else json.dump(tmq_summary_metrics, result_file, indent=4)
        # end_time = datetime.utcnow()
        # url = (
        #     f'http://grafana.tdengine.net:3000/d/{self.workflow_config["grafana_datasource_name"]}/tdengine-process-exporter'
        #     f"?var-interval=10m&orgId=1&from={self.start_time}&to={end_time.isoformat(timespec='milliseconds')}Z"
        #     f"&timezone=browser&var-processes=$__all&refresh=5s"
        # )
        # self.workflow_config["end_time"] = end_time.isoformat(timespec='milliseconds')
        # self.workflow_config["grafana_url"] = url
        # with open(f'{os.environ["TEST_ROOT"]}/env/workflow_config.json', "w") as config_file:
        #     json.dump(self.workflow_config, config_file, indent=4)

if __name__ == "__main__":
    # Configure command-line arguments
    main = Stop()
    main.run()