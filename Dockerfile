FROM python:3-alpine

LABEL maintainer="Sami Shakir"

ENV PROJ_DIR="/app"
ENV CONFIG_DIR="/config"
ENV LOG_FILE="${CONFIG_DIR}/app.log"
ENV CRON_SPEC="*/5 * * * *"

# App ENV vars declared
ENV OZBARGAIN_TIMESTAMP_FILE="${CONFIG_DIR}/oz2slack.timestamp"
ENV OZBARGAIN_TIMESTAMP_FILE_FRONTPAGE="${CONFIG_DIR}/oz2slack.timestamp.frontpage"

RUN mkdir ${PROJ_DIR} ${CONFIG_DIR}
COPY app ${PROJ_DIR}

WORKDIR ${PROJ_DIR}
RUN pip install pipenv && \
  touch ${LOG_FILE} && \
  echo "${CRON_SPEC} python ${PROJ_DIR}/lambda_handler.py >> ${LOG_FILE} 2>&1" > /etc/crontab && \
  pipenv install --system && \
  printenv > /etc/environment && \
  crontab /etc/crontab

# Run it initially as the container boots because cron won't run it as it loads - not working, not providing a stack trace either..
# RUN python ${PROJ_DIR}/lambda_handler.py >> ${LOG_FILE} 2>&1

# crond runs per default in the background
CMD crond && tail -f ${LOG_FILE}

VOLUME ${CONFIG_DIR}
