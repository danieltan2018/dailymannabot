# Local development. CI does the same steps in .github/workflows/deploy.yml.
STACK   := devotion-bots
CHANNEL ?= psalms

.PHONY: test build deploy invoke logs

test:
	python3 -m unittest

build:
	sam build

## Deploy from your machine. Needs BOT_TOKEN in the environment; ALARM_EMAIL is optional.
deploy: build
	@test -n "$(BOT_TOKEN)" || (echo "BOT_TOKEN is not set" && exit 1)
	@sam deploy --parameter-overrides BotToken=$(BOT_TOKEN) AlarmEmail=$(ALARM_EMAIL)

## Send a channel's devotion now. Override DATE=YYYY-MM-DD and CHAT_ID=@somewhere to test safely.
invoke:
	sam remote invoke --stack-name $(STACK) DevotionFunction \
	  --event '{"channel": "$(CHANNEL)", "date": "$(DATE)", "chat_id": "$(CHAT_ID)"}'

logs:
	sam logs --stack-name $(STACK) --name DevotionFunction --tail
