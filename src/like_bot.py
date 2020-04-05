from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Set, List, Optional, Tuple, Union
import time

import tweepy
from tweepy import models
from tweepy.error import RateLimitError, TweepError

from base import BotBase
from utils import *
from models.users import ValuableUsers
from user_bot import UserBot


@dataclass
class LikeBot(BotBase):
    user_bot = UserBot()

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
                return self.API.search(**kwargs)
            except RateLimitError:
                time.sleep(REQUEST_LIMIT_RECOVERY_TIME_IN_SECOND)
                self.SLACK_WARNING.send_message(
                    (
                        'WARNING: Rate limit error occurred in fetch_tweets_by_keyword'
                        'Sleep for 15min..zzzz'
                    )
                )
                continue
            except TweepError:
                raise

    def like_tweet(self, **kwargs):
        for _ in range(RETRY_NUM):
            try:
                return self.API.create_favorite(**kwargs)
            except RateLimitError:
                time.sleep(REQUEST_LIMIT_RECOVERY_TIME_IN_SECOND)
                self.SLACK_WARNING.send_message(
                    (
                        'WARNING: Rate limit error occurred in like_tweet'
                        'Sleep for 15min..zzzz'
                    )
                )
                continue
            except TweepError as e:
                if e.response.status_code == 403:
                    # TODO: Should either get all of my favourites or save them in db.
                    self.SLACK_WARNING.send_message(
                        (
                            'WARNING: This tweet has been liked.'
                        )
                    )
                    return
                raise

    def fetch_users_with_likes_less_than_threshold_from_db(
            self,
            data_num: int = 50,
            threshold_likes: int = 3
    ) -> List[models.User]:
        """

        Args:
            data_num:
            threshold_likes:

        Returns:

        Examples:
            >>> users = LikeBot().fetch_users_with_likes_less_than_threshold_from_db(data_num=10)
            >>> len(users)
            10
            >>> users[0].user_id
            1237950324255502336
            >>> users[0].screen_name
            '虚実の海の彷徨者'
            >>> users[0].is_friend
            False
            >>> users[0].num_likes
            0
        """
        session = self.get_session
        target_users: List[int] = []

        for threshold in range(threshold_likes):
            users_in_db: List[ValuableUsers] = session.query(ValuableUsers).filter(
                ValuableUsers.num_likes == threshold).all()
            target_users.extend(users_in_db[:data_num])
            if len(target_users[:data_num]) == data_num:
                session.close()
                return users_in_db[:data_num]

        self.SLACK_WARNING(
            'There is not enough number of users to like. Update user database immediately.'
        )
        session.close()
        return target_users

    @staticmethod
    def is_likable(tweet):
        if tweet.favorited or tweet.retweeted:
            return False
        if tweet.favorite_count > 10 or tweet.retweet_count > 10:
            return False
        return True

    @classmethod
    def find_likable_tweet(cls, tweets):
        for i in range(5):
            target_tweet = tweets[i]
            if cls.is_likable(target_tweet):
                return target_tweet
        return None

    def like_tweet_from_users_in_db(self, data_num: int):
        users: List[ValuableUsers] = self.fetch_users_with_likes_less_than_threshold_from_db(
            data_num=data_num
        )
        session = self.get_session
        # TODO: This code looks ugly, fix it
        total_like_tweets: int = 0
        for user in users:
            tweets = self.user_bot.fetch_user_tweet(id=user.user_id)
            likable_tweet = self.find_likable_tweet(tweets)
            if likable_tweet is None:
                continue
            self.like_tweet(id=likable_tweet.id)
            user_model = session.query(ValuableUsers).filter(ValuableUsers.user_id == user.user_id).first()
            user_model.num_likes += 1
            session.commit()
            total_like_tweets += 1
        session.close()
        self.SLACK_INFO.send_message(f'{total_like_tweets} tweets have been liked.')

    def like_from_keyword(self, search_word: str, num_to_like: int):
        self.SLACK_INFO.send_message(f'1/4: Fetch tweets by search_word「{search_word}」')
        tweets = self.fetch_tweets_by_keyword(q=search_word, count=100)

        self.SLACK_INFO.send_message(f"2/4: filter {len(tweets)}tweets based on user's value")
        filtered_tweets_by_user_info = [
            tweet
            for tweet in tweets
            if self.user_bot.is_valuable_user(tweet.author)
        ]

        self.SLACK_INFO.send_message(
            f"2/4: filter {len(filtered_tweets_by_user_info)}tweets based on tweet's likability"
        )
        filtered_tweets_by_likability = [
            tweet
            for tweet in filtered_tweets_by_user_info
            if self.is_likable(tweet)
        ]

        target_tweets_to_like = filtered_tweets_by_likability[:num_to_like]
        if len(target_tweets_to_like) < num_to_like:
            self.SLACK_WARNING.send_message(
                f'Could not find {num_to_like} tweets to like.'
                f'I only found {len(target_tweets_to_like)}...Sorry bro.'
            )

        self.SLACK_INFO.send_message(f"3/4: Like them all {len(target_tweets_to_like)}")
        users_to_save = []
        for tweet in target_tweets_to_like:
            status = self.like_tweet(id=tweet.id)
            if status is not None:
                users_to_save.append(tweet.author)

        self.SLACK_INFO.send_message(f"4/4: Save {len(users_to_save)} users")
        self.user_bot.save_users(users_to_save, num_likes=1)

        self.SLACK_INFO.send_message(
            f'{len(users_to_save)}/{len(tweets)}tweets searched by keyword have been liked.'
        )


if __name__ == '__main__':
    like_bot = LikeBot()
    try:
        like_bot.like_tweet_from_users_in_db(data_num=500)
    except TweepError as e:
        BotBase.SLACK_ERROR.send_message(
            'An error occurred from tweepy client.'
            f'Reason for this error is「{e.reason}」'
        )
    except Exception as e:
        # TODO: Narrow Exception by creating wrapper
        import sys

        tb = sys.exc_info()[2]
        BotBase.SLACK_ERROR.send_message(e.with_traceback(tb))
        raise e

    for keyword, importance in TARGET_KEYWORD_AND_IMPORTANCE:
        try:
            like_bot.like_from_keyword(keyword, importance)
        except TweepError as e:
            BotBase.SLACK_ERROR.send_message(
                'An error occurred from tweepy client.'
                f'Reason for this error is「{e.reason}」'
            )
        except Exception as e:
            # TODO: Narrow Exception by creating wrapper
            import sys

            tb = sys.exc_info()[2]
            BotBase.SLACK_ERROR.send_message(e.with_traceback(tb))
            raise e
