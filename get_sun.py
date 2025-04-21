import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import time
import random
from database_utils.db_manager import DBManager
from database_utils.utils import FileUtils

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 抓取数据
def scrape_data():
    # 通过包调用工具类的方法读取关键字
    keywords = FileUtils.read_keywords()
    db_manager = DBManager()
    conn = db_manager.connect_db()
    # 检查 conn 是否为 None
    logging.info(f"数据库连接状态: {conn is not None}")
    if conn is None:
        logging.error("数据库连接失败，无法继续抓取数据。")
        return

    headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json;charset=UTF-8',
    'Origin': 'https://ygcg.nbcqjy.org',
    'Referer': 'https://ygcg.nbcqjy.org/list?type=2&class=%E5%85%AC%E5%91%8A%E5%85%AC%E7%A4%BA&noticeType=21',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.95 Safari/537.36',
    'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
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

    try:
        # 随机延时 1 到 3 秒，模拟人为操作
        time.sleep(random.uniform(1, 3))
        # 发起请求，不设置代理
        response = requests.post('https://ygcg.nbcqjy.org/api/Portal/GetBulletinList', headers=headers, json=json_data)
        response.raise_for_status()
        # 尝试解析为 JSON 数据并打印
        json_data = response.json()
        print(json_data)

        # 后续需要根据实际 JSON 结构修改获取项目信息的逻辑
        items = json_data.get('data', [])  # 示例，需根据实际修改

        for item in items:
            try:
                # 这里需要根据实际 JSON 结构修改获取信息的方式
                project_number = item.get('project_number', '')
                project_name = item.get('project_name', '')
                addtime = item.get('addtime', '')
                title = item.get('title', '')
                detail_url = item.get('detail_url', '')

                # 尝试将 addtime 转换为日期对象
                publish_date = datetime.strptime(addtime, '%Y-%m-%d').date() if addtime else None

                if publish_date and publish_date < datetime(2025, 1, 1).date():
                    continue

                # 存储匹配到的关键字
                matched_keywords = []
                if publish_date and publish_date.year >= 2025:
                    for keyword in keywords:
                        if keyword in title:
                            matched_keywords.append(keyword)

                if matched_keywords:
                    if db_manager.check_project_number_exists(project_number):
                        continue

                    # 获取详细内容前随机延时
                    time.sleep(random.uniform(1, 3))
                    try:
                        detail_response = requests.get(detail_url, headers=headers)
                        detail_response.raise_for_status()
                        total_content = detail_response.text
                    except requests.RequestException as e:
                        logging.error(f"获取详细内容失败: {e}")
                        continue

                    title = '[阳光采购网 匹配关键字' + ', '.join(matched_keywords) + '] ' + title
                    print(f"标题: {title},  项目编号: {project_number}, 发布时间: {addtime}")
                    # db_manager.insert_data(project_number, title, publish_date, total_content, detail_url)

            except ValueError as e:
                logging.warning(f"日期转换失败: {e}")
                continue

    except requests.RequestException as e:
        logging.error(f"请求失败: {e}")
    except ValueError as e:
        logging.error(f"解析 JSON 数据失败: {e}")
    finally:
        db_manager.close_connection()

if __name__ == "__main__":
    scrape_data()