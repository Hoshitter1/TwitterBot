
# Architecture
Postgre(Database) x python


# What does this bot do?
TwitterBot will collect Twitter IDs of users that follow your target celebrities managed in `scr/target_list`,
and at the same time it will like tweets searched by keywords mentioned in `utils/settings.py`.
Slack will be used to notify about the process.


# Usage

## 1. Add a directory named secrets that contains text files below and add each secret info accordingly.
ref: https://developer.twitter.com/ja/docs/basics/authentication/guides/access-tokens
(Go to your twitter account and create app and then you'll get everything.)

1. access_token.txt
2. access_token_secret.txt
3. consumer_key.txt
4. consumer_secret.txt
5. slack_token.txt


## 2. Add a directory named target lists under src and include text files.
Include twitter IDs of your target celebrities in target_lists so user_bot will save their followers based on their values.


## 2. Do this
```shell script
make build
docker-compose up
```

For debug python
```shell script
make debug
```

For exection
```shell script
make exec
```

make build allows you to access secrets info inside of python container as
environment variable.
