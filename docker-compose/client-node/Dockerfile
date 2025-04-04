FROM python:3.9-slim

WORKDIR /app

COPY config/config.yaml /app/config.yaml
COPY config/parser.yaml /app/parser.yaml
COPY config/mqtt_datain.py /app/mqtt_datain.py
COPY config/sync_center.py /app/sync_center.py

# RUN apt update -y && apt install -y procps
RUN pip install --no-cache-dir pyyaml requests

ENV EDGE_HOST=localhost
ENV MQTT_HOST=localhost
ENV EDGE_DBNAME=mqtt_datain
ENV CENTER_HOST=localhost
ENV CENTER_DBNAME=center_db

CMD \
[   \
    "sh", \
    "-c", \
    "python3 mqtt_datain.py --edge-host $EDGE_HOST --mqtt-host $MQTT_HOST --edge-dbname $EDGE_DBNAME && \
    python3 sync_center.py --center-host $CENTER_HOST --center-dbname $CENTER_DBNAME --edge-dbname $EDGE_DBNAME --edge-host $EDGE_HOST && \
    while true; do sleep 1; done" \
]
