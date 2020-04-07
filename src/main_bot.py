import asyncio

from logics import (
    UserLogic,
    LikeLogic,
)
from clients import SLACK_INFO
from models.users import create_table_unless_exists


def main():
    create_table_unless_exists()
    loop = asyncio.get_event_loop()
    gather = asyncio.gather(
        LikeLogic.main(),
        UserLogic.main(target_dir='./target_lists'),
    )
    loop.run_until_complete(gather)
    SLACK_INFO.send_message('Async process has been started.')


if __name__ == '__main__':
    main()
