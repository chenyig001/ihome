# 图片验证码的redis有限期,单位秒

IMAGE_CODE_REDIS_EXPIRES = 180

# 短信验证码的redis有限期，单位秒
SMS_CODE_REDIS_EXPIRES = 300

# 发送短信验证码的间隔，单位秒
SEND_SMS_CODE_INTERVAL = 60

# 登陆错误尝试次数
LOGIN_ERROR_MAX_TIMES = 5

# 登陆错误限制时间间隔,单位秒
LOGIN_ERROR_FORBID_TIME = 600

# 七牛的域名
# QINIU_URL_DOMAIN = "http://qb0q8pgy4.bkt.clouddn.com/"
QINIU_URL_DOMAIN = "http://chenyig.cn/"

# 城区信息的缓存时间，单位秒
AREA_INFO_REDIS_CACHE_EXPIRE = 7200

# 首页幻灯片展示的房屋订单数目
HOME_PAGE_MAX_HOUSES = 5

# 主页数据的缓存时间，单位秒
HOME_PAGE_DATA_EXPIRE = 3600

# 房屋详情评论数：
HOUSE_DETAIL_COMMENT_COUNTS = 5

# 房屋列表页面每页数据容量
HOUSE_LIST_PAGE_CAPACITY = 3

# 房屋列表缓存数据过期时间，单位秒
HOUSE_LIST_REDIS_CACHE_EXPIRE = 7200
