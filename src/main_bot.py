import asyncio

from logics import (
    UserLogic,
    LikeLogic,
)
from clients import SLACK_INFO


def main():
    loop = asyncio.get_event_loop()
    gather = asyncio.gather(
        # UserLogic.main(target_file='target_lists/tier3.txt'),
        LikeLogic.main(),
    )
    loop.run_until_complete(gather)
    SLACK_INFO.send_message('Async process has been started.')


if __name__ == '__main__':
    main()
