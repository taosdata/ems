FROM python:3.10-slim

ARG WORKDIR=/app
ARG ENTERPRISE_CLIENT_VERSION=3.3.6.0

WORKDIR $WORKDIR
ENV DEBIAN_FRONTEND=noninteractive \
    EDGE_HOST=localhost \
    MQTT_HOST=localhost \
    EDGE_DBNAME=mqtt_datain \
    CENTER_HOST=localhost \
    CENTER_DBNAME=center_db

RUN apt update -y && \
    apt install -y python3-pip git wget  && \
    git clone https://github.com/taosdata/ems.git && \
    pip install --no-cache-dir https://platform.tdengine.net:8090/download/wheels/taostest-0.1.5-py3-none-any.whl -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    wget https://www.taosdata.com/assets-download/3.0/TDengine-enterprise-client-${ENTERPRISE_CLIENT_VERSION}-Linux-x64.tar.gz && \
    tar -xf TDengine-enterprise-client-${ENTERPRISE_CLIENT_VERSION}-Linux-x64.tar.gz && \
    cd TDengine-enterprise-client-${ENTERPRISE_CLIENT_VERSION} && \
    /bin/bash install_client.sh -e no && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/

COPY config/config.yaml /app/config.yaml
COPY config/parser.yaml /app/parser.yaml
COPY config/mqtt_datain.py /app/mqtt_datain.py
COPY config/sync_center.py /app/sync_center.py

# RUN apt update -y && apt install -y procps
RUN pip install --no-cache-dir pyyaml requests



CMD \
[   \
    "sh", \
    "-c", \
    "python3 mqtt_datain.py --edge-host $EDGE_HOST --mqtt-host $MQTT_HOST --edge-dbname $EDGE_DBNAME && \
    python3 sync_center.py --center-host $CENTER_HOST --center-dbname $CENTER_DBNAME --edge-dbname $EDGE_DBNAME --edge-host $EDGE_HOST && \
    while true; do sleep 1; done" \
]
