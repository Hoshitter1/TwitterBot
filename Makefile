
DB_USERNAME := user_dev
DB_NAME := develop_db
$(eval ACCESS_TOKEN := $(shell cat secrets/access_token.txt))
$(eval ACCESS_TOKEN_SECRET := $(shell cat secrets/access_token_secret.txt))
$(eval CONSUMER_KEY := $(shell cat secrets/consumer_key.txt))
$(eval CONSUMER_SECRET := $(shell cat secrets/consumer_secret.txt))
$(eval SLACK_TOKEN := $(shell cat secrets/slack_token.txt))

database: #See what's in database
	docker exec -it twitter_db bash -c "psql -U $(DB_USERNAME) -d $(DB_NAME)"

clean_db: #[BE CAREFUL] this deletes all migration history so that you can test various model structus
	docker-compose down -v

build:
	docker-compose build --build-arg ACCESS_TOKEN=$(ACCESS_TOKEN) \
	                     --build-arg ACCESS_TOKEN_SECRET=$(ACCESS_TOKEN_SECRET) \
	                     --build-arg CONSUMER_KEY=$(CONSUMER_KEY) \
	                     --build-arg CONSUMER_SECRET=$(CONSUMER_SECRET) \
	                     --build-arg SLACK_TOKEN=$(SLACK_TOKEN)
debug:
	docker-compose run src bash

exec:
	docker-compose run -d src python main_bot.py

