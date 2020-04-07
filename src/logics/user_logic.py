import asyncio
import os
from dataclasses import dataclass
from typing import Set, List

from tweepy.models import User as user_account
from tweepy.error import TweepError

import models
from clients import (
    SLACK_INFO,
    SLACK_WARNING,
    SLACK_ERROR,
)
from utils.functions import parse_target_users
from utils.settings import DUMPED_FILE, NUM_PER_BATCH
from .base import LogicBase
from .errors import LogicErrorFileNotFound, LogicError


@dataclass
class UserLogic(LogicBase):

    def filter_by_existence_in_database(self, user_ids: Set[int]) -> List[int]:
        """filter lists by checking if they are in db

        Args:
            user_ids:

        Returns:

        """
        session = self.get_session
        filtered_ids: List[int] = []
        for id_ in user_ids:
            user_in_db = session.query(models.ValuableUsers).filter(models.ValuableUsers.user_id == id_).first()
            if user_in_db is not None:
                continue
            filtered_ids.append(id_)
        session.close()
        return filtered_ids

    def collect_followers_of_famous_users_and_save_them_in_db(self, famous_guys: List[str]) -> List[List[int]]:
        """collect_followers_of_famous_users_and_save_them_in_db

        """
        SLACK_INFO.send_message('[save_user]1/4: Fetch all_ids')
        all_ids: Set[int] = {
            id_
            for famous_guy in famous_guys
            for id_ in self.twitter.fetch_user_follower_ids(famous_guy)
        }

        SLACK_INFO.send_message(
            f'[save_user]2/4: filter to avoid saving duplicate id. all_ids:{len(all_ids)}'
        )
        users_filtered_if_existed: List[int] = self.filter_by_existence_in_database(all_ids)

        SLACK_INFO.send_message(
            f'[save_user]3/5: Divide users_filtered_if_existed by {NUM_PER_BATCH}. '
        )
        user_batches: List[List[int]] = [
            users_filtered_if_existed[idx:idx + NUM_PER_BATCH]
            for idx in range(0, len(users_filtered_if_existed), NUM_PER_BATCH)
        ]

        SLACK_INFO.send_message(
            f'[save_user]total batch number is {len(user_batches)}'
        )
        return user_batches

    def save_batches(self, user_batch):
        SLACK_INFO.send_message(
            f'[save_user]4/5: filter based on their values. '
        )
        users_filtered_by_value: List[user_account] = [
            self.evaluate.user_info_cache for id_ in user_batch
            if self.evaluate.is_valuable_user(id_)
        ]

        SLACK_INFO.send_message(
            f'[save_user]Save all of them. users_filtered_by_value{len(users_filtered_by_value)}'
        )
        self.save_new_users(users_filtered_by_value)

    @classmethod
    async def main(cls, *args, **kwargs) -> None:
        """

        """
        target_dir = kwargs.get('target_dir', None)
        if target_dir is None:
            raise LogicErrorFileNotFound('target_file has to be specified in main of UserLogic')
        files: List[str] = os.listdir(target_dir)
        print(f'files{files}')
        famous_guys = [
            user
            for file in files
            for user in parse_target_users(os.path.join(target_dir, file))
        ]
        print(f'famous_guys{famous_guys}')
        dumped_list: List[str] = parse_target_users(DUMPED_FILE)

        cls_instance = cls()

        for famous_guy in famous_guys:
            if famous_guy in dumped_list:
                SLACK_WARNING.send_message(f'this guy {famous_guy} has already been used. Skip him.')
                continue
            SLACK_INFO.send_message(f'TwitterBot-chan will collect followers of「{famous_guy}」')
            try:
                user_batches = cls_instance.collect_followers_of_famous_users_and_save_them_in_db([famous_guy])
            except TweepError as e:
                SLACK_ERROR.send_message(
                    'An error occurred from tweepy client in UserLogic.'
                    f'error code is「{e.api_code}」'
                    f'error message is「{e.reason}」'
                    f'error response is「{e.response}」'
                )
                raise e
            except LogicError as e:
                SLACK_ERROR.send_message(
                    'An error occurred in UserLogic.'
                    f'Reason for this error is「{e}」'
                )
                raise e
            except Exception as e:
                # TODO: Update this
                import sys
                tb = sys.exc_info()[2]
                SLACK_ERROR.send_message(e.with_traceback(tb))
                raise e
            for user_batch in user_batches:
                cls_instance.save_batches(user_batch)
                await asyncio.sleep(1)
            with open(DUMPED_FILE, mode='a') as f:
                f.write(f'{famous_guy}\n')
        SLACK_INFO.send_message('****[IMPORTANT]The whole process of registering users ended!*****')
