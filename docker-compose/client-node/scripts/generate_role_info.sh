#!/bin/bash

CLIENT_HOSTS=$(echo "$CLIENT_HOST" | tr ',' ' ')
EDGE_HOSTS=$(echo "$EDGE_HOST" | tr ',' ' ')
MQTT_HOSTS=$(echo "$MQTT_HOST" | tr ',' ' ')
CENTER_HOSTS=$(echo "$CENTER_HOST" | tr ',' ' ')

JSON='{
  "mqtt": [],
  "center": [],
  "client": [],
  "edge": []
}'

resolve_and_add() {
  local role="$1"
  local hosts="$2"

  for hostname in $hosts; do
    IP=$(getent ahosts "$hostname" | awk '{ print $1 }' | head -n 1)
    if [ -n "$IP" ]; then
      ENTRY=$(jq -n --arg hn "$hostname" --arg ip "$IP" '{ "hostname": $hn, "ip": $ip }')
      JSON=$(echo "$JSON" | jq --argjson entry "$ENTRY" ".$role += [\$entry]")
    else
      echo "Warning: Could not resolve $hostname"
    fi
  done
}

resolve_and_add "client" "$CLIENT_HOSTS"
resolve_and_add "edge" "$EDGE_HOSTS"
resolve_and_add "mqtt" "$MQTT_HOSTS"
resolve_and_add "center" "$CENTER_HOSTS"

echo "$JSON" | jq '.' > "role_info.json"

echo "✅ Generated $OUTPUT_FILE"