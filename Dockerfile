FROM python:3-alpine

LABEL maintainer="Sami Shakir"

ENV PROJ_DIR="/app" \
CONFIG_DIR="/config"

ENV LOG_FILE="${CONFIG_DIR}/app.log" \
OZBARGAIN_TIMESTAMP_FILE="${CONFIG_DIR}/oz2slack.timestamp" \
OZBARGAIN_TIMESTAMP_FILE_FRONTPAGE="${CONFIG_DIR}/oz2slack.timestamp.frontpage"

# Copy app source
COPY app ${PROJ_DIR}

# copy crontab for root user
COPY docker/cronjobs /etc/crontabs/root

# Copy entrypoint.sh
COPY docker/entrypoint.sh /app/entrypoint.sh

# Setup container
WORKDIR ${PROJ_DIR}
RUN pip install pipenv && \
  pipenv install --system && \
  printenv > /etc/environment && \
  chmod +x /app/entrypoint.sh
  # crontab /etc/crontabs/root

# Run it initially as the container boots because cron won't run it as it loads - not working, not providing a stack trace either..
# RUN python ${PROJ_DIR}/lambda_handler.py >> ${LOG_FILE} 2>&1

# Create an entrypoint script to wrap the container and do things
ENTRYPOINT ["/app/entrypoint.sh"]

# start crond with log level 8 in foreground, output to stderr
# CMD ["crond", "-f", "-d", "8"]

# crond runs per default in the background
# CMD crond && tail -f ${LOG_FILE}

VOLUME ${CONFIG_DIR}
