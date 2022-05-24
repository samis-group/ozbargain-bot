
image_name = ozbargain

rebuild: stop rm image-rm build-no-cache run

setup:
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
	@docker build -t $(image_name) .

build-no-cache:
	@docker build --no-cache -t $(image_name) .

run:
	@docker run -d \
	--name=$(image_name) \
	--restart unless-stopped \
	-e OZBARGAIN_SLACK_WEBHOOK=${OZBARGAIN_SLACK_WEBHOOK} \
	-e OZBARGAIN_SLACK_WEBHOOK_FRONTPAGE=${OZBARGAIN_SLACK_WEBHOOK_FRONTPAGE} \
	-v ${PWD}/ozbargain:/config \
	--env-file ${PWD}/.env \
	$(image_name)

exec:
	@docker exec -it $(image_name) /bin/sh
