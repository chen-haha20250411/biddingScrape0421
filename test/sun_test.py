import os
import requests
import sys
sys.path.append('..')  # 添加上级目录到Python路径
from database_utils.db_manager import DBManager

# 代理服务器的IP地址和端口
proxy_ip = "127.0.0.1"
proxy_port = "7890"

# 设置代理
proxies = {
    "http": f"http://{proxy_ip}:{proxy_port}",
    "https": f"http://{proxy_ip}:{proxy_port}",
}

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



# 移除代理设置
# proxy_ip = "127.0.0.1"
# proxy_port = "7890"
# proxies = {
#     "http": f"http://{proxy_ip}:{proxy_port}",
#     "https": f"http://{proxy_ip}:{proxy_port}",
# }

# 修改请求调用，移除proxies参数
response = requests.post('https://ygcg.nbcqjy.org/api/Portal/GetBulletinList', headers=headers, json=json_data)

json_data = response.json()
# 获取 bulletinList 里的所有信息
all_bulletin_info = json_data['body']['data']['bulletinList']
# 初始化数据库管理器
db_manager = DBManager()
conn = db_manager.connect_db()
if conn is None:
    print("数据库连接失败，无法插入数据。")
else:
    for item in all_bulletin_info:
        # 提取所需信息
        bulletinTitle = item['bulletinTitle']
        prjNo = item['prjNo']
        publishDate = item['publishDate']
        bulletinId = item['bulletinId']
        auid=item['autoid']
        # 打印信息
        print(f"标题: {bulletinTitle}, 项目编号: {prjNo}, 发布时间: {publishDate}, bulletinId: {bulletinId}")

        # 构建详细信息的 URL 并发送请求
        detail_url = f"https://ygcg.nbcqjy.org/detail?bulletinId={auid}"
        try:
            # 修改详情请求调用
            detail_response = requests.get(detail_url, headers=headers)
            detail_response.raise_for_status()  # 检查请求是否成功
            # 假设返回的是 JSON 数据，根据实际情况调整
            detail_data = detail_response.json()
            # 将 detail_data 转为字符串存储，可根据实际情况调整
            detail_data_str = str(detail_data)
            print(f"公告 {bulletinId} 的详细信息: {detail_data}")

            # 调用插入数据方法
            db_manager.insert_data(
                project_number=prjNo,
                project_name=bulletinTitle,
                publish_date=publishDate,
                content=detail_data_str,
                project_id=bulletinId,
                total_content=detail_data_str,
                data_source="https://ygcg.nbcqjy.org",
                html_url=detail_url
            )
        except requests.RequestException as e:
            print(f"获取公告 {bulletinId} 详细信息时出错: {e}")
        except Exception as e:
            print(f"处理或插入数据时出错: {e}")

    # 关闭数据库连接
    db_manager.close_connection()

# 打印所有信息
print(type(all_bulletin_info), all_bulletin_info)