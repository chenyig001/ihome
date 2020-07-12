import requests
import json


class SendSmsCode(object):
    def send_sms_code(self, sms_code, phone):
        self.host = 'https://feginesms.market.alicloudapi.com'
        self.path = '/codeNotice'
        # method = 'GET'
        # appcode = '你自己的AppCode'
        # querys = 'param=123456&phone=13547119500&sign=175622&skin=1'
        # bodys = {}
        # url = host + path + '?' + querys
        self.header = {"Authorization": "APPCODE b4c8a39e21e5415caf458b5f3217d4c6"}
        self.querys = 'param='+sms_code+'&'+'phone='+phone+'&'+'sign=1&skin=1'
        self.url = self.host+self.path+'?'+self.querys
        res = requests.get(self.url, headers=self.header)
        return res
