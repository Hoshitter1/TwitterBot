import requests

from utils import SLACK_TOKEN


class Slack:

    def __init__(self, channel):
        self.__token = SLACK_TOKEN
        self.__headers = {'Content-Type': 'application/json'}
        self.__channel = channel

    def send_message(self, message):
        params = {
            'token': self.__token,
            'channel': self.__channel,
            'text': message
        }

        res = requests.post(
            'https://slack.com/api/chat.postMessage',
            headers=self.__headers,
            params=params
        )
        if not res.json().get('ok'):
            print('add logging here')
