import asyncio
from typing import List

from tweepy.error import TweepError

from bots import (
    BotBase,
    UserBot,
    LikeBot,
)
from utils import (
    TARGET_KEYWORD_AND_IMPORTANCE,
    DUMPED_FILE,
    DB_LIKES,
    LIKE_LIMIT_PER_DAY,
)
from models import users


async def like_users_in_db_and_tweets_by_keyword():
    """like tweets of users in db and tweets that searched by keywords mentioned in setting.

    First process: Like tweets of users from db.
    Second process:
    """
    like_bot = LikeBot()

    while True:
        # First process: Like tweets of users from db.
        try:
            like_bot.like_tweet_from_users_in_db(data_num=DB_LIKES)
        except TweepError as e:
            BotBase.SLACK_ERROR.send_message(
                'An error occurred from tweepy client of like_tweet_from_users_in_db.'
                f'Reason for this error is「{e.reason}」'
            )
        except Exception as e:
            # TODO: Narrow Exception by creating wrapper
            import sys

            tb = sys.exc_info()[2]
            BotBase.SLACK_ERROR.send_message(e.with_traceback(tb))
            raise e

        # Second process: Like tweets that searched by keywords mentioned in setting.
        total_likes_by_keyword = int(LIKE_LIMIT_PER_DAY - like_bot.total_likes)
        for keyword, importance in TARGET_KEYWORD_AND_IMPORTANCE:
            like_num = int(total_likes_by_keyword * importance / len(TARGET_KEYWORD_AND_IMPORTANCE))
            try:
                like_bot.like_from_keyword(keyword, like_num)
            except TweepError as e:
                BotBase.SLACK_ERROR.send_message(
                    'An error occurred from tweepy client of like_from_keyword.'
                    f'Reason for this error is「{e.reason}」'
                )
            except Exception as e:
                # TODO: Narrow Exception by creating wrapper
                import sys

                tb = sys.exc_info()[2]
                BotBase.SLACK_ERROR.send_message(e.with_traceback(tb))
                raise e


async def save_users_following_target_celebrities(target_file: str) -> None:
    """Collect all the followers of target celebrities and save users depending on their value
    The users will be used for liking their tweets so I would get attentions from them.

    Args:
        target_file: text file that contains celebrities's ID
        ID should be described line by line so parse_target_users will work okay.

    """
    # TODO: parser should be in utils
    famous_guys: List[str] = UserBot.parse_target_users(target_file)
    dumped_list: List[str] = UserBot.parse_target_users(DUMPED_FILE)

    users.ValuableUsers.create_table_unless_exists()

    for famous_guy in famous_guys:
        if famous_guy in dumped_list:
            UserBot.SLACK_WARNING.send_message(f'this guy {famous_guy} has already been used. Skip him.')
            continue
        UserBot.SLACK_INFO.send_message(f'[save_user]TwitterBot-chan will collect followers of「{famous_guy}」')
        try:
            UserBot().collect_followers_of_famous_users_and_save_them_in_db([famous_guy])
        except TweepError as e:
            BotBase.SLACK_ERROR.send_message(
                '[save_user]An error occurred from tweepy client.'
                f'Reason for this error is「{e.reason}」'
            )
        except Exception as e:
            # TODO: Narrow Exception by creating wrapper
            import sys

            tb = sys.exc_info()[2]
            BotBase.SLACK_ERROR.send_message(e.with_traceback(tb))
            raise e
        with open(DUMPED_FILE, mode='a') as f:
            f.write(f'{famous_guy}\n')
    UserBot.SLACK_INFO.send_message('****[IMPORTANT]The whole process of registering users ended!*****')


def main():
    loop = asyncio.get_event_loop()
    gather = asyncio.gather(
        like_users_in_db_and_tweets_by_keyword(),
        save_users_following_target_celebrities(target_file='target_lists/tier3.txt'),
    )
    loop.run_until_complete(gather)
    BotBase.SLACK_INFO.send_message('Async process has been started.')


if __name__ == '__main__':
    main()
