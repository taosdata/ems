# Dockerfile
FROM ubuntu:22.04

# Download mqtt_pub from nas
ADD http://platform.tdengine.net:8090/download/mqtt_pub /usr/local/bin/mqtt_pub

# set mqtt_pub as executable
RUN chmod +x /usr/local/bin/mqtt_pub

COPY config/ems.toml /etc/mqtt/ems.toml

ENV MQTT_PUB_INTERVAL=1000
ENV EDGE_HOST=flashmq

CMD ["sh", "-c", "/usr/local/bin/mqtt_pub --schema /etc/mqtt/ems.toml --host ${EDGE_HOST} --interval ${MQTT_PUB_INTERVAL}ms > /var/log/mqtt_pub.log 2>&1"]