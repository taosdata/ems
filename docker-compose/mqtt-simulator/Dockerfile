FROM ubuntu:22.04

ARG EXEC_TIME=300

# Download mqtt_pub from nas
ADD https://platform.tdengine.net:8090/download/binary_tools/mqtt_pub /usr/local/bin/mqtt_pub

# set mqtt_pub as executable
RUN chmod +x /usr/local/bin/mqtt_pub

COPY config/ems.toml /etc/mqtt/ems.toml

ENV MQTT_PUB_INTERVAL=1000 \
    EDGE_HOST=flashmq \
    EXEC_TIME=${EXEC_TIME}

CMD ["sh", "-c", "/usr/local/bin/mqtt_pub --schema /etc/mqtt/ems.toml --host ${EDGE_HOST} --interval ${MQTT_PUB_INTERVAL}ms --exec-duration ${EXEC_TIME}s > /var/log/mqtt_pub.log 2>&1"]