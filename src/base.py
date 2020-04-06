from datetime import datetime
from functools import wraps
from typing import Any
import time

from sqlalchemy.orm import sessionmaker
import tweepy
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


def prevent_from_limit_error(
        *args_,
        request_limit: int = 15,
        window_in_sec: int = 15 * 60,
        recovery_time_in_sec: int = 15 * 60
):
    def decorator(func):
        cache = {}

        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - cache['previous_call']
            is_too_soon = elapsed < window_in_sec
            is_too_many = cache['num_called'] >= request_limit
            is_exceeded_request_limit: bool = is_too_soon and is_too_many
            if is_exceeded_request_limit:
                now_in_unix = datetime.now().timestamp()
                recovery_time_in_sec_ = fetch_request_limit(*args_)['reset'] - now_in_unix \
                    if len(args_) != 0 else recovery_time_in_sec

                BotBase.SLACK_WARNING.send_message(
                    (
                        f'Too many requests for {func.__name__}'
                        f"let's sleep {recovery_time_in_sec_} seconds."
                    )
                )
                time.sleep(recovery_time_in_sec_)
                cache['num_called'] = 0

            cache['previous_call'] = time.time()
            cache['num_called'] += 1
            print(f'{func.__name__}_cache_inside: {cache}')
            return func(*args, **kwargs)
        cache = {
            'num_called': 0,
            'previous_call': time.time(),
            'request_limit': fetch_request_limit(*args_)['limit'] if len(args_) != 0 else request_limit,
        }
        print(f'{func.__name__}_cache_outside: {cache}')
        return wrapper

    def fetch_request_limit(*args) -> Any:
        """

        Returns:

        Notes:
            API Document xxx

        """
        for _ in range(RETRY_NUM):
            try:
                status = BotBase.API.rate_limit_status()
            except RateLimitError:
                BotBase.SLACK_WARNING.send_message(
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

    return decorator
