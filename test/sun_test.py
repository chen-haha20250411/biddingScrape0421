import os
import requests

import requests

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json;charset=UTF-8',
    'Origin': 'https://ygcg.nbcqjy.org',
    'Referer': 'https://ygcg.nbcqjy.org/list?type=2&class=%E5%85%AC%E5%91%8A%E5%85%AC%E7%A4%BA&noticeType=21',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0',
    'sec-ch-ua': '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

json_data = {
    'pageIndex': 1,
    'pageSize': 15,
    'classID': '21',
    'ZtbTypeId': None,
    'InfoTypeId': None,
}

response = requests.post('https://ygcg.nbcqjy.org/api/Portal/GetBulletinList', headers=headers, json=json_data)

# Note: json_data will not be serialized by requests
# exactly as it was in the original request.
#data = '{"pageIndex":1,"pageSize":15,"classID":"21","ZtbTypeId":null,"InfoTypeId":null}'
#response = requests.post('https://ygcg.nbcqjy.org/api/Portal/GetBulletinList', headers=headers, data=data)
json_data = response.json()
print(json_data)