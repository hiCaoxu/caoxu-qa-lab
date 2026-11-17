"""
使用requests这个发送接口请求
- 同样要去构造请求四大要素。
 - 请求参数，请求头部分：要求用字典格式表示

函数参数：
- 必备参数： 函数括号里写了一定要传的参数，不传报错的
- 默认参数： 定义参数的时候设置了默认值 可以不传-使用默认值；传-- 替换默认值
- 不定长参数： **kwargs *args

参数 部分： get请求参数，params

"""

import requests

meth = "get"

url = "http://shop.lemonban.com:8107/search/searchProdPage"

param ={"prodNmame":"真皮圆筒包"}

head = {"Accept-Language":"zh"}

resp = requests.request(method=meth,url=url,headers=head,params=param)

# print(resp) # Response对象
# print(resp.status_code) #获取响应状态码
# print(resp.headers)  #获取响应头
# print(resp.text) #获取响应数据
print(resp.json())
