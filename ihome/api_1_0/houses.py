from . import api
from ihome.utils.comment import login_require
from flask import g, current_app, jsonify, request, json, session
from ihome.utils.response_code import RET
from ihome.utils.image_storage import storage
from ihome.models import Area, House, Facility, HouseImage, User, Order

from ihome import db, redis_store, constants
from datetime import datetime


@api.route("/areas", methods=["GET"])
def get_area_info():
    '''获取城区信息'''
    # 从redis读取数据
    try:
        resp_json = redis_store.get("area_info")
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json is not None:
            # 表示redis有数据，直接返回
            return resp_json, 200, {"content-Type": "application/json"}

    # redis没有数据，查询数据库，读取城区信息
    try:
        area_list = Area.query.all()  # 查询出来是所有城区对象的列表
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    area_dict_li = []
    # 将对象转换为字典
    for area in area_list:
        d = {
            "aid": area.id,
            "aname": area.name
        }
        area_dict_li.append(d)

    # 将数据转换为json字符串
    resp_dict = dict(errno=RET.OK, errmsg="ok", data=area_dict_li)
    resp_json = json.dumps(resp_dict)

    # 将数据保存到redis中
    try:
        redis_store.setex("area_info", constants.AREA_INFO_REDIS_CACHE_EXPIRE, resp_json)
    except Exception as e:
        current_app.logger.error(e)

    return resp_json, 200, {"content-Type": "application/json"}


@api.route("house/info", methods=["POST"])
@login_require
def save_house_info():
    '''保存房屋信息
    前端发过来的json数据
    {
        "title":"",
        "price":"",
        "area_id":"",
        "address":"",
        "room_count":"",
        "acreage":"",
        "unit":"",
        "capacity":"",
        "beds":"",
        "deposit":"",
        "min_days":"",
        "max_days":"",
        "facility":["7","8"]
    }
    '''
    user_id = g.user_id
    # 接收参数
    house_dict = request.get_json()
    title = house_dict.get("title")             # 房屋标题
    price = house_dict.get("price")             # 房屋单价
    area_id = house_dict.get("area_id")         # 房屋所属城区的编号
    address = house_dict.get("address")         # 房屋地址
    room_count = house_dict.get("room_count")   # 房屋包含的房间数目
    acreage = house_dict.get("acreage")         # 房屋面积
    unit = house_dict.get("unit")               # 房屋布局（几室几厅）
    capacity = house_dict.get("capacity")       # 房屋容纳人数
    beds = house_dict.get("beds")               # 房屋卧床数目
    deposit = house_dict.get("deposit")         # 押金
    min_days = house_dict.get("min_days")       # 最小入住天数
    max_days = house_dict.get("max_days")       # 最大入住天数
    # 校验参数
    if not all([title,price,area_id,address,room_count,acreage,unit,capacity,beds,deposit,min_days,max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    # 业务处理
    # 前端传过来的单价和押金是以元为单位，转换为分
    # 判断金额是否正确
    try:
        price = int(float(price)*100)
        deposit = int(float(deposit)*100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 判断城区id是否存在
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")
    if area is None:
        return jsonify(errno=RET.NODATA, errmsg="城区信息有误")

    # 保存房屋信息
    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )


    # 处理房屋的设施信息
    facility_ids = house_dict.get("facility")
    # 如果用户勾选了设施信息，再保存到数据库
    if facility_ids:
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
            print(facilities)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库异常")

        if facilities:
            # 保存设施数据，合法的设施数据
            house.facilities = facilities
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    # 保存数据成功,返回应答
    return jsonify(errno=RET.OK, errmsg="ok", data={"house_id": house.id})


@api.route("house/image", methods=["POST"])
@login_require
def save_house_image():
    '''保存房屋图片
    参数：房屋id,图片
    '''
    # 获取参数
    house_id = request.form.get("house_id")
    image = request.files.get("house_image")

    # 校验参数
    if not all([house_id, image]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 判断房屋id是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")
    if house is None:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 上传图片到七牛云
    image_data = image.read()
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="保存图片失败")

    # 保存图片到数据库中
    house_image = HouseImage(house_id=house_id, url=file_name)
    db.session.add(house_image)

    # 处理房屋的主图片
    if not house.index_image_url:
        house.index_image_url = file_name
        db.session.add(house)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存图片数据异常")

    # 拼接图片路径，返回应答
    image_url = constants.QINIU_URL_DOMAIN + file_name
    return jsonify(errno=RET.OK, errmsg="ok", data={"image_url": image_url})


@api.route("/house/info", methods=["GET"])
@login_require
def get_house_basic_info():
    '''获取房东发布的房源基本信息'''
    user_id = g.user_id
    print(user_id)
    # 从数据库查询
    try:
        user = User.query.get(user_id)
        houses = user.houses
        print(houses)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取数据失败")

    # 将查询到的房屋信息转换为字典存放到列表中
    houses_list = []
    if houses:
        for house in houses:
            houses_list.append(house.to_basic_dict())
    # 返回给前端
    return jsonify(errno=RET.OK, errmsg="OK", data={"houses": houses_list})


@api.route("/house/index", methods=["GET"])
def get_house_index():
    '''获取主页幻灯片展示的房屋信息'''
    # 尝试从redis获取数据
    try:
        json_house = redis_store.get("home_page_data")
    except Exception as e:
        current_app.logger.error(e)
        json_house = None

    if json_house:
        # 表示缓存有数据
        # 从redis取出的数据是字节类型，转换为字符串
        json_house = str(json_house, encoding="utf8")
        # print(json_house)
        return '{"errno":0, "errmsg":"OK", "data":%s}' % json_house, 200, {"Content-Type": "application/json"}
    else:
        # 表示缓存无数据，则查询数据库
        try:
            # 查询数据库，返回房屋订单数目最多的五条数据
            houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

        if not houses:
            return jsonify(errno=RET.NODATA, errmsg="查询无数据")

        house_list = []
        for house in houses:
            # 如果房屋未设置主图片，则跳过
            if not house.index_image_url:
                continue
            house_list.append(house.to_basic_dict())

        # 将数据转换为json格式，保存到redis缓存
        json_house = json.dumps(house_list)
        try:
            redis_store.setex("home_page_data", constants.HOME_PAGE_DATA_EXPIRE, json_house)
        except Exception as e:
            current_app.logger.error(e)

        return '{"errno":0, "errmsg":"OK", "data":%s}' % json_house, 200, {"Content-Type": "application/json"}


@api.route("/house/<int:house_id>", methods=["GET"])
def get_house_detail(house_id):
    '''房屋详情页'''
    # 尝试获取用户登录信息，若登录，则返回给前端登录的用户user_id,否则返回user_id=-1
    use_id = session.get("user_id", "-1")

    # 尝试从redis获取数据
    try:
        json_house = redis_store.get("house_info_%s" % house_id)
    except Exception as e:
        current_app.logger.error(e)
        json_house = None

    if json_house:
        # 表示redis有缓存，直接返回给前端
        json_house = str(json_house, encoding="utf8")
        print(json_house)
        return '{"errno":0,"errmsg":"ok", "data":{"user_id":%s, "house":%s}}' % (use_id, json_house), 200, \
               {"Content-Type": "application/json"}
    # 否则查询数据库
    else:
        # 根据house_id获取房屋对象
        try:
            house = House.query.get(house_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询失败")

        if not house:
            return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

        # 将房屋对象数据转换为字典
        try:
            house_data = house.to_full_dict()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DATAERR, errmsg="数据出错")

        # 保存到redis中
        json_house = json.dumps(house_data)
        print(json_house)
        try:
            redis_store.setex("house_info_%s" % house_id, constants.HOME_PAGE_DATA_EXPIRE, json_house)
        except Exception as e:
            current_app.logger.error(e)

        return '{"errno":0,"errmsg":"ok", "data":{"user_id":%s, "house":%s}}' % (use_id, json_house), 200,\
               {"Content-Type": "application/json"}


# GET /api/v1.0/houses?sd=xxx&ed=xxx&aid=xxx&sk=new&page=1
@api.route("/houses")
def get_house_list():
    '''获取房屋的列表信息（搜索页面）'''
    # 获取参数
    start_date = request.args.get("sd", "")  # 用户想要的起始时间
    end_date = request.args.get("ed", "")   # 用户想要的结束时间
    area_id = request.args.get("aid", "")   # 区域编号
    sort_key = request.args.get("sk", "new")  # 排序关键字 如果不传数据默认new
    page = request.args.get("page", "1")  # 页数

    # 校验参数
    # 把时间字符串转时间格式
    try:
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            print(start_date)
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            print(end_date)
        if start_date and end_date:
            assert start_date <= end_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="日期参数有误")

    # 判断区域id
    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="区域参数有误")

    # 处理页数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 尝试从redis获取缓存数据
    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
    try:
        resp_json = redis_store.hget(redis_key, page)
        resp_json = str(resp_json, encoding="utf8")
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json:
            return resp_json, 200, {"Content-Type": "application/json"}

    # 业务处理
    # 过滤条件的参数列表容器
    filter_params = []
    # 从订单查出所有冲突的房屋对象
    # 时间条件
    conflict_orders = None
    try:
        if start_date and end_date:
            #                                                     多个条件使用','不用and
            conflict_orders = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date).all()

        elif start_date:
            conflict_orders = Order.query.filter(Order.end_date >= start_date).all()
        elif end_date:
            conflict_orders = Order.query.filter(Order.begin_date <= end_date).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    print("冲突房间：%s" % conflict_orders)
    if conflict_orders:
        # 从订单获取冲突房屋的id
        conflict_house_ids = [order.house_id for order in conflict_orders]
        # 如果冲突的房屋id不为空，向查询参数中添加条件
        if conflict_house_ids:
            filter_params.append(House.id.notin_(conflict_house_ids))

    # 区域条件
    if area_id:
        filter_params.append(House.area_id == area_id)

    # 查询数据库
    # 补充排序条件
    print("过滤条件的参数:%s" % filter_params)
    if sort_key == "booking":  # 入住最多
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sort_key == "price-inc":  # 价格最低
        house_query = House.query.filter(*filter_params).order_by(House.price.asc())
    elif sort_key == "price-des":  # 价格最高
        house_query = House.query.filter(*filter_params).order_by(House.price.desc())
    else:  # 新旧
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())

    # 处理分页
    try:
        #                               当前页数       每页数据量                                 自动的错误输出
        page_obj = house_query.paginate(page=page, per_page=constants.HOUSE_LIST_PAGE_CAPACITY, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    # 获取当前页面数据
    house_list = page_obj.items
    houses = []
    for house in house_list:
        houses.append(house.to_basic_dict())
    # 获取总页数
    total_page = page_obj.pages

    # 返回应答
    resp_dict = dict(errno=RET.OK, errmsg="ok", data={"total_page": total_page, "houses": houses, "current_page": page})
    resp_json = json.dumps(resp_dict)

    # 设置缓存数据
    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
    # 哈希类型
    if page <= total_page:
        try:
            # redis_store.hset(redis_key, page, resp_json)
            # redis_store.expire(redis_key, constants.HOUSE_LIST_REDIS_CACHE_EXPIRE)

            # 创建redis管道对象
            pipeline = redis_store.pipeline()
            # 开启多个语句的记录
            pipeline.multi()
            pipeline.hset(redis_key, page, resp_json)
            pipeline.expire(redis_key, constants.HOUSE_LIST_REDIS_CACHE_EXPIRE)

            # 执行语句
            pipeline.execute()
        except Exception as e:
            current_app.logger.error(e)
    return resp_json, 200, {"Content-Type": "application/json"}


















