from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Union

from tweepy.models import User as user_account

from clients import TwitterClient


@dataclass
class Evaluate:
    twitter = TwitterClient()
    user_info_cache: user_account = None
    tweet_info_cache = None

    def is_valuable_user(self, user_info: Union[int, user_account], tweets=None) -> bool:
        if isinstance(user_info, int):
            user_info = self.twitter.fetch_user_info(id=user_info)
        self.user_info_cache = user_info
        if self.user_info_cache is None:
            return False

        if tweets is None:
            tweets = self.twitter.fetch_user_tweet(id=self.user_info_cache.id)
        self.tweet_info_cache = tweets
        if tweets is None:
            return False

        if not self.is_reliable(self.user_info_cache):
            return False

        if not self.has_valuable_description(self.user_info_cache):
            return False

        if not self.is_active(self.tweet_info_cache):
            return False

        if self.is_business_account(self.user_info_cache):
            return False

        return True

    @staticmethod
    def is_active(tweets) -> bool:
        if tweets is None:
            return False

        has_tweets = len(tweets) > 0
        if not has_tweets:
            return False

        three_days_ago: datetime = datetime.now() - timedelta(days=30)
        return three_days_ago < tweets[0].created_at

    @staticmethod
    def has_valuable_description(user: user_account) -> bool:
        if len(user.description) < 10:
            return False
        return True

    @staticmethod
    def is_reliable(user: user_account) -> bool:
        if user.followers_count < 10:
            return False
        if user.friends_count < 10:
            return False
        if user.favourites_count < 10:
            return False
        if user.protected:
            return False
        return True

    @staticmethod
    def is_likable(tweet):
        # TODO: Issue(Favorited state in search is always false):https://github.com/tweepy/tweepy/issues/1233
        if tweet is None:
            return False
        if tweet.favorited or tweet.retweeted:
            return False
        if tweet.favorite_count > 10 or tweet.retweet_count > 10:
            return False
        return True

    @staticmethod
    def is_business_account(user: user_account):
        if user.verified:
            return True
        return False

    def find_likable_tweet(self, tweets):
        if tweets is None:
            return None
        for i in range(5):
            target_tweet = tweets[i]
            if self.is_likable(target_tweet):
                return target_tweet
        return None
