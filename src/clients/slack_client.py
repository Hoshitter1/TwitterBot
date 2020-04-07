import requests

from .mixins import SlackCredentialMixin


class SlackBase:
    pass


class SlackClient(SlackBase, SlackCredentialMixin):

    def send_message(self, message):
        params = {
            'token': self._token,
            'channel': self._channel,
            'text': message
        }

        res = requests.post(
            'https://slack.com/api/chat.postMessage',
            headers=self._headers,
            params=params
        )
        if not res.json().get('ok'):
            # TODO
            print('add logging here')


SLACK_INFO = SlackClient('#twitter_bot_info')
SLACK_WARNING = SlackClient('#twitter_bot_warning')
SLACK_ERROR = SlackClient('#twitter_bot_error')
