import asyncio
from dataclasses import dataclass
from typing import List, Tuple
import random

from tweepy.models import User as user_account
from tweepy.error import TweepError

from models import ValuableUsers
from clients import (
    SLACK_INFO,
    SLACK_WARNING,
    SLACK_ERROR,
)
from utils.settings import (
    TARGET_KEYWORD_AND_IMPORTANCE,
    DUMPED_FILE,
    DB_LIKES,
    LIKE_LIMIT_PER_DAY,
)
from .base import LogicBase
from .errors import LogicError


@dataclass
class LikeLogic(LogicBase):
    total_likes: int = 0

    def fetch_users_with_likes_less_than_threshold_from_db(
            self,
            data_num: int = 50,
            threshold_likes: int = 3
    ) -> List[ValuableUsers]:
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

        SLACK_WARNING.send_message(
            'There is not enough number of users to like. Update user database immediately.'
        )
        session.close()
        return target_users

    def increment_num_like_of_user_in_db(self, id_: int) -> None:
        """Increased number of likes of user in db

        Args:
            id_: user id that has already been registered in db

        """
        session = self.get_session
        user_model = session.query(ValuableUsers).filter(ValuableUsers.user_id == id_).first()
        user_model.num_likes += 1
        session.commit()

    def like_tweet_from_users_in_db(self, data_num: int):
        """like tweets of users that are saved in db

        Args:
            data_num: Number of users to extract for liking

        """
        SLACK_INFO.send_message(
            f'1/3: fetch users from db in like_tweet_from_users_in_db. data_num: {data_num}'
        )
        users: List[ValuableUsers] = self.fetch_users_with_likes_less_than_threshold_from_db(
            data_num=data_num
        )
        total_like_tweets: int = 0
        SLACK_INFO.send_message(
            f'2/3: number of fetched users from db in like_tweet_from_users_in_db: {len(users)}'
        )
        for user in users:
            tweets = self.twitter.fetch_user_tweet(id=user.user_id)
            likable_tweet = self.evaluate.find_likable_tweet(tweets)
            if likable_tweet is None:
                continue
            self.twitter.like_tweet(id=likable_tweet.id)
            self.increment_num_like_of_user_in_db(id_=user.user_id)
            self.total_likes += 1
            total_like_tweets += 1
        SLACK_INFO.send_message(f'{total_like_tweets} tweets have been liked.')

    def like_from_keyword(self, search_word: str, num_to_like: int):
        """like tweets searched by a keyword and save their owner's data

        Args:
            search_word: keyword to search tweets
            num_to_like: number of likes to execute

        """
        SLACK_INFO.send_message(f'1/5: Fetch tweets by search_word「{search_word}」num_to_like: {num_to_like}')
        tweets = self.twitter.fetch_tweets_by_keyword(q=search_word, count=100)

        all_user_ids: List[int] = [
            tweet.author.id
            for tweet in tweets
        ]
        # TODO: FIx this later
        duplicate_user_ids = [
            user_id
            for user_id in set(all_user_ids)
            if all_user_ids.count(user_id) > 1
        ]

        SLACK_INFO.send_message(f"2/5: filter {len(tweets)}tweets based on user's value")
        filtered_tweets_by_user_info = [
            tweet
            for tweet in tweets
            if self.evaluate.is_valuable_user(tweet.author, [tweet])
            if tweet.author.id not in duplicate_user_ids
        ]

        SLACK_INFO.send_message(
            f"3/5: filter {len(filtered_tweets_by_user_info)}tweets based on tweet's likability"
        )
        filtered_tweets_by_likability = [
            tweet
            for tweet in filtered_tweets_by_user_info
            if self.evaluate.is_likable(tweet)
        ]

        target_tweets_to_like = filtered_tweets_by_likability[:num_to_like]
        if len(target_tweets_to_like) < num_to_like:
            SLACK_WARNING.send_message(
                f'Could not find {num_to_like} tweets to like.'
                f'I only found {len(target_tweets_to_like)}...Sorry bro.'
            )

        SLACK_INFO.send_message(f"4/5: Like them all {len(target_tweets_to_like)}")
        users_to_save: List[user_account] = []
        for tweet in target_tweets_to_like:
            status = self.twitter.like_tweet(id=tweet.id)
            if status is not None:
                users_to_save.append(tweet.author)

        SLACK_INFO.send_message(f"5/5: Save {len(users_to_save)} users")
        self.save_new_users(users_to_save, num_likes=1)

        self.total_likes += len(users_to_save)
        SLACK_INFO.send_message(
            f'{len(users_to_save)}/{len(tweets)}tweets searched by keyword have been liked.'
        )

    @classmethod
    async def main(cls):
        """

        """
        cls_instance = cls()
        while True:
            try:
                cls_instance.like_tweet_from_users_in_db(data_num=DB_LIKES)
            except TweepError as e:
                SLACK_ERROR.send_message(
                    'An error occurred from tweepy client of like_tweet_from_users_in_db.'
                    f'Reason for this error is「{e.reason}」'
                )
                raise e
            except LogicError as e:
                SLACK_ERROR.send_message(
                    'An error occurred from tweepy client of like_tweet_from_users_in_db.'
                    f'Reason for this error is「{e}」'
                )
                raise e
            except Exception as e:
                # TODO: Narrow Exception by creating wrapper
                import sys
                tb = sys.exc_info()[2]
                SLACK_ERROR.send_message(
                    'An error occurred  like_tweet_from_users_in_db.'
                )
                SLACK_ERROR.send_message(e.with_traceback(tb))
                raise e
            total_likes_by_keyword = int(LIKE_LIMIT_PER_DAY - cls_instance.total_likes)
            random_keywords_and_importance: List[Tuple[str, int]] = random.sample(
                TARGET_KEYWORD_AND_IMPORTANCE,
                len(TARGET_KEYWORD_AND_IMPORTANCE)
            )
            for keyword, importance in random_keywords_and_importance:
                await asyncio.sleep(1)
                like_num = int(total_likes_by_keyword * importance / len(TARGET_KEYWORD_AND_IMPORTANCE))
                try:
                    cls_instance.like_from_keyword(keyword, like_num)
                except TweepError as e:
                    SLACK_ERROR.send_message(
                        'An error occurred from tweepy client of like_from_keyword.'
                        f'Reason for this error is「{e.reason}」'
                    )
                    raise e
                except LogicError as e:
                    SLACK_ERROR.send_message(
                        'A LogicError occurred from like_from_keyword.'
                        f'Reason for this error is「{e}」'
                    )
                    raise e
                except Exception as e:
                    # TODO: Narrow Exception by creating wrapper
                    import sys
                    tb = sys.exc_info()[2]
                    SLACK_ERROR.send_message(
                        'An error occurred from tweepy client of like_from_keyword.'
                    )
                    SLACK_ERROR.send_message(e.with_traceback(tb))
                    raise e
