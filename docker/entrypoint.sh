#!/bin/sh

PROJ_DIR="/app"
CONFIG_DIR="/config"
LOG_FILE="${CONFIG_DIR}/app.log"

mkdir ${CONFIG_DIR}

# if ! [ -z ${PGID} ] || ! [ -z ${PUID} ]; then
#   chown -R ${PUID}:${PGID} ${CONFIG_DIR}
# fi

# Ensure these required files exist
touch ${LOG_FILE}

if ! [ -z ${OZBARGAIN_TIMESTAMP_FILE} ]; then
  touch ${OZBARGAIN_TIMESTAMP_FILE}
fi

if ! [ -z ${OZBARGAIN_TIMESTAMP_FILE_FRONTPAGE} ]; then
  touch ${OZBARGAIN_TIMESTAMP_FILE_FRONTPAGE}
fi

# start crond with log level 8 in foreground, output to stderr
crond -f -d 8
