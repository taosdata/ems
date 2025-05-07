import json
import os
import re
import requests
import time
import shutil
from typing import Dict, List
from datetime import datetime, timedelta
import subprocess
import sys

class Summary():
    def __init__(self):
        self.case_config = json.load(open(os.path.join(os.environ["WORKDIR"], "test_env.json")))
        self.log_path = f'/report/{self.case_config["test_start_time"]}'
        # self.log_path = f'{os.environ["TEST_ROOT"]}/run/workflow_logs/20250228_215853'
        self.detail_log_path = f'{self.log_path}/details'
        self.summary_log_path = f'{self.log_path}/summary'
        os.makedirs(self.detail_log_path, exist_ok=True)
        os.makedirs(self.summary_log_path, exist_ok=True)

        self.timeout = 20  # Maximum wait time in seconds
        self.retention_timeout = 300
        self.query_interval = 3
        self.retry_times = 3
        self.edge_dbname = "mqtt_datain"
        self.center_dbname = "center_db"
        self.stable_data = {}
        self.report_file = f'{self.log_path}/perf_report_{self.case_config["test_start_time"]}.txt'
        self.edge_host_list = os.environ["EDGE_HOST"].split(",")
        self.center_first_ep_host = os.environ["CENTER_HOST"].split(",")[0]
        self.taosd_url = f'http://{self.center_first_ep_host}:6041/rest/sql'
        self.taosd_headers = {"Authorization": "Basic cm9vdDp0YW9zZGF0YQ=="}
        self.mqtt_received_bytes = 0

    def _execute_query(self, node: str, sql: str) -> Dict:
        url = f"http://{node}:6041/rest/sql"
        for _ in range(self.retry_times):
            try:
                resp = requests.post(url, data=sql, headers=self.taosd_headers, timeout=self.timeout)
                if resp.status_code == 200:
                    return resp.json()
            except Exception as e:
                print(f"Query failed on {node}: {str(e)}")
                time.sleep(self.query_interval)
        return {"code": -1, "desc": "Max retries exceeded"}

    def _get_stables(self, node: str, dbname: str) -> List[str]:
        sql = f"SHOW {dbname}.STABLES"
        result = self._execute_query(node, sql)
        if result.get("code") == 0:
            return [row[0] for row in result.get("data", [])]
        return []

    def _get_table_count(self, node: str, stable: str, dbname: str) -> int:
        sql = f"SELECT COUNT(*) FROM {dbname}.`{stable}`"
        result = self._execute_query(node, sql)
        if result.get("code") == 0 and result.get("data"):
            return int(result["data"][0][0])
        return 0

    def _get_compression_data(self) -> float:
        sql = f'select sum(data1+data2+data3) from information_schema.ins_disk_usage where db_name = "{self.center_dbname}";'
        result = self._execute_query(self.center_first_ep_host, sql)
        if result.get("code") == 0 and result.get("data"):
            return float(result["data"][0][0])
        return 0

    def collect_edge_data(self):
        total = 0
        for node in self.edge_host_list:
            stables = self._get_stables(node, self.edge_dbname)
            node_total = sum(self._get_table_count(node, stable, self.edge_dbname) for stable in stables)
            self.stable_data[node] = {"stables": stables, "count": node_total}
            total += node_total
        return total

    def validate_sync(self):
        edge_total = self.collect_edge_data()
        center_total = self._get_center_data()

        if edge_total == center_total:
            return [f"100%", center_total, edge_total]

        start_time = time.time()
        last_center_count = 0
        stable_counter = 0

        while time.time() - start_time < self.timeout:
            current_center = self._get_center_data()

            if current_center == last_center_count:
                stable_counter += 1
                if stable_counter >= 10:
                    break
            else:
                stable_counter = 0
                last_center_count = current_center

            completeness = current_center / edge_total if edge_total > 0 else 0
            print(f"Current sync progress: {completeness*100}%")

            time.sleep(self.query_interval)

        final_center = self._get_center_data()
        ratio = final_center / edge_total if edge_total > 0 else 0
        return [f"{round(ratio*100, 2)}%", final_center, edge_total]

    def _get_center_data(self) -> int:
        stables = self._get_stables(self.center_first_ep_host, self.center_dbname)
        return sum(self._get_table_count(self.center_first_ep_host, stable, self.center_dbname) for stable in stables)

    def get_query_detail_result(self):
        query_log = f'{self.log_path}/details/query_result.txt'
        shutil.copy(os.path.join(os.environ["WORKDIR"], "query_result.txt"), query_log)
        with open(query_log, 'r') as file:
            log_content = file.read()
        # query_pattern = r"complete query with (\d+) threads and (\d+) query delay avg:\s+([\d.]+)s min:\s+([\d.]+)s max:\s+([\d.]+)s p90:\s+([\d.]+)s p95:\s+([\d.]+)s p99:\s+([\d.]+)s SQL command: (.+);"
        query_pattern = r"complete query with (\d+) threads and (\d+)(?: sql \d+ spend [\d.]+s QPS: [\d.]+)? query delay avg:\s+([\d.]+)s min:\s+([\d.]+)s max:\s+([\d.]+)s p90:\s+([\d.]+)s p95:\s+([\d.]+)s p99:\s+([\d.]+)s SQL command: (.+?);"
        total_pattern = r"Spend ([\d.]+) second completed total queries: (\d+), the QPS of all threads:\s+([\d.]+)"

        query_matches = re.findall(query_pattern, log_content)
        total_match = re.search(total_pattern, log_content)

        results = []
        for match in query_matches:
            threads, query_times, avg, min_, max_, p90, p95, p99, sql = match
            results.append({
                "sql": sql,
                "query_times": int(int(query_times)/int(threads)),
                "concurrent": int(threads),
                "avg": float(avg),
                "min": float(min_),
                "max": float(max_),
                "p90": float(p90),
                "p95": float(p95),
                "p99": float(p99)
            })

        if total_match:
            spent, total_query, qps = total_match.groups()
            summary = {
                "QPS": float(qps),
                "spent": float(spent),
                "total_query": int(total_query)
            }
        else:
            summary = {
                "QPS": None,
                "spent": None,
                "total_query": None
            }

        final_result = {
            "summary": summary,
            "queries": results
        }
        return final_result

    def get_insert_result(self):
        insert_res_list = list()
        for filename in os.listdir(self.summary_log_path):
            if filename.endswith('.json'):
                file_path = os.path.join(self.summary_log_path, filename)
                with open(file_path, 'r') as json_file:
                    data = json.load(json_file)
                    if "mqtt_received_bytes" in data:
                        self.mqtt_received_bytes += data["mqtt_received_bytes"]
                        del data["mqtt_received_bytes"]
                    insert_res_list.append(data)
        return insert_res_list


    def get_compression_ratio(self):
        sql = f'show {self.center_dbname}.disk_info;'
        # Flush the database first
        requests.post(self.taosd_url, data=f'flush database {self.center_dbname};', headers=self.taosd_headers)

        # Retry logic with self.timeout
        start_time = time.time()
        stable_threshold = 3  # Number of consecutive stable readings required
        stable_count = 0
        last_ratio = None
        response = requests.post(self.taosd_url, data=sql, headers=self.taosd_headers)
        result = response.json()

        while time.time() - start_time < self.timeout:
            # Query disk info
            response = requests.post(self.taosd_url, data=sql, headers=self.taosd_headers)
            result = response.json()

            # Check response structure and data
            if result.get('code') == 0 and result.get('data'):
                query_res = result['data'][0][0]
                if 'Compress_radio' in query_res or 'Compress_ratio' in query_res:
                    ratio_str = query_res.split("=")[1].replace("[", "").replace("]", "")

                    # Skip NULL values
                    if ratio_str == 'NULL':
                        time.sleep(0.1)
                        continue

                    # Check if ratio has changed
                    if ratio_str != last_ratio:
                        last_ratio = ratio_str
                        stable_count = 0
                    else:
                        stable_count += 1

                    # Return when ratio is stable
                    if stable_count >= stable_threshold:
                        return f"{ratio_str}"

            # Wait for next check with a constant sleep interval
            time.sleep(min(1, self.timeout - (time.time() - start_time)))

        # Return final result (last seen ratio or NULL)
        return f"{last_ratio}%" if last_ratio is not None else "NULL%"

    def get_retention_rate(self):
        pass

    def import_dashboard(self, gf_url):
        DL_FILES = ["import_grafana_dashboard.sh", "install_via_apt.sh"]

        try:
            for DL_FILE in DL_FILES:
                DL_URL = f"https://raw.githubusercontent.com/taosdata/.github/main/.github/scripts/{DL_FILE}"
                subprocess.run(
                    ["wget", "-q", "--tries=3", "--timeout=15",
                    "-O", f"/tmp/{DL_FILE}", DL_URL],
                    check=True,
                    stderr=subprocess.PIPE
                )

                subprocess.run(["chmod", "+x", f"/tmp/{DL_FILE}"], check=True)

            subprocess.run(
                [f"/tmp/{DL_FILES[0]}", gf_url, os.environ["TDINSIGHT_DASHBOARD_IDS"], os.environ["TDINSIGHT_DASHBOARD_UIDS"]],
                check=True
            )
            print("✅ Import Successfully")

        except subprocess.CalledProcessError as e:
            print(f"❌ Exec Failed: {e}")
            sys.exit(1)

    def get_grafana_url(self):
        start_time  = datetime.utcnow() - timedelta(seconds=int(os.environ["EXEC_TIME"])) - timedelta(minutes=10)
        end_time = datetime.utcnow() + timedelta(minutes=10)
        EXTERNAL_GF_IP = os.environ["HOST_IP"] if len(os.environ["HOST_IP"]) > 0 else "<your_host_ip>"
        gf_url = f'http://{EXTERNAL_GF_IP}:{os.environ["EXTERNAL_GF_PORT"]}'
        self.import_dashboard(gf_url)

        url = (
            f'{gf_url}/d/{os.environ["TDINSIGHT_DASHBOARD_UIDS"].split(",")[0]}'
            f"?var-interval=10m&orgId=1&from={start_time.isoformat(timespec='milliseconds')}Z&to={end_time.isoformat(timespec='milliseconds')}Z"
            f"&timezone=browser&var-processes=$__all&refresh=5s"
        )
        return url

    def get_test_specs(self):
        return {
            "td_version": os.environ["TD_VERSION"],
            "edge_dnode_count": len(self.edge_host_list),
            "center_dnode_count": len(os.environ["CENTER_HOST"].split(",")),
            "exec_time": f'{os.environ["EXEC_TIME"]}s',
            "source_interval": f'{os.environ["MQTT_PUB_INTERVAL"]}ms',
            "enable_compression": os.environ["ENABLE_COMPRESSION"],
            "test_start_time": self.case_config["test_start_time"],
        }

    def cleanup(self) -> None:
        pass

    def run(self):
        insert_perf = self.get_insert_result()
        query_perf = self.get_query_detail_result()
        compression_ratio_disk_info = self.get_compression_ratio()
        data_retention_ratio, center_total_rows, edge_total_rows = self.validate_sync()
        data_retention_info = dict()
        data_retention_info["data_retention_ratio"] = data_retention_ratio
        data_retention_info["center_total_rows"] = center_total_rows
        data_retention_info["edge_total_rows"] = edge_total_rows
        compression_data_size = self._get_compression_data()
        compression_ratio = f'{round(self.mqtt_received_bytes/(compression_data_size*1024), 2)}:1' if compression_data_size != 0 else 'Null'

        grafana_url = self.get_grafana_url()
        test_specs = self.get_test_specs()
        final_res_dict = {
            "Test Specs": test_specs,
            "Insert Performance": insert_perf,
            "Query Performance": query_perf,
            "Compression Ratio": compression_ratio,
            "Data Retention Info": data_retention_info,
            "Grafana URL": grafana_url
        }
        with open(self.report_file, 'w') as file:
            json.dump(final_res_dict, file, indent=4)

if __name__ == "__main__":
    # Configure command-line arguments
    main = Summary()
    main.run()