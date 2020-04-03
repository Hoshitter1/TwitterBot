from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Set, List, Dict, Union
import time

from sqlalchemy.orm import sessionmaker
import tweepy
from tweepy import models
from tweepy.error import RateLimitError

from utils import *
from slack_client import Slack


class BotBase:
    AUTH = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    AUTH.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    API = tweepy.API(AUTH)
    SLACK_INFO = Slack('#twitter_bot_info')
    SLACK_WARNING = Slack('#twitter_bot_warning')
    SLACK_ERROR = Slack('#twitter_bot_error')

    @property
    def get_session(self):
        session = sessionmaker(bind=ENGINE)
        return session()

    @classmethod
    def fetch_request_limit_remaining(cls, *args, **kwargs) -> Any:
        """15 calls every 15 minutes

        Returns:

        Notes:
            API Document xxx

        """
        # TODO: Create cache
        for _ in range(RETRY_NUM):
            try:
                status = cls.API.rate_limit_status()
            except RateLimitError:
                cls.SLACK_WARNING.send_message(
                    (
                        'WARNING: Woops Rate limit (fetch_request_limit_remaining in Base) '
                        'error occurred! Sleep for 15min..zzzz'
                    )
                )
                time.sleep(REQUEST_LIMIT_RECOVERY_TIME_IN_SECOND)
                continue
            break
        outer = status.get('resources', {})
        inner: Any
        for target in args:
            inner = outer.get(target, None)
            if inner is None:
                break
            outer = inner
        return inner
