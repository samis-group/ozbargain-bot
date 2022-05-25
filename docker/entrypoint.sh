#!/bin/sh
echo "entrypoint start..."

PROJ_DIR="/app"
CONFIG_DIR="/config"
LOG_FILE="${CONFIG_DIR}/app.log"

# Ensure these required files exist
touch ${LOG_FILE}

if ! [ -z ${OZBARGAIN_TIMESTAMP_FILE} ]; then
  touch ${OZBARGAIN_TIMESTAMP_FILE}
fi

if ! [ -z ${OZBARGAIN_TIMESTAMP_FILE_FRONTPAGE} ]; then
  touch ${OZBARGAIN_TIMESTAMP_FILE_FRONTPAGE}
fi

# Initial run, because cron runs on a strict 'at every 5th min' interval
if ! [ -z ${RUN_ON_BOOT} ]; then
  python /app/lambda_handler.py >> ${LOG_FILE} 2>&1
fi

# Both PUID and PGID need to be declared, otherwise default to 1
if ! [ -z ${PGID} ] || ! [ -z ${PUID} ]; then
  chown -R ${PUID:-1}:${PGID:-1} ${CONFIG_DIR}
fi

# start crond with log level 8 in foreground, output to stderr
crond -f -d 8
