import json
import os
import re
import requests
import time
import shutil

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
        self.dbname = "center_db"
        self.report_file = f'{self.log_path}/perf_report_{self.case_config["test_start_time"]}.txt'

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
                    insert_res_list.append(data)
        return insert_res_list


    def get_compression_ratio(self):
        taosd_url = f'http://{os.environ["CENTER_HOST"]}:6041/rest/sql'
        headers = {"Authorization": "Basic cm9vdDp0YW9zZGF0YQ=="}
        sql = f'show {self.dbname}.disk_info;'
        # Flush the database first
        requests.post(taosd_url, data=f'flush database {self.dbname};', headers=headers)

        # Retry logic with self.timeout
        start_time = time.time()
        stable_threshold = 3  # Number of consecutive stable readings required
        stable_count = 0
        last_ratio = None
        response = requests.post(taosd_url, data=sql, headers=headers)
        result = response.json()

        while time.time() - start_time < self.timeout:
            # Query disk info
            response = requests.post(taosd_url, data=sql, headers=headers)
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

    def get_grafana_url(self):
        return "http://[your_ip]:3000"

    def get_test_specs(self):
        return {
            "td_version": os.environ["TD_VERSION"],
            "edge_dnode_count": len(os.environ["EDGE_HOST"].split(",")),
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
        compression_ratio = self.get_compression_ratio()
        grafana_url = self.get_grafana_url()
        test_specs = self.get_test_specs()
        final_res_dict = {
            "Test Specs": test_specs,
            "Insert Performance": insert_perf,
            "Query Performance": query_perf,
            "Compression Ratio": compression_ratio,
            "Grafana URL": grafana_url
        }
        with open(self.report_file, 'w') as file:
            json.dump(final_res_dict, file, indent=4)

if __name__ == "__main__":
    # Configure command-line arguments
    main = Summary()
    main.run()