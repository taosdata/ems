# Dockerfile
FROM ubuntu:22.04

# Download mqtt_pub from nas
ADD http://platform.tdengine.net:8090/download/mqtt_pub /usr/local/bin/mqtt_pub

# set mqtt_pub as executable
RUN chmod +x /usr/local/bin/mqtt_pub

COPY config/fractal.toml /etc/mqtt/fractal.toml

ENV MQTT_PUB_INTERVAL=1000
ENV EDGE_HOST=flashmq

CMD ["sh", "-c", "/usr/local/bin/mqtt_pub --schema /etc/mqtt/fractal.toml --host ${EDGE_HOST} --interval ${MQTT_PUB_INTERVAL}ms > /var/log/mqtt_pub.log 2>&1"]