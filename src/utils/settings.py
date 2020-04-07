import os
from typing import Dict, Union, List, Tuple

from sqlalchemy.engine import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


DEBUG = True


# DB settings
DB = 'postgresql'
USER = 'user_dev'
PASSWORD = 'pass_dev'
HOST = 'db:5432'
DBNAME = 'develop_db'
if not DEBUG:
    DB = os.environ['DB'],
    USER = os.environ['USER'],
    HOST = os.environ['HOST'],
    PASSWORD = os.environ['PASSWORD'],
    DBNAME = os.environ['DBNAME'],

ENGINE = create_engine(
    f'{DB}://{USER}:{PASSWORD}@{HOST}/{DBNAME}',
    encoding="utf-8",
    echo=True
)
session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=ENGINE
    )
)
Base = declarative_base()
Base.query = session.query_property()


# Twitter secrets
CONSUMER_KEY = os.environ['CONSUMER_KEY']
CONSUMER_SECRET = os.environ['CONSUMER_SECRET']
ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
ACCESS_TOKEN_SECRET = os.environ['ACCESS_TOKEN_SECRET']

# Slack secrets
SLACK_TOKEN = os.environ['SLACK_TOKEN']

if DEBUG:
    print(
        f'CONSUMER_KEY:{CONSUMER_KEY}'
        f'CONSUMER_SECRET:{CONSUMER_SECRET}'
        f'ACCESS_TOKEN:{ACCESS_TOKEN}'
        f'ACCESS_TOKEN_SECRET:{ACCESS_TOKEN_SECRET}'
        f'SLACK_TOKEN: {SLACK_TOKEN}'
    )


# Total number of importance has to be less than limit(1000) - 500(like_tweet_from_users_in_db) = 500
# Express importance by 5 levels
TARGET_KEYWORD_AND_IMPORTANCE: List[Tuple[str, int]] = [
    ('#駆け出しエンジニアと繋がりたい', 5),
    ('python', 3),
    ('Ruby', 3),
    ('機械学習', 3),
    ('webアプリ', 4),
    ('インフラエンジニア', 2),
    ('デプロイ', 1),
    ('AWS', 1),
    ('GCP', 1),
    ('vscod', 1),
    ('WEB系エンジニア', 2),
    ('フリーランスエンジニア', 4),
    ('SES', 1),
    ('AI', 1),
    ('外資系コンサル', 3),
    ('GAFA', 3),
    ('#駆け出しwebデザイナーと繋がりたい', 4),
    ('プログラミング', 1),
    ('C++', 1),
    ('MatrixFLow', 1),
]


# Client
REQUEST_LIMIT_RECOVERY_TIME_IN_SECOND = 60 * 15
RETRY_NUM = 3
LIKE_LIMIT_PER_DAY = 1000


# Settings for logics
DUMPED_FILE = 'target_lists/dumped_users.txt'
DB_LIKES = 500
NUM_PER_BATCH = 100
