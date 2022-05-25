# Alpine slim image
FROM python:3-alpine

LABEL maintainer="Sami Shakir"

ENV PROJ_DIR="/app" \
CONFIG_DIR="/config"

ENV LOG_FILE="${CONFIG_DIR}/app.log" \
OZBARGAIN_TIMESTAMP_FILE="${CONFIG_DIR}/oz2slack.timestamp" \
OZBARGAIN_TIMESTAMP_FILE_FRONTPAGE="${CONFIG_DIR}/oz2slack.timestamp.frontpage"

WORKDIR /app
# Copy app source
COPY app .
# Copy entrypoint.sh
COPY docker/entrypoint.sh ./entrypoint.sh
# copy crontab for root user
COPY docker/cronjobs /etc/crontabs/root

# Setup container
RUN pip install pipenv && \
  pipenv install --system && \
  chmod +x /app/entrypoint.sh

# Create an entrypoint script to wrap the container and do fancy things
ENTRYPOINT ["/app/entrypoint.sh"]

# start crond with log level 8 in foreground, output to stderr - Using entrypoint shell script above instead
# CMD ["crond", "-f", "-d", "8"]

# Allow host bind mount of config containing timestamp data and logs
VOLUME /config
