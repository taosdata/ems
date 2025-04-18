FROM python:3.10-slim

ARG WORKDIR=/app
ARG TD_VERSION=3.3.6.0
ARG EXEC_TIME=300
ARG ENABLE_COMPRESSION=true



WORKDIR $WORKDIR
ENV DEBIAN_FRONTEND=noninteractive \
    EDGE_HOST=localhost \
    MQTT_HOST=localhost \
    EDGE_DBNAME=mqtt_datain \
    CENTER_HOST=localhost \
    CENTER_DBNAME=center_db \
    EXEC_TIME=${EXEC_TIME} \
    WORKDIR=${WORKDIR} \
    TD_VERSION=${TD_VERSION} \
    ENABLE_COMPRESSION=${ENABLE_COMPRESSION} \
    MQTT_PUB_INTERVAL=1000
    # GITHUB_OUTPUT=/dev/null

# ADD scripts/generate_role_info.sh ${WORKDIR}/
# ADD ./TDengine-enterprise-client-${TD_VERSION}-Linux-x64.tar.gz ${WORKDIR}

RUN apt update -y && \
    apt install -y python3-pip jq && \
    wget https://www.taosdata.com/assets-download/3.0/TDengine-enterprise-client-${TD_VERSION}-Linux-x64.tar.gz && \
    tar -xf TDengine-enterprise-client-${TD_VERSION}-Linux-x64.tar.gz && \
    cd TDengine-enterprise-client-${TD_VERSION} && \
    /bin/bash install_client.sh -e no && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/

COPY config/config.yaml config/parser.yaml \
     scripts/*.py config/query.json \
     ${WORKDIR}/
# RUN apt update -y && apt install -y procps
RUN pip install --no-cache-dir pyyaml requests

# ARG PUB_DL_URL=https://platform.tdengine.net:8090/download
# ARG TEST_ROOT=/app/ems/tests
# ARG PIP_SOURCE=https://pypi.tuna.tsinghua.edu.cn/simple

# RUN apt update -y && \
#     apt install -y python3-pip git wget jq  && \
#     git clone https://github.com/taosdata/ems.git && \
#     git clone https://github.com/taosdata/.github.git && \
#     ${WORKDIR}/generate_role_info.sh && \
#     ${WORKDIR}/.github/.github/scripts/deploy_taostest.sh ${PUB_DL_URL} ${TEST_ROOT} ${PIP_SOURCE} && \
#     ${WORKDIR}/.github/.github/scripts/gen_taostest_env.sh ${WORKDIR}/role_info.json ${TEST_ROOT} && \
#     # wget https://www.taosdata.com/assets-download/3.0/TDengine-enterprise-client-${TD_VERSION}-Linux-x64.tar.gz && \
#     # tar -xf TDengine-enterprise-client-${TD_VERSION}-Linux-x64.tar.gz && \
#     ADD TDengine-enterprise-client-${TD_VERSION}-Linux-x64.tar.gz ${WORKDIR} && \
#     cd TDengine-enterprise-client-${TD_VERSION} && \
#     /bin/bash install_client.sh -e no && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/
#     # taostest --convert-json=ems-center.json && \
#     # taostest --convert-json=ems-query.json
#     # taostest --setup=ems-center.yaml --case=customer_scenarios/ems/start.py --keep

CMD \
[   \
    "sh", \
    "-c", \
    "test_start_time=$(date +%Y%m%d_%H%M%S)  && \
    echo '{}' | jq --arg test_start_time $test_start_time '. + {test_start_time: $test_start_time}' > ${WORKDIR}/test_env.json && \
    python3 mqtt_datain.py --edge-host $EDGE_HOST --mqtt-host $MQTT_HOST --edge-dbname $EDGE_DBNAME && \
    python3 sync_center.py --center-host $CENTER_HOST --center-dbname $CENTER_DBNAME --edge-dbname $EDGE_DBNAME --edge-host $EDGE_HOST && \
    sleep ${EXEC_TIME} && \
    python3 stop.py && \
    taosBenchmark -f ${WORKDIR}/query.json > ${WORKDIR}/query_result.txt && \
    python3 summary.py && \
    while true; do sleep 1; done" \
]


