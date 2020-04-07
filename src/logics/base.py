from dataclasses import dataclass
from typing import List

from sqlalchemy.orm import sessionmaker
from tweepy.models import User as user_account

from utils import ENGINE
from clients import TwitterClient
from models import ValuableUsers
from .evaluate import Evaluate


@dataclass
class LogicBase:
    twitter = TwitterClient()
    evaluate = Evaluate()

    @property
    def get_session(self):
        session = sessionmaker(bind=ENGINE)
        return session()

    def save_new_users(self, target_all: List[user_account], num_likes: int = 0) -> None:
        """Save users in target_all

        Args:
            target_all (user_account): Target  users to save in db
            num_likes (int): number of likes to save

        Notes:
            table: user_id(integer) screen_name(str) is_friend(boolean) num_likes(int)
        """
        session = self.get_session
        for target in target_all:
            screen_name: str = target.name
            id_: int = target.id
            is_friend: bool = target.following
            vu = ValuableUsers(
                user_id=id_,
                screen_name=screen_name,
                is_friend=is_friend,
                num_likes=num_likes
            )
            session.add(vu)
        session.commit()
        session.close()

    def update_db(self, model_object, *, search_key: str, **kwargs) -> None:
        """Update object

        Args:
            model_object (Any): Model object to update
            search_key (str): key to search data to update
            kwargs (Dict[str, Any]): things to update key: column name value: value to update

        """
        session = self.get_session
        search_ = getattr(model_object, search_key)
        model_ = session.query(model_object).filter(search_ == kwargs[search_key]).first()
        for k, v in kwargs.items():
            setattr(model_, k, v)
        session.commit()
        session.close()

    @classmethod
    async def main(cls, *args, **kwargs):
        raise NotImplementedError
