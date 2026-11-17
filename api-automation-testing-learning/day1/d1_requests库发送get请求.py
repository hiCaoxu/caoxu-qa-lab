import requests

meth = "get"

url = "http://shop.lemonban.com:8107/search/searchProdPage"

param ={"prodNmame":"真皮圆筒包"}

head = {"Accept-Language":"zh"}

resp = requests.request(method=meth,url=url,headers=head,params=param)

# print(resp) # Response对象
# print(resp.status_code) #获取响应状态码
# print(resp.headers)  #获取响应头
print(resp.text) #获取响应数据