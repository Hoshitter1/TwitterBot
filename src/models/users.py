from sqlalchemy import Column, BigInteger, Boolean, String

from utils import *


class ValuableUsers(Base):
    """

    """

    __tablename__ = 'valuable_users'
    user_id = Column('id', BigInteger, primary_key=True)
    screen_name = Column('screen_name', String)
    is_friend = Column('is_friend', Boolean, default=False)
    is_liked = Column('is_liked', Boolean, default=False)
