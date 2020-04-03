import os
from typing import Dict, Union

from sqlalchemy.engine import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DEBUG = True

# DB settings
# {database_name}://{user}:{password}@{host}/{dbname}
DB = 'postgresql'
USER = 'user_dev'
PASSWORD = 'pass_dev'
HOST = 'db:5432'
DBNAME = 'develop_db'

# TODO: Add logging
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

# TODO: This way of implementation does not look good
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
    pass
    # print(
    #     f'CONSUMER_KEY:{CONSUMER_KEY}'
    #     f'CONSUMER_SECRET:{CONSUMER_SECRET}'
    #     f'ACCESS_TOKEN:{ACCESS_TOKEN}'
    #     f'ACCESS_TOKEN_SECRET:{ACCESS_TOKEN_SECRET}'
    # )

REQUEST_LIMIT_RECOVERY_TIME_IN_SECOND = 60*15

RETRY_NUM = 3
