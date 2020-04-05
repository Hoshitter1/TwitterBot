from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Set, List, Optional, Union
import time

import tweepy
from tweepy import models
from tweepy.error import RateLimitError, TweepError

from base import BotBase
from utils import *
from models import users


@dataclass
class UserBot(BotBase):
    user_info_cache: Optional[models.User] = None

    def fetch_user_info(self, **kwargs) -> Optional[models.User]:
        """

        Args:
            **kwargs:

        Returns:

        Notes:
            API docs
        """
        for _ in range(RETRY_NUM):
            try:
                return self.API.get_user(**kwargs)
            except RateLimitError:
                time.sleep(REQUEST_LIMIT_RECOVERY_TIME_IN_SECOND)
                self.SLACK_WARNING.send_message('WARNING: Rate limit error occurred! Sleep for 15min..zzzz')
                continue
            except Exception:
                raise Exception('Something is wrong in fetch_user_info.')

    def fetch_user_tweet(self, **kwargs) -> models.User:
        """

        Args:
            **kwargs:

        Returns:

        Notes:
            API docs
        """
        for _ in range(RETRY_NUM):
            try:
                return self.API.user_timeline(**kwargs)
            except RateLimitError:
                time.sleep(REQUEST_LIMIT_RECOVERY_TIME_IN_SECOND)
                self.SLACK_WARNING.send_message('WARNING: Rate limit error occurred! Sleep for 15min..zzzz')
                continue
            except Exception:
                raise Exception('Something is wrong in fetch_user_info.')

    def fetch_user_follower_ids(self, user_id: str) -> Set[int]:
        followers_ids_iter = tweepy.Cursor(self.API.followers_ids, id=user_id).pages()
        remaining = self.fetch_request_limit_remaining(
            'followers',
            '/followers/ids',
            'remaining'
        )
        if remaining == 0:
            time.sleep(REQUEST_LIMIT_RECOVERY_TIME_IN_SECOND)
            self.SLACK_WARNING.send_message(
                'WARNING: Rate limit (fetch_user_follower_ids) error occurred! Sleep for 15min..zzzz'
            )

        all_ids: Set[int] = set()
        for _ in range(RETRY_NUM):
            try:
                ids = next(followers_ids_iter)
            except RateLimitError:
                time.sleep(REQUEST_LIMIT_RECOVERY_TIME_IN_SECOND)
                self.SLACK_WARNING.send_message('WARNING: Rate limit error occurred! Sleep for 15min..zzzz')
                continue
            except StopIteration:
                break

            for id_ in ids:
                all_ids.add(id_)

        return all_ids

    def is_active(self, user: models.User) -> bool:
        tweets = self.fetch_user_tweet(id=user.id)

        # Filters from here
        has_tweets = len(tweets) > 0
        if not has_tweets:
            return False

        three_days_ago: datetime = datetime.now() - timedelta(days=30)
        return three_days_ago < tweets[0].created_at

    def save_users(self, target_all: List[models.User], num_likes: int = 0) -> None:
        """

        Args:
            target_all:
            num_likes:

        Returns:

        Notes:
            table: user_id(integer) is_friend(boolean) num_likes(int)
        """
        session = self.get_session
        for target in target_all:
            screen_name = target.name
            id_: int = target.id
            is_friend: bool = target.following
            vu = users.ValuableUsers(
                user_id=id_,
                screen_name=screen_name,
                is_friend=is_friend,
                num_likes=num_likes
            )
            session.add(vu)
        session.commit()
        session.close()

    def filter_by_existence_in_database(self, user_ids: Set[int]) -> List[int]:
        session = self.get_session
        filtered_ids: List[int] = []
        for id_ in user_ids:
            user_in_db = session.query(users.ValuableUsers).filter(users.ValuableUsers.user_id == id_).first()
            if user_in_db is not None:
                continue
            filtered_ids.append(id_)
        session.close()
        return filtered_ids

    def is_valuable_user(self, user_id: Union[int, models.User]) -> bool:
        if isinstance(user_id, int):
            self.user_info_cache = self.fetch_user_info(id=user_id)
        else:
            # TODO: Use elif once type is confirmed and change arg name of user_id
            self.user_info_cache = user_id

        if not self.is_reliable(self.user_info_cache):
            return False

        if not self.has_valuable_description(self.user_info_cache):
            return False

        if not self.is_active(self.user_info_cache):
            return False

        if self.is_business_account(self.user_info_cache):
            return False

        return True

    @staticmethod
    def create_table_unless_exists() -> None:
        Base.metadata.create_all(bind=ENGINE)

    @staticmethod
    def parse_target_users(text_file: str) -> List[str]:
        f = open(text_file)
        return f.read().splitlines()

    @staticmethod
    def has_valuable_description(user: models.User) -> bool:
        if len(user.description) < 10:
            return False
        return True

    @staticmethod
    def is_reliable(user: models.User) -> bool:
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
    def is_business_account(user: models.User):
        if user.verified:
            return True
        return False

    def collect_followers_of_famous_users_and_save_them_in_db(self, famous_guys: List[str]):
        """I know this is a terrible name

        Returns:

        """

        famous_guys = ['717nkz']  # test user
        self.SLACK_INFO.send_message('1/4: Fetch all_ids')
        all_ids: Set[int] = {
            id_
            for famous_guy in famous_guys
            for id_ in self.fetch_user_follower_ids(famous_guy)
        }

        self.SLACK_INFO.send_message(
            f'2/4: filter to avoid saving duplicate id. all_ids:{len(all_ids)}'
        )
        users_filtered_if_existed: List[int] = self.filter_by_existence_in_database(all_ids)

        self.SLACK_INFO.send_message(
            f'3/4: filter based on their values. users_filtered_if_existed:{len(users_filtered_if_existed)}'
        )
        users_filtered_by_value: List[models.User] = [
            self.user_info_cache for id_ in users_filtered_if_existed
            if self.is_valuable_user(id_)
        ]

        self.SLACK_INFO.send_message(
            f'4/4: Save all of them. users_filtered_by_value{len(users_filtered_by_value)}'
        )
        self.save_users(users_filtered_by_value)


if __name__ == '__main__':
    """
    This process should be implemented before executing main twitter bot
    """
    # id_ = '3690091'
    # user = UserBot().fetch_user_info(id=id_)

    target_file = 'target_lists/tier1.txt'
    dumped_file = 'target_lists/dumped_users.txt'
    dumped_list: List[str] = UserBot.parse_target_users(dumped_file)
    famous_guys: List[str] = UserBot.parse_target_users(target_file)

    UserBot.create_table_unless_exists()
    UserBot.SLACK_INFO.send_message(f'TwitterBot-chan will collect followers of「{famous_guys}」')

    for famous_guy in famous_guys:
        if famous_guy in dumped_list:
            UserBot.SLACK_WARNING.send_message(f'this guy {famous_guy} has already been used. Skip him.')
            continue
        try:
            UserBot().collect_followers_of_famous_users_and_save_them_in_db([famous_guy])
        except Exception as e:
            # TODO: Narrow Exception by creating wrapper
            import sys

            tb = sys.exc_info()[2]
            BotBase.SLACK_ERROR.send_message(e.with_traceback(tb))
            raise e
        UserBot.SLACK_INFO.send_message('The whole process ended! お疲れ様でした!')
        with open(dumped_file, mode='a') as f:
            f.write(f'{famous_guy}\n')
