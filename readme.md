
# Architecture
Postgre(Database) x python


# Usage

## 1. Add a directory named secrets that contains text files below and add each secret info accordingly.
ref: https://developer.twitter.com/ja/docs/basics/authentication/guides/access-tokens
(Go to your twitter account and create app and then you'll get everything.)

1. access_token.txt
2. access_token_secret.txt
3. consumer_key.txt
4. consumer_secret.txt

## 2. Do this
```shell script
make build
docker-compose up
```

make build allows you to access secrets info inside of python container as
environment variable.
