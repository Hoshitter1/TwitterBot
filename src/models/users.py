from sqlalchemy import Column, BigInteger, Boolean, String, Integer

from utils import *


class ValuableUsers(Base):
    """

    """

    __tablename__ = 'valuable_users'
    user_id = Column('id', BigInteger, primary_key=True)
    screen_name = Column('screen_name', String)
    is_friend = Column('is_friend', Boolean, default=False)
    num_likes = Column('num_liked', Integer, default=0)
