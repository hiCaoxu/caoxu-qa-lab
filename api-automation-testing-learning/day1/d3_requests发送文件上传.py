"""
文件上传接口
问题1、是一个需要登录之后才能操作的接口，所以需要先做登录执行-做接口关联
问题2、Internal Server Error
  -如果加了content-type 的头部： {"Content-Type":"multipart/form-data"}会报错：Internal Server Error


"""

import requests

meth = "post"
url = "http://shop.lemonban.com:8107/login"
param = {"principal":"lemon_python","credentials":"12345678","appType":3,"loginType":0}  #字典格式
head = {"Accept-Language": "zh"}
#发送接口请求--调用request库，用变量接受返回值
resp = requests.request(method=meth,url=url,headers=head,json=param)

print(resp.json())

token = resp.json()["token_type"] + " " + resp.json()["access_token"]

# post请求-- 电商项目的上传头像接口，文件参数
pic = "api-automation-testing-learning/day1/lemon.png"
meth = "post"
url = "http://shop.lemonban.com:8107/p/file/upload"
param = {"file":(pic,open(pic,mode="rb"),"image/png")}  #文件
head = {"Accept-Language": "zh","Authorization":token}

#发送接口请求--调用request库，用变量接受返回值
resp = requests.request(method=meth,url=url,headers=head,files=param)
print(resp.text)   #获取响应数据 --文本
print(resp.json())  # 把json格式的响应数据，转换成python字典，方便提取数据

