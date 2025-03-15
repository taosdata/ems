import json
import random
import yaml
import string
import requests
import argparse
import time
import socket
from typing import Dict, List, Any

# Default headers for HTTP requests
headers = {"Authorization": "Basic cm9vdDp0YW9zZGF0YQ=="}


def get_cluster_id(hostname: str) -> str:
    """
    Retrieve the cluster ID from the TDengine server.

    Args:
        hostname (str): The hostname of the TDengine server.

    Returns:
        str: The cluster ID.
    """
    taosd_url = f"http://{hostname}:6041/rest/sql/information_schema"
    cluster_resp = requests.post(taosd_url, data="show cluster", headers=headers)
    cluster_resp.raise_for_status()
    resp = cluster_resp.json()
    return resp["data"][0][0]


def create_database(
    hostname: str, db_name: str, retries: int = 10, interval: int = 10, **kwargs: Any
) -> Dict[str, str]:
    """
    Create a database in the TDengine server with retry logic.

    Args:
        hostname (str): The hostname of the TDengine server.
        db_name (str): The name of the database to create.
        retries (int): Number of retry attempts.
        interval (int): Time interval between retries (in seconds).
        **kwargs: Additional database parameters.

    Returns:
        Dict[str, str]: The result of the database creation operation.
    """
    taosd_url = f"http://{hostname}:6041/rest/sql"
    headers = {"Authorization": "Basic cm9vdDp0YW9zZGF0YQ=="}

    # Construct database parameters from kwargs
    db_params = ""
    if len(kwargs) > 0:
        for param, value in kwargs.items():
            if param == "precision":
                db_params += f'{param} "{value}" '
            else:
                db_params += f"{param} {value} "
    sql = f"CREATE DATABASE IF NOT EXISTS {db_name} {db_params}"

    # Retry logic for database creation
    for attempt in range(retries):
        try:
            response = requests.post(taosd_url, data=sql, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            result = response.json()
            return result
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < retries - 1:
                time.sleep(interval)
            else:
                return {"status": "error", "message": str(e)}


def load_json(file_path: str) -> Dict[str, Any]:
    """
    Load JSON data from a file.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        Dict[str, Any]: The loaded JSON data.
    """
    with open(file_path, "r") as f:
        return json.load(f)


def load_yaml(file_path: str) -> Dict[str, Any]:
    """
    Load YAML data from a file.

    Args:
        file_path (str): Path to the YAML file.

    Returns:
        Dict[str, Any]: The loaded YAML data.
    """
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def get_long_name(length: int = 5, mode: str = "letters") -> str:
    """
    Generate a random string of a specified length and mode.

    Args:
        length (int): Length of the generated string.
        mode (str): Mode for generating the string. Options: "numbers", "letters", "letters_mixed", "mixed".

    Returns:
        str: The generated random string.
    """
    if mode == "numbers":
        population = string.digits
    elif mode == "letters":
        population = string.ascii_letters.lower()
    elif mode == "letters_mixed":
        population = string.ascii_letters.upper() + string.ascii_letters.lower()
    else:
        population = string.ascii_letters.lower() + string.digits
    return "".join(random.choices(population, k=length))


def set_mqtt_datain_payload(
    edge_host: str = "localhost",
    edge_dbname: str = "mqtt_datain",
    mqtt_host: str = "localhost",
) -> List[Dict[str, Any]]:
    """
    Generate MQTT data ingestion payload for tasks.

    Args:
        edge_host (str): Hostname of the edge node.
        edge_dbname (str): Name of the target database.
        mqtt_host (str): Hostname of the MQTT broker.

    Returns:
        List[Dict[str, Any]]: A list of task payloads for MQTT data ingestion.
    """
    task_list = []
    cluster_id = get_cluster_id(edge_host)
    case_data_org = load_yaml("config.yaml")
    case_data_org["from"]["labels"][0] = f"cluster-id::{cluster_id}"
    case_data_from = case_data_org["from"]
    mqtt_parser = load_yaml("parser.yaml")

    for topic_id, _ in case_data_from["topics"].items():
        task_data = {}
        mqtt_parser[topic_id]["parser"]["s_model"]["name"] = (
            f'site_{topic_id}_{edge_host.replace("-", "_")}'
        )
        child_table_model = mqtt_parser[topic_id]["parser"]["model"]["name"]
        mqtt_parser[topic_id]["parser"]["model"]["using"] = (
            f'site_{topic_id}_{edge_host.replace("-", "_")}'
        )
        mqtt_parser[topic_id]["parser"]["model"]["name"] = (
            f"{child_table_model}_{edge_host.replace('-', '_')}"
        )
        cliend_id = get_long_name(4, "numbers")
        task_data["from"] = (
            f"""mqtt://{mqtt_host}:1883?version=5.0&client_id={cliend_id}&char_encoding=UTF_8&keep_alive=60&clean_session=true&topics={case_data_from["topics"][topic_id]}::0&topic_pattern={case_data_from["topic_patterns"][topic_id]}"""
        )
        task_data["parser"] = mqtt_parser[topic_id]
        task_data["to"] = f"taos+ws://{edge_host}:6041/{edge_dbname}"
        task_data["labels"] = case_data_from["labels"]
        task_list.append(task_data)
    return task_list


def post_with_retry(
    url: str,
    data: Dict[str, Any],
    headers: Dict[str, str],
    max_retries: int = 10,
    retry_interval: int = 10,
) -> requests.Response:
    """
    Send an HTTP POST request with retry logic.

    Args:
        url (str): The URL to send the request to.
        data (Dict[str, Any]): The data to send in the request body.
        headers (Dict[str, str]): The headers for the request.
        max_retries (int): Maximum number of retry attempts.
        retry_interval (int): Time interval between retries (in seconds).

    Returns:
        requests.Response: The response from the server.

    Raises:
        requests.exceptions.RequestException: If all retries fail.
    """
    for attempt in range(max_retries):
        try:
            response = requests.post(url, data=json.dumps(data), headers=headers)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_interval)
            else:
                raise


def check_port(host: str, port: int, timeout: int = 5) -> bool:
    """
    Check if a specific port on a host is open.

    Args:
        host (str): The hostname or IP address.
        port (int): The port number to check.
        timeout (int): The connection timeout in seconds.

    Returns:
        bool: True if the port is open, False otherwise.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error checking port {port}: {e}")
        return False


def check_ports(host: str, ports: List[int], max_wait: int = 120) -> bool:
    """
    Check if multiple ports on a host are open, with a maximum wait time.

    Args:
        host (str): The hostname or IP address.
        ports (List[int]): A list of port numbers to check.
        max_wait (int): The maximum wait time in seconds.

    Returns:
        bool: True if all ports are open within the wait time, False otherwise.
    """
    start_time = time.time()
    while time.time() - start_time < max_wait:
        all_ports_up = True
        for port in ports:
            if not check_port(host, port):
                all_ports_up = False
                print(f"Port {port} is not open, retrying...")
                break

        if all_ports_up:
            print("All ports are open!")
            return True

        time.sleep(5)

    print(
        f"Exceeded maximum wait time of {max_wait} seconds, some ports are still not open."
    )
    return False


def main(edge_host: str, edge_dbname: str, mqtt_host: str) -> None:
    """
    Main function to set up MQTT data ingestion tasks.

    Args:
        edge_host (str): Hostname of the edge node.
        edge_dbname (str): Name of the target database.
        mqtt_host (str): Hostname of the MQTT broker.
    """
    # Check if all required ports are open
    for host in [edge_host]:
        if not check_ports(host, [6030, 6041, 6060], max_wait=120):
            print(
                f"Ports on host {host} are not fully open, please check the server status."
            )

    headers = {"Content-Type": "application/json"}
    create_database(edge_host, edge_dbname)
    cases_data = set_mqtt_datain_payload(
        edge_host=edge_host, mqtt_host=mqtt_host, edge_dbname=edge_dbname
    )

    try:
        for case_data in cases_data:
            case_data["name"] = get_long_name(4)
            task_url = f"http://{edge_host}:6060/api/x/tasks"
            response = post_with_retry(
                task_url, case_data, headers, max_retries=10, retry_interval=10
            )
            print("Request succeeded:", response.status_code)
    except Exception as e:
        print("Request failed after retries:", e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Edge Node Parser")
    parser.add_argument(
        "--edge-host", type=str, default="localhost", help="Edge Node Hostname"
    )
    parser.add_argument("--mqtt-host", type=str, default="localhost", help="MQTT Host")
    parser.add_argument(
        "--edge-dbname", type=str, default="mqtt_datain", help="Target Database Name"
    )
    args = parser.parse_args()

    main(
        edge_host=args.edge_host, edge_dbname=args.edge_dbname, mqtt_host=args.mqtt_host
    )
