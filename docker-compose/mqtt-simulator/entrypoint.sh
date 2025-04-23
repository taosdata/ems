#!/bin/bash
set -eo pipefail

TOML_FILE=/etc/mqtt/ems.toml

# Environment variable validation and default settings
: "${EDGE_HOST:?Environment variable EDGE_HOST must be set}"
: "${MQTT_PUB_INTERVAL:=1000}"
: "${EXEC_TIME:=60}"

# Verify configuration file existence
if [ ! -f "${TOML_FILE}" ]; then
    echo "Error: Config file ${TOML_FILE} not found" >&2
    exit 1
fi

current_time=$(date -u +'%Y-%m-%dT%H:%M:%S.%3NZ' -d '+8 hours')
if [ "${MQTT_PUB_INTERVAL}" -eq "0" ];then
    interval=1
else
    interval=${MQTT_PUB_INTERVAL}
fi

sed -i "s/\(start_time = \)[^,]*/\1$current_time/" ${TOML_FILE}
sed -i "s/\(interval = \"\)[^\"]*/\1${interval}ms/" ${TOML_FILE}

# Build base command arguments
BASE_ARGS=(
    "--schema" "${TOML_FILE}"
    "--host" "${EDGE_HOST}"
    "--interval" "${MQTT_PUB_INTERVAL}ms"
    "--exec-duration" "${EXEC_TIME}s"
)

# Process additional arguments
EXTRA_ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --host|--interval|--exec-duration)
            echo "Warning: $1 parameter is predefined in entrypoint and will be ignored" >&2
            shift 2  # Skip parameter value
            ;;
        *)
            EXTRA_ARGS+=("$1")
            shift
            ;;
    esac
done

# Execute command with assembled arguments
/usr/local/bin/mqtt_pub "${BASE_ARGS[@]}" "${EXTRA_ARGS[@]}" > /var/log/mqtt_pub.log 2>&1
while true; do sleep 1; done