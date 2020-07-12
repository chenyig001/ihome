import redis


class Config(object):
    '''配置信息'''
    SECRET_KEY = 'kdjsdoasklaa'

    # 设置连接数据库的URI
    SQLALCHEMY_DATABASE_URI = 'mysql://root:''@127.0.0.1:3306/ihome'
    # 设置每次请求结束后会自动提交数据库中的改动
    # app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True


    # redis
    REDIS_HOST = "127.0.0.1"
    REDIS_POST = 6379

    # flask_session配置
    SESSION_TYPE = 'redis'
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_POST)
    SESSION_USE_SIGNER = True  # 对cookie中的session_id进行隐藏处理
    PERMANENT_SESSION_LIFETIME = 3600*24  # session数据的有效期，单位秒


class DevelopmentConfig(Config):
    '''开发模式的配置信息'''
    DEBUG = True


class ProductionConfig(Config):
    '''生产环境配置信息'''
    pass


config_map = {
    "develop": DevelopmentConfig,
    "product": ProductionConfig
}

