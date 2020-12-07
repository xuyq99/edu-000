import random

import requests

from edu_back.settings import constants


class Message(object):
    def __init__(self, api_key):
        # APIkey
        self.api_key = api_key
        # 单条短信发送的接口
        self.single_send_url = constants.single_send_url
    def send_message(self, phone, code):
        """
        短信发送的实现
        :param phone: 要发送的手机号
        :param code: 随机验证码
        :return:
        """
        params = {
            "apikey": self.api_key,
            "mobile": phone,
            "text": "【许雅倩test】您的验证码是{code}。如非本人操作，请忽略本短信".format(code=code)
        }
        req = requests.post(self.single_send_url, data=params)
        print(req)



if __name__ == '__main__':
    # apikey :  6d7595a5ce8b3294fca26ebaf973196e
    message = Message(constants.API_KEY)
    message.send_message('18736114603', '123456')
