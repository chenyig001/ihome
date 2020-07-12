from . import api
from ihome.utils.comment import login_require
from flask import g, current_app, jsonify, request, session
from ihome.utils.response_code import RET
from ihome.utils.image_storage import storage
from ihome.models import User

from ihome import db, constants


@api.route("/user/avatar", methods=["POST"])
@login_require
def set_user_avatar():
    '''
    设置用户头像
    参数：图片（多媒体表单格式） 用户id(g.user_id)
    :return:
    '''
    # 装饰器的代码已经把user_id保存到g对象中，所以视图可以直接获取
    user_id = g.user_id

    # 获取图片
    image = request.files.get("avatar")
    print(image)
    if image is None:
        return jsonify(errno=RET.PARAMERR, errmsg="未上传图片")

    image_data = image.read()

    # 调用七牛闪传图片，返回文件名
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传图片失败")

    # 保存文件名到数据库
    try:
        User.query.filter_by(id=user_id).update({"avatar_url": file_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图片失败")

    avatar_url = constants.QINIU_URL_DOMAIN + file_name
    # 保存成功返回
    return jsonify(errno=RET.OK, errmsg="保存成功", data={"avatar_url": avatar_url})


@api.route("user/user_name", methods=["POST"])
@login_require
def save_user_name():
    '''
    保存用户昵称
    参数：用户id,用户昵称
    :return:
    '''
    # 获取参数
    user_id = g.user_id
    req_dict = request.get_json()
    user_name = req_dict.get("user_name")

    # 判断用户昵称是否为空
    if user_name is None:
        return jsonify(errno=RET.PARAMERR, errmsg="请填写用户昵称")

    # 保存用户昵称到数据库,并判断name是否重复（利用数据库的唯一索引）
    try:
        User.query.filter_by(id=user_id).update({"name": user_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存用户昵称失败")

    # 修改session数据中的name字段
    session["name"] = user_name
    # 返回json数据
    return jsonify(errno=RET.OK, errmsg="保存成功")


@api.route("/user/info", methods=["GET"])
@login_require
def show_user_info():
    '''
    显示用户信息
    参数：用户id
    :return: 用户昵称，用户手机号，用户头像
    '''
    #
    user_id = g.user_id
    try:
        # 根据用户id从数据库查询该用户对象
        user = User.query.filter_by(id=user_id).first()
        name = user.name
        mobile = user.mobile
        avatar = user.avatar_url
        # 拼接文件路径
        file_name = constants.QINIU_URL_DOMAIN + avatar
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

    # 返回信息
    return jsonify(errno=RET.OK, errmsg="获取用户信息成功", data={"name": name, "mobile": mobile, "avatar": file_name})


@api.route("user/auth", methods=["GET"])
@login_require
def set_user_auth():
    '''获取用户实名认证信息'''
    user_id = g.user_id
    # 在数据库查询信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

    if user is None:
        # 数据为空
        return jsonify(errno=RET.NODATA, errmsg="无效的操作")

    # 获取真实名字和身份证id
    real_name = user.real_name
    id_card = user.id_card

    return jsonify(errno=RET.OK, errmsg="ok", data={"real_name": real_name, "id_card": id_card})


@api.route("user/auth", methods=["POST"])
@login_require
def get_user_auth():
    '''设置用户实名认证信息'''
    user_id = g.user_id
    # 获取参数
    resp_dict = request.get_json()
    real_name = resp_dict.get("real_name")
    id_card = resp_dict.get("id_card")
    print(real_name)
    print(id_card)
    # 校验参数完整性
    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 在数据库保存用户实名认证信息
    try:
        # 只有真实姓名和身份证号码为空才保存，否则认为用户已保存过
        User.query.filter_by(id=user_id, real_name=None, id_card=None).update({"real_name": real_name, "id_card":id_card})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存用户实名信息失败")
    # 返回应答
    return jsonify(errno=RET.OK, errmsg="ok")













