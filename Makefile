.PHONY: env stop rm image-rm build build-no-cache run exec base-shell

image_name = ozbargain-bot

up: build-no-cache run

down: stop rm image-rm

rebuild: stop rm image-rm build-no-cache run

# Writes your webhooks to the docker/.env file (deletes if existing so they don't dupe ad infinitum)
env:
	@read -p "slack webhook (leave blank if n/a): " OZBARGAIN_SLACK_WEBHOOK;\
	read -p "slack_frontpage webhook (leave blank if n/a): " OZBARGAIN_SLACK_WEBHOOK_FRONTPAGE;\
	read -p "discord webhook (leave blank if n/a): " OZBARGAIN_DISCORD_WEBHOOK;\
	read -p "discord_frontpage webhook (leave blank if n/a): " OZBARGAIN_DISCORD_WEBHOOK_FRONTPAGE;\
	read -p "Verbose (true/false - leave blank if n/a): " OZBARGAIN_VERBOSE;\
	read -p "Timestamp Override (integer - do you want to override the timestamp that is set on each 5 min interval, useful for testing - leave blank if n/a): " OZBARGAIN_TIMESTAMP_OVERRIDE;\
	read -p "Run on container boot as well as cron (<any user input = true> - Run the script on initial container boot as well as cron - leave blank if only cron): " RUN_ON_BOOT;\
	read -p "PUID (most likely 'id -u' for you - leave blank if n/a): " PUID;\
	read -p "PGID (most likely 'id -g' for you - leave blank if n/a): " PGID;\
	ENV_FILE="${PWD}/docker/.env";\
	touch "$${ENV_FILE}";\
	if ! [ -z "$${OZBARGAIN_SLACK_WEBHOOK}" ]; then\
		echo "Writing OZBARGAIN_SLACK_WEBHOOK...";\
		sed -i '/OZBARGAIN_SLACK_WEBHOOK=/d' $${ENV_FILE};\
		echo "OZBARGAIN_SLACK_WEBHOOK=$${OZBARGAIN_SLACK_WEBHOOK}" >> "$${ENV_FILE}";\
	fi;\
	if ! [ -z "$${OZBARGAIN_SLACK_WEBHOOK_FRONTPAGE}" ]; then\
		echo "Writing OZBARGAIN_SLACK_WEBHOOK_FRONTPAGE...";\
		sed -i '/OZBARGAIN_SLACK_WEBHOOK_FRONTPAGE=/d' $${ENV_FILE};\
		echo "OZBARGAIN_SLACK_WEBHOOK_FRONTPAGE=$${OZBARGAIN_SLACK_WEBHOOK_FRONTPAGE}" >> "$${ENV_FILE}";\
	fi;\
	if ! [ -z "$${OZBARGAIN_DISCORD_WEBHOOK}" ]; then\
		echo "Writing OZBARGAIN_DISCORD_WEBHOOK...";\
		sed -i '/OZBARGAIN_DISCORD_WEBHOOK=/d' $${ENV_FILE};\
		echo "OZBARGAIN_DISCORD_WEBHOOK=$${OZBARGAIN_DISCORD_WEBHOOK}" >> "$${ENV_FILE}";\
	fi;\
	if ! [ -z "$${OZBARGAIN_DISCORD_WEBHOOK_FRONTPAGE}" ]; then\
		echo "Writing OZBARGAIN_DISCORD_WEBHOOK_FRONTPAGE...";\
		sed -i '/OZBARGAIN_DISCORD_WEBHOOK_FRONTPAGE=/d' $${ENV_FILE};\
		echo "OZBARGAIN_DISCORD_WEBHOOK_FRONTPAGE=$${OZBARGAIN_DISCORD_WEBHOOK_FRONTPAGE}" >> "$${ENV_FILE}";\
	fi;\
	if ! [ -z "$${OZBARGAIN_TIMESTAMP_OVERRIDE}" ]; then\
		echo "Writing OZBARGAIN_TIMESTAMP_OVERRIDE...";\
		sed -i '/OZBARGAIN_TIMESTAMP_OVERRIDE=/d' $${ENV_FILE};\
		echo "OZBARGAIN_TIMESTAMP_OVERRIDE=$${OZBARGAIN_TIMESTAMP_OVERRIDE}" >> "$${ENV_FILE}";\
	fi;\
	if ! [ -z "$${OZBARGAIN_VERBOSE}" ]; then\
		echo "Writing OZBARGAIN_VERBOSE...";\
		sed -i '/OZBARGAIN_VERBOSE=/d' $${ENV_FILE};\
		echo "OZBARGAIN_VERBOSE=$${OZBARGAIN_VERBOSE}" >> "$${ENV_FILE}";\
	fi;\
	if ! [ -z "$${RUN_ON_BOOT}" ]; then\
		echo "Writing RUN_ON_BOOT...";\
		sed -i '/RUN_ON_BOOT=/d' $${ENV_FILE};\
		echo "RUN_ON_BOOT=$${RUN_ON_BOOT}" >> "$${ENV_FILE}";\
	fi;\
	if ! [ -z "$${PUID}" ]; then\
		echo "Writing PUID...";\
		sed -i '/PUID=/d' $${ENV_FILE};\
		echo "PUID=$${PUID}" >> "$${ENV_FILE}";\
	fi;\
	if ! [ -z "$${PGID}" ]; then\
		echo "Writing PGID...";\
		sed -i '/PGID=/d' $${ENV_FILE};\
		echo "PGID=$${PGID}" >> "$${ENV_FILE}";\
	fi

setup: env
	@mkdir -p ${PWD}/ozbargain
	@touch ${PWD}/ozbargain/app.log
	@touch ${PWD}/ozbargain/oz2slack.timestamp
	@touch ${PWD}/ozbargain/oz2slack.timestamp.frontpage

stop-rm: stop rm

stop:
	@docker stop $(image_name)

rm:
	@docker rm $(image_name)

image-rm:
	@docker image rm $(image_name)

build-run: build run

build:
	@docker build -t $(image_name) -f docker/Dockerfile .

build-no-cache:
	@docker build --no-cache -t $(image_name) -f docker/Dockerfile .

run:
	@docker run -d \
	--user="$(id -u):$(id -u)" \
	--name=$(image_name) \
	--restart unless-stopped \
	-v ${PWD}/ozbargain:/config \
	--env-file ${PWD}/docker/.env \
	$(image_name)

exec:
	@docker exec -it $(image_name) /bin/sh

# Make a brand new container from the base image and enter shell (Useful for dev in docker containers)
base-shell:
	@docker run --rm -it $(image_name) /bin/sh

compose-up:
	@docker compose --env-file ./docker/.env -f ./docker/docker-compose.yml up -d

compose-down:
	@docker compose --env-file ./docker/.env -f ./docker/docker-compose.yml down
