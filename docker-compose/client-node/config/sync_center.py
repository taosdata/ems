import json
import requests
import argparse
from typing import List
from mqtt_datain import load_yaml, get_cluster_id, create_database, check_ports


def create_task(
    center_host: str,
    edge_host: str,
    edge_dbname: str,
    center_dbname: str,
    labels: List[str],
) -> str:
    """
    Create a task for the specified edge node.

    Args:
        center_host (str): Hostname of the center node.
        edge_host (str): Hostname of the edge node.
        edge_dbname (str): Database name on the edge node.
        center_dbname (str): Target database name on the center node.
        labels (List[str]): Labels for the task.

    Returns:
        str: The ID of the created task.
    """
    compression_param = ""
        # "from": f"taos+ws://{edge_host}:6041/{edge_dbname}?mode=all&schema=always&schema-polling-interval=5s",
        # "from": f"tmq+ws://{edge_host}:6041/{edge_dbname}?auto_offset_reset=earliest&client_id=test&experimental_snapshot_enable=true",
        # "from": "tmq+ws://edge-node1-tdengine:6041/mqtt_datain?auto.offset.reset=earliest&busy_threshold=100%&busy_threshold_type=%&client.id=10&commit.chunk.size=0&commit.interval.ms=0&compression=false&experimental.snapshot.enable=true&health_check_window_in_second_type=s&max_errors_in_window=10&max_queue_length=1000&num.of.consumers=0&num.of.writers=0&prefer=auto&with.meta.delete=true&with.meta.drop=true",
        # "from": f"tmq+ws://{edge_host}:6041/{edge_dbname}?auto.offset.reset=earliest&client_id=test&experimental_snapshot_enable=true",

    case_data = {
        "from": f"tmq+ws://{edge_host}:6041/{edge_dbname}?auto.offset.reset=earliest&client.id=10&experimental.snapshot.enable=true",
        "to": f"taos+ws://{center_host}:6041/{center_dbname}?{compression_param}",
        "labels": labels,
    }
    task_url = f"http://{center_host}:6060/api/x/tasks"
    headers = {"Content-Type": "application/json"}
    response = requests.post(task_url, data=json.dumps(case_data), headers=headers)
    response.raise_for_status()
    return response.json()["id"]

def main(
    center_host: str, center_dbname: str, edge_dbname: str, edge_host: List[str]
) -> None:
    """
    Main function to execute the script logic.

    Args:
        center_host (str): Hostname of the center node.
        center_dbname (str): Target database name on the center node.
        edge_dbname (str): Database name on the edge node.
        edge_host (List[str]): List of edge node hostnames.
    """
    try:
        # Check if all required ports are open on the center host
        for host in [center_host]:
            if not check_ports(host, [6030, 6041, 6060], max_wait=120):
                print(
                    f"Ports on host {host} are not fully open, please check the server status."
                )

        # Get the cluster ID
        create_database(center_host, center_dbname)
        cluster_id = get_cluster_id(center_host)

        # Create tasks for each edge node
        task_list = []
        case_data_org = load_yaml("config.yaml")
        case_data_org["from"]["labels"][0] = f"cluster-id::{cluster_id}"

        for edge_host_name in edge_host:
            task_id = create_task(
                center_host,
                edge_host_name,
                edge_dbname,
                center_dbname,
                case_data_org["from"]["labels"],
            )
            task_list.append(task_id)
            print(f"Task created for {edge_host_name} with ID: {task_id}")

        print("All tasks created successfully:", task_list)
    except Exception as e:
        print("Error occurred:", e)


if __name__ == "__main__":
    # Configure command-line arguments
    parser = argparse.ArgumentParser(description="Create tasks for edge nodes")
    parser.add_argument(
        "--center-host",
        type=str,
        default="center-node",
        help="Hostname of the center node",
    )
    parser.add_argument(
        "--center-dbname",
        type=str,
        default="mqtt_datain",
        help="Database name on center nodes",
    )
    parser.add_argument(
        "--edge-dbname",
        type=str,
        default="mqtt_datain",
        help="Database name on edge nodes",
    )
    parser.add_argument(
        "--edge-host",
        type=str,
        nargs="+",
        default=["edge-node1", "edge-node2"],
        help="List of edge node hosts",
    )
    args = parser.parse_args()

    # Call the main function
    main(
        center_host=args.center_host,
        center_dbname=args.center_dbname,
        edge_dbname=args.edge_dbname,
        edge_host=args.edge_host,
    )
