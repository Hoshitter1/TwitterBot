from sqlalchemy import Column, BigInteger, Boolean, String, Integer

from utils import ENGINE, Base


class ValuableUsers(Base):
    """

    """

    __tablename__ = 'valuable_users'
    user_id = Column('id', BigInteger, primary_key=True)
    screen_name = Column('screen_name', String)
    is_friend = Column('is_friend', Boolean, default=False)
    num_likes = Column('num_likes', Integer, default=0)


def create_table_unless_exists() -> None:
    Base.metadata.create_all(bind=ENGINE)
