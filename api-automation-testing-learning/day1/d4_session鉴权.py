import requests

# 初始化session对象，后面发送接口请求都用这个session对象发送，不用requests库
# 可以自动传递cookies信息 不需手动传入
session = requests.Session()

# 先登录接口--ERP
url = "http://erp.lemonban.com/user/login"
meth = "POST"
param = {"loginame":"test1","password":"e10adc3949ba59abbe56e057f20f883e"}
resp = session.request(method=meth,url=url,data=param)
print(resp.json())  # 把json格式的响应数据，转换成python字典
print("http响应头中的cookies：",dict(resp.cookies)) # 获取cookie

# 做登录之后的添加接口
url = "http://erp.lemonban.com/supplier/add"
meth = "post"
param = {"info":'{"supplier":"1213","contacts":"","telephone":"","email":"","phonenum":"","fax":"","BeginNeedGet":"","BeginNeedPay":"","AllNeedGet":"","AllNeedPay":"","taxNum":"","taxRate":"","bankName":"","accountNumber":"","address":"","description":"","type":"客户","enabled":1}'}
resp = session.request(method=meth,url=url,data=param)
print(resp.text) #html -登录页面提示先登录
# print(resp.json())  #直接转化json数据为字典格式 但是如果不是json格式数据，就会报错 [HTML数据]