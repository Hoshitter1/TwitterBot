import tweepy

from utils import (
    CONSUMER_KEY,
    CONSUMER_SECRET,
    ACCESS_TOKEN,
    ACCESS_TOKEN_SECRET,
    SLACK_TOKEN
)


class CredentialMixinBase:
    def __init__(self):
        raise NotImplementedError


class TwitterCredentialMixin(CredentialMixinBase):

    def __init__(self):
        __auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        __auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
        self.__api = tweepy.API(__auth)

    # TODO: api should not belong to credential
    @property
    def api(self):
        return self.__api


class SlackCredentialMixin(CredentialMixinBase):

    def __init__(self, channel: str):
        self._token = SLACK_TOKEN
        self._headers = {'Content-Type': 'application/json'}
        self._channel = channel
