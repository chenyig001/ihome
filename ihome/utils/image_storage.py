# -*- coding: utf-8 -*-
# flake8: noqa

from qiniu import Auth, put_file, etag, put_data
import qiniu.config

# 需要填写你的 Access Key 和 Secret Key
access_key = '5wZvGuiwcyX5ImCPcxei4aZqw_4NpVKQUua_fKqq'
secret_key = 'S-_Jv44akVJeswwqCRmXIyoUNQUvvo5bfR6wU8cz'


def storage(file_data):
    # 构建鉴权对象
    q = Auth(access_key, secret_key)

    # 要上传的空间
    bucket_name = 'ihome-storage'

    # 上传后保存的文件名
    # key = 'my-python-logo.png'

    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, None, 3600)

    ret, info = put_data(token, None, file_data)
    if info.status_code == 200:
        # 表示上传成功
        return ret.get("key")
    else:
        # 上传失败
        raise Exception("上传到七牛失败")
    # print(info)
    # print("*"*10)
    # print(ret)
    # assert ret['key'] == key
    # assert ret['hash'] == etag(localfile)


if __name__ == '__main__':
    with open("./1.png", 'rb') as f:
        data = f.read()
        storage(data)