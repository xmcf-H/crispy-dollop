import requests
import json

# 测试API的URL
url = "http://172.22.110.24:5000/detect/pe_unauth"

# 测试数据
data = {
    "reqA": "GET /api/user/info?user_id=10086",
    "responseA": '{"code": 0, "data": {"id": 10086, "name": "test"}}',
    "responseB": '{"code": 0, "data": {"id": 10086, "name": "test"}}',
    "statusB": "200"
}

# 发送请求
response = requests.post(url, json=data)

# 打印响应结果
print("Status Code:", response.status_code)
print("Response:", json.dumps(response.json(), indent=2, ensure_ascii=False))