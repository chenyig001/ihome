from celery import Celery
from ihome.libs.sms_code import SendSmsCode

# 创建一个Celery类的实例对象
app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/1')  # 配置redis为broker


@app.task
def send_sms(sms_code, mobile):
    '''发送短信的异步任务'''
    sms = SendSmsCode()
    sms.send_sms_code(sms_code, mobile)