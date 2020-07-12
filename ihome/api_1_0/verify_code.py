from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store, constants, db
from flask import current_app, jsonify, make_response, request
from ihome.utils.response_code import RET

from ihome.libs.sms_code import SendSmsCode
from ihome.sms_task.send_sms import send_sms
from ihome.models import User
import json, random


@api.route("image_codes/<image_code_id>")
def get_image_code(image_code_id):
    '''
    获取图片验证码
    :param image_code_id:
    :return:验证码图片
    '''
    # 业务逻辑处理
    # 生成验证码图片
    # 名字  真实文本  图片数据
    name, text, image_data = captcha.generate_captcha()
    # redis_store.set("image_code_%s"%image_code_id,text)
    # redis_store.expire("image_code_%s"%image_code_id,constants.IMAGE_CODE_REDIS_EXPIRES)
    try:
        redis_store.setex("image_code_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 记录日志
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存验证码图片失败")

    # 返回图片
    resp = make_response(image_data)
    resp.headers["Content-Type"] = "image/jpg"

    return resp


# GET /api/v1.0/sms_codes/<mobile>?image_code=xxx&image_code_id=xxx
# @api.route("/sms_codes/<re(r'1[34578]\d{9}'):mobile>")
# def get_sms_code(mobile):
#     '''获取短信验证码'''
#     # 获取参数
#     image_code = request.args.get("image_code")
#     print(image_code)
#     image_code_id = request.args.get("image_code_id")
#
#     # 校验参数
#     if not all([image_code_id, image_code]):
#         # 表示参数不完整
#         return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
#     # 业务处理
#     # 从redis取出真实的图片验证码
#     try:
#         real_image_code = redis_store.get("image_code_%s"%image_code_id)
#         # real_image_code是字节类型，转换为字符串
#         real_image_code = str(real_image_code, encoding="utf8")
#         print(real_image_code)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR, errmsg="redis数据库异常")
#
#     # 判断图片验证码是否过期
#     if real_image_code is None:
#         # 表示图片验证码没有或过期
#         return jsonify(errno=RET.NODATA, errmsg="图片验证码失效")
#
#     # 删除redis中的图片验证码
#     try:
#         redis_store.delete("image_code_%s"%image_code_id)
#     except Exception as e:
#         current_app.logger.error(e)
#
#     # 与用户填写的值对比
#     if real_image_code.lower() != image_code.lower():
#         # 用户填写错误
#         return jsonify(errno=RET.DATAERR, errmsg="图片验证码错误")
#
#     # 判断用户60内有没有重新发送短信
#     try:
#         send_flag = redis_store.get("send_sms_code_%s"%mobile)
#     except Exception as e:
#         current_app.logger.error(e)
#     else:
#         if send_flag is not None:
#             # 表示60内之前有过发送的记录
#             return jsonify(errno=RET.REQERR, errmsg="请求过于频繁，请60秒内重试")
#
#
#     #  判断手机号是否存在
#     try:
#         user = User.query.filter_by(mobile=mobile).first()
#     except Exception as e:
#         current_app.logger.error(e)
#     else:
#         if user is not None:
#             # 表示手机号已存在
#             return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")
#
#     # 如果手机号不存在，则生成短信验证码
#     sms_code = "%06d" % random.randint(0, 999999)
#
#     # 保存真实的短信验证码
#     try:
#         redis_store.setex("sms_code_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
#         # 保存发送给这个手机号的记录，防止用户在60秒内重新发短信
#         redis_store.setex("send_sms_code_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR, errmsg="保存短信验证码失败")
#
#     # 发送短信
#     try:
#         sms = SendSmsCode()
#         res = sms.send_sms_code(sms_code, mobile)
#         data = json.loads(res.text)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.THIRDERR, errmsg="发送失败")
#     # 返回值
#     if data.get("Message") == 'OK':
#         # 发送成功
#         return jsonify(errno=RET.OK, errmsg="发送成功")
#     else:
#         return jsonify(errno=RET.THIRDERR, errmsg="发送失败")


@api.route("/sms_codes/<re(r'1[34578]\d{9}'):mobile>")
def get_sms_code(mobile):
    '''获取短信验证码'''
    # 获取参数
    image_code = request.args.get("image_code")
    print(image_code)
    image_code_id = request.args.get("image_code_id")

    # 校验参数
    if not all([image_code_id, image_code]):
        # 表示参数不完整
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    # 业务处理
    # 从redis取出真实的图片验证码
    try:
        real_image_code = redis_store.get("image_code_%s"%image_code_id)
        # real_image_code是字节类型，转换为字符串
        real_image_code = str(real_image_code, encoding="utf8")
        print(real_image_code)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="redis数据库异常")

    # 判断图片验证码是否过期
    if real_image_code is None:
        # 表示图片验证码没有或过期
        return jsonify(errno=RET.NODATA, errmsg="图片验证码失效")

    # 删除redis中的图片验证码
    try:
        redis_store.delete("image_code_%s"%image_code_id)
    except Exception as e:
        current_app.logger.error(e)

    # 与用户填写的值对比
    if real_image_code.lower() != image_code.lower():
        # 用户填写错误
        return jsonify(errno=RET.DATAERR, errmsg="图片验证码错误")

    # 判断用户60内有没有重新发送短信
    try:
        send_flag = redis_store.get("send_sms_code_%s"%mobile)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if send_flag is not None:
            # 表示60内之前有过发送的记录
            return jsonify(errno=RET.REQERR, errmsg="请求过于频繁，请60秒内重试")


    #  判断手机号是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if user is not None:
            # 表示手机号已存在
            return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")

    # 如果手机号不存在，则生成短信验证码
    sms_code = "%06d" % random.randint(0, 999999)

    # 保存真实的短信验证码
    try:
        redis_store.setex("sms_code_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 保存发送给这个手机号的记录，防止用户在60秒内重新发短信
        redis_store.setex("send_sms_code_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存短信验证码失败")

    # 发送短信
    # 使用celery异步发送短信
    send_sms.delay(sms_code, mobile)   # 发出任务

    return jsonify(errno=RET.OK, errmsg="发送成功")
