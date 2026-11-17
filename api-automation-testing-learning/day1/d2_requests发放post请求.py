"""
post请求:
   - 参数格式是json数据:json接受参数
     - 自动把数据用json格式封装了,不需要指定这个content-type为json;这个头部可以不带,带了也不会报错
   - 参数是form表单格式,用data接受参数
     - 自动把数据用form表单格式封装了,不需要指定这个content-type为form;这个头部可以不带,带了也不会报错
"""

import requests

# post请求-- 电商项目的登录接口-json数据
meth = "post"

url = "http://shop.lemonban.com:8107/login"

param = {"principal":"lemon_python","credentials":"12345678","appType":3,"loginType":0}

head = {"Accept-Language":"zh"}

resp = requests.request(method=meth,url=url,headers=head,json=param)

# print(resp) # Response对象
# print(resp.status_code) #获取响应状态码
# print(resp.headers)  #获取响应头
# print(resp.text) #获取响应数据
# print(resp.json())

# ERP项目的登录接口--表单格式的参数

meth = "post"

url = "http://erp.lemonban.com/user/login"

param = {"loginame":"test1","password":"e10adc3949ba59abbe56e057f20f883e"}

head = {"Accept-Language":"zh"}

resp = requests.request(method=meth,url=url,headers=head,data=param)

# print(resp) # Response对象
# print(resp.status_code) #获取响应状态码
# print(resp.headers)  #获取响应头
# print(resp.text) #获取响应数据
print(resp.json())