from . import api
from ihome.utils.comment import login_require
from ihome.models import Order
from flask import g, current_app, jsonify, request
from ihome.utils.response_code import RET
from ihome import constants, db

from alipay import AliPay
import os


@api.route("orders/<int:order_id>/payment", methods=["POST"])
@login_require
def order_pay(order_id):
    '''订单支付（支付宝）'''
    user_id = g.user_id

    # 判断订单状态
    try:
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id, Order.status == "WAIT_PAYMENT").first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")
    if not order:
        return jsonify(errno=RET.NODATA, errmsg="订单错误")

    # 业务处理：使用python sdk调用支付宝的支付接口
    # 创建支付宝工具对象
    alipay = AliPay(
        appid="2016102200736882",  # 应用id
        app_notify_url=None,  # 默认回调url
        app_private_key_string=open(os.path.join(os.path.dirname(__file__), 'keys/rsa_private_key.pem')).read(),
        alipay_public_key_string=open(os.path.join(os.path.dirname(__file__), 'keys/alipay_public_key.pem')).read(),
        sign_type="RSA2",  # RSA 或 RSA2
        debug=True  # 默认false
    )

    # 调用支付接口
    # 手机网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
    order_string = alipay.api_alipay_trade_wap_pay(
        out_trade_no=order.id,  # 订单id
        total_amount=str(order.amount/100.0),  # 支付总金额
        subject=u'爱家租%s' % order_id,  # 标题
        return_url="http://127.0.0.1:5000/payComplete.html",
        notify_url=None  # 可选, 不填则使用默认notify url
    )

    # 返回应答
    pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
    return jsonify(errno=RET.OK, errmsg="ok", data={"pay_url": pay_url})


@api.route("/order/payment", methods=["PUT"])
@login_require
def save_order_payment_result():
    '''保存订单支付结果'''

    alipay_dict = request.form.to_dict()

    # 对支付宝进行数据分离 提取支付宝的签名参数sign和剩下的数据
    alipay_sign = alipay_dict.pop("sign")

    # 创建支付宝工具对象
    alipay = AliPay(
        appid="2016102200736882",  # 应用id
        app_notify_url=None,  # 默认回调url
        app_private_key_string=open(os.path.join(os.path.dirname(__file__), 'keys/rsa_private_key.pem')).read(),
        alipay_public_key_string=open(os.path.join(os.path.dirname(__file__), 'keys/alipay_public_key.pem')).read(),
        sign_type="RSA2",  # RSA 或 RSA2
        debug=True  # 默认false
    )
    # 借助工具验证参数的合法性
    # 如果参数是支付宝返回的，result返回True，否则返回false
    result = alipay.verify(alipay_dict, alipay_sign)

    if result:
        order_id = alipay_dict.get("out_trade_no")
        trade_no = alipay_dict.get("trade_no")  # 支付宝的交易号
        try:
            Order.query.filter_by(id=order_id).update({"status":"WAIT_COMMENT", "trade_no":trade_no})
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()

    return jsonify(errno=RET.OK, errmsg="ok")



