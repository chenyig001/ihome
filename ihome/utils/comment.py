from werkzeug.routing import BaseConverter
from flask import jsonify, session, g
from ihome.utils.response_code import RET
import functools


# 定义正则表达式转换器
class ReConverter(BaseConverter):
    def __init__(self, url_map, regex):
        # 调用父类的初始化方法
        super(ReConverter, self).__init__(url_map)
        # 保存正则表达式
        self.regex = regex


def login_require(view_func):
    @functools.wraps(view_func)  # 不改变被装饰函数的属性
    def wrapper(*args, **kwargs):
        # 判断用户的登录状态
        user_id = session.get("user_id")
        # 如果用户是登录的，执行视图函数
        if user_id is not None:
            g.user_id = user_id
            return view_func(*args, **kwargs)
        else:
            # 如果用户未登录，返回未登录信息
            return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    return wrapper


# @login_require
# def set_user_avatar():
#     pass