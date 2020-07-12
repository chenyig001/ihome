from . import api
from ihome.utils.comment import login_require
from flask import g, current_app, jsonify, request, json, session
from ihome.utils.response_code import RET
from ihome.utils.image_storage import storage
from ihome.models import Area, House, Facility, HouseImage, User, Order

from ihome import db, redis_store, constants
from datetime import datetime


@api.route("/orders", methods=["POST"])
@login_require
def save_order():
    '''保存订单'''
    user_id = g.user_id
    # 获取参数
    order_data = request.get_json()
    if not order_data:
        return jsonify(errno=RET.PARAMERR, ermsg="参数错误")

    house_id = order_data.get("house_id")  # 预定的房屋编号
    start_date = order_data.get("start_date")
    end_date = order_data.get("end_date")

    # 参数校验
    if not all((house_id, start_date, end_date)):
        return jsonify(errno=RET.PARAMERR, ermsg="参数错误")

    # 日期格式检查
    try:
        # 将请求的时间字符串参数转换为datetime类型
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        assert start_date <= end_date
        # 计算预定的天数
        days = (end_date - start_date).days + 1
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, ermsg="日期格式错误")

    # 查询房屋是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, ermsg="获取房屋信息失败")
    if not house:
        return jsonify(errno=RET.NODATA, ermsg="房屋不存在")

    # 预定的房屋是否是房东的：
    if user_id == house.user_id:
        return jsonify(errno=RET.ROLEERR, ermsg="不能预定自己的房屋")

    # 确保用户预定的时间内，房屋没有被别人下单
    try:
        # 查询时间冲突的订单数
        count = Order.query.filter(Order.house_id == house_id, Order.begin_date <= end_date, Order.end_date >= start_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, ermsg="检查出错，请稍后重试")
    if count > 0:
        return jsonify(errno=RET.DATAERR, ermsg="房屋已被预订")

    # 订单金额：
    amount = days * house.price

    # 保存订单数据
    order = Order(
        house_id=house_id,
        user_id=user_id,
        begin_date=start_date,
        end_date=end_date,
        days=days,
        house_price=house.price,
        amount=amount

    )
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, ermsg="保存订单失败")

    # 返回数据给前端
    return jsonify(errno=RET.OK, errmsg="ok", data={"order_id": order.id})


# /api/v1.0/user/orders?role=custom    role=landlord
@api.route("/user/orders", methods=["GET"])
@login_require
def get_user_orders():
    '''查询用户的订单信息'''
    user_id = g.user_id

    # 用户身份，用户想要查询自己预定的订单，还是房东想查询别人预定自己的房子
    role = request.args.get("role", "")

    # 查询订单数据
    try:
        if role == "landlord":
            # 以房东的身份查询订单
            # 先查询属于自己的房子有哪些
            houses = House.query.filter(House.user_id == user_id).all()
            house_ids = [house.id for house in houses]
            # 再查询预定了自己房子的订单
            orders = Order.query.filter(Order.house_id.in_(house_ids)).order_by(Order.create_time.desc()).all()
        else:
            # 以房客的身份查询订单
            orders = Order.query.filter(Order.user_id == user_id).order_by(Order.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, ermsg="查询订单信息失败")

    # 将订单转换为字典数据
    orders_dict_list = []
    if orders:
        for order in orders:
            orders_dict_list.append(order.to_dict())

    return jsonify(errno=RET.OK, errmsg="ok", data={"orders": orders_dict_list})


@api.route("/orders/<int:order_id>/status", methods=["PUT"])
@login_require
def accept_reject_order(order_id):
    '''接单 拒单'''
    user_id = g.user_id

    # 获取参数
    req_data = request.get_json()
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # action参数表示客户端请求的的是接单还是拒单行为
    action = req_data.get("action")
    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        # 根据订单号查询订单，并且要求订单出待接单状态
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_ACCEPT").first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, ermsg="无法获取订单数据")

    # 确保房东只能修改自己房子的订单
    if not order or house.user_id != user_id:
        return jsonify(errno=RET.REQERR, ermsg="操作无效")

    if action == "accept":
        # 接单，将订单状态设置为等待评论
        order.status = "WAIT_PAYMENT"
    elif action == "reject":
        reason = req_data.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
        order.status = "REJECTED"
        order.comment = reason

    try:
        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, ermsg="修改订单失败")

    return jsonify(errno=RET.OK, errmsg="ok")


@api.route("/orders/<int:order_id>/comment", methods=["PUT"])
@login_require
def save_order_comment(order_id):
    '''修改订单评论信息'''
    user_id = g.user_id

    resp_data = request.get_json()
    comment = resp_data.get("comment")  # 评价信息

    # 检验参数
    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 确保只能评论自己下的订单
    try:
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id, Order.status == "WAIT_COMMENT").first()
        print(order)
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, ermsg="无法获取订单数据")
    if not order:
        return jsonify(errno=RET.REQERR, ermsg="操作无效")

    try:
        # 将订单状态设置为完成
        order.status = "COMPLETE"
        # 保存订单的评价信息
        order.comment = comment
        # 将房屋的订单数加一
        house.order_count += 1
        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, ermsg="操作无效")
    # 一旦评价信息修改，房屋详情的页面信息需要更新，删除redis缓存
    try:
        redis_store.delete("house_info_%s" % order.house_id)
    except Exception as e:
        current_app.logger.error(e)

    return jsonify(errno=RET.OK, errmsg="ok")
