
image_name = ozbargain_bot

rebuild: stop rm image-rm build-no-cache run

setup:
	@mkdir -p ${PWD}/ozb/config
	@touch ${PWD}/ozb/config/app.log
	@touch ${PWD}/ozb/config/oz2slack.timestamp
	@touch ${PWD}/ozb/config/oz2slack.timestamp.frontpage

stop-rm: stop rm

stop:
	@docker stop $(image_name)

rm:
	@docker rm $(image_name)

image-rm:
	@docker image rm $(image_name)

build-run: build run

build:
	@docker build -t $(image_name) .

build-no-cache:
	@docker build --no-cache -t $(image_name) .

run:
	@docker run -d \
  --name=ozbargain_bot \
	--user $(id -u):$(id -u) \
  -e OZBARGAIN_SLACK_WEBHOOK=${OZBARGAIN_SLACK_WEBHOOK} \
	-e TZ=${TZ} \
  -v "${PWD}/ozb/config:/config" \
  --restart unless-stopped \
  ozbargain_bot

exec:
	@docker exec -it $(image_name) /bin/sh
