import time
from typing import Optional, Set

import tweepy
from tweepy import models
from tweepy.error import RateLimitError, TweepError

from .mixins import TwitterCredentialMixin
from .utils import prevent_from_limit_error
from .slack_client import (
    SLACK_WARNING,
    SLACK_ERROR,
)
from utils import (
    RETRY_NUM,
    REQUEST_LIMIT_RECOVERY_TIME_IN_SECOND,
)


class TwitterBase:
    pass


class TwitterClient(
    TwitterBase,
    TwitterCredentialMixin
):

    @prevent_from_limit_error(
        'search',
        '/search/tweets',
        window_in_sec=15 * 60,
        recovery_time_in_sec=15 * 60
    )
    def fetch_tweets_by_keyword(self, **kwargs):
        """

        Args:
            **kwargs:

        Returns:

        Examples:
            TODO Fix the annotation
            >>>search_results: models.SearchResults[models.Status] = LikeBot().fetch_tweets_by_keyword(q='python', lang='ja', count=100)
            >>>search_results
            Status(_api=<tweepy.api.API object at 0x7fc01e3012b0>,...)

        Notes:
            100 is the limit of tweets that can be fetched at a time.
            ref: https://developer.twitter.com/en/docs/tweets/search/api-reference/get-search-tweets
            Issue(Favorited state in search is always false):https://github.com/tweepy/tweepy/issues/1233
        """
        if 'lang' not in kwargs.keys():
            kwargs['lang'] = 'ja'
        if 'count' not in kwargs.keys():
            kwargs['count'] = 100
        for _ in range(RETRY_NUM):
            try:
                return self.api.search(**kwargs)
            except RateLimitError:
                time.sleep(REQUEST_LIMIT_RECOVERY_TIME_IN_SECOND)
                SLACK_WARNING.send_message(
                    (
                        'WARNING: Rate limit error occurred in fetch_tweets_by_keyword'
                        'Sleep for 15min..zzzz'
                    )
                )
                continue
            except TweepError as e:
                if e.response is None:
                    SLACK_WARNING.send_message(
                        f'WARNING: None response received in fetch_tweets_by_keyword.'
                    )
                    SLACK_WARNING.send_message(
                        f'Reason is {e.reason}'
                    )
                    return []
                raise

    @prevent_from_limit_error(
        request_limit=15,
        window_in_sec=15 * 60,
        recovery_time_in_sec=15 * 60
    )
    def like_tweet(self, **kwargs):
        """

        Args:
            **kwargs:

        Returns:

        Notes:
            Requests / 24-hour window	1000 per user; 1000 per app
            https://developer.twitter.com/en/docs/tweets/post-and-engage/api-reference/post-favorites-create
        """
        for _ in range(RETRY_NUM):
            try:
                return self.api.create_favorite(**kwargs)
            except TweepError as e:
                if e.response is None:
                    SLACK_WARNING.send_message(
                        f'WARNING: None response received in like_tweet.'
                    )
                    SLACK_WARNING.send_message(
                        f'Reason is {e.reason}'
                    )
                    return None
                if e.response.status_code == 403:
                    # TODO: Should either get all of my favourites or save them in db.
                    SLACK_WARNING.send_message(
                        (
                            'WARNING: This tweet has been liked.'
                        )
                    )
                    return
                elif e.response.status_code == 429:
                    SLACK_ERROR.send_message(
                        (
                            "Like request limit has been exceeded. Let's sleep 24hours"
                        )
                    )
                    time.sleep(24 * 60 * 60)
                    return
                raise

    @prevent_from_limit_error(
        'users',
        '/users/show/:id',
        window_in_sec=15 * 60,
        recovery_time_in_sec=15 * 60
    )
    def fetch_user_info(self, **kwargs) -> Optional[models.User]:
        """

        Args:
            **kwargs:

        Returns:

        Notes:
            api docs
        """
        for _ in range(RETRY_NUM):
            try:
                return self.api.get_user(**kwargs)
            except RateLimitError:
                time.sleep(REQUEST_LIMIT_RECOVERY_TIME_IN_SECOND)
                SLACK_WARNING.send_message(
                    (
                        'WARNING: Rate limit error occurred in fetch_user_info'
                        'Sleep for 15min..zzzz'
                    )
                )
                continue
            except TweepError as e:
                if e.response is None:
                    SLACK_WARNING.send_message(
                        f'WARNING: None response received in fetch_user_info.'
                    )
                    SLACK_WARNING.send_message(
                        f'Reason is {e.reason}'
                    )
                    return None
                if e.response.status_code == 401:
                    """Not Authorized(protected account)"""
                    SLACK_WARNING.send_message(f'WARNING: This user is protected{str(kwargs)}')
                    return None
                raise e

    @prevent_from_limit_error(
        'statuses',
        '/statuses/user_timeline',
        window_in_sec=15 * 60,
        recovery_time_in_sec=15 * 60
    )
    def fetch_user_tweet(self, **kwargs) -> Optional[models.User]:
        """

        Args:
            **kwargs:

        Returns:

        Notes:
            api docs
        """
        for _ in range(RETRY_NUM):
            try:
                return self.api.user_timeline(**kwargs)
            except RateLimitError:
                time.sleep(REQUEST_LIMIT_RECOVERY_TIME_IN_SECOND)
                SLACK_WARNING.send_message('WARNING: Rate limit error occurred! Sleep for 15min..zzzz')
                continue
            except TweepError as e:
                if e.response is None:
                    SLACK_WARNING.send_message(
                        f'WARNING: None response received in fetch_user_tweet.'
                    )
                    SLACK_WARNING.send_message(
                        f'Reason is {e.reason}'
                    )
                    return None
                if e.response.status_code == 401:
                    """Not Authorized(protected account)"""
                    SLACK_WARNING.send_message(f'WARNING: This user is protected{str(kwargs)}')
                    return None
                raise e

    @prevent_from_limit_error(
        'followers',
        '/followers/ids',
        window_in_sec=15 * 60,
        recovery_time_in_sec=15 * 60
    )
    def fetch_user_follower_ids(self, user_id: str) -> Set[int]:
        followers_ids_iter = tweepy.Cursor(self.api.followers_ids, id=user_id).pages()
        all_ids: Set[int] = set()
        while True:
            try:
                ids = next(followers_ids_iter)
            except RateLimitError:
                time.sleep(REQUEST_LIMIT_RECOVERY_TIME_IN_SECOND)
                SLACK_WARNING.send_message('WARNING: Rate limit error occurred! Sleep for 15min..zzzz')
                continue
            except StopIteration:
                break
            except TweepError as e:
                if e.response is None:
                    SLACK_WARNING.send_message(
                        f'WARNING: None response received in fetch_user_follower_ids.'
                    )
                    SLACK_WARNING.send_message(
                        f'Reason is {e.reason}'
                    )
                    return all_ids
                if e.response.status_code == 401:
                    """ID that does not exist"""
                    SLACK_ERROR.send_message(f'ID:{user_id} does not exist')
                raise e

            for id_ in ids:
                all_ids.add(id_)

        return all_ids
