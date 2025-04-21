import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import time
import random
from database_utils.utils import FileUtils, get_time_range
from database_utils.db_manager import DBManager

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 抓取数据
def scrape_data():
    start_date, end_date = get_time_range()
    if start_date is None or end_date is None:
        logging.error("无法获取有效的时间范围，无法继续抓取数据。")
        return
    keywords = FileUtils.read_keywords()
    db_manager = DBManager()
    conn = db_manager.connect_db()
    # 检查 conn 是否为 None
    logging.info(f"数据库连接状态: {conn is not None}")
    if conn is None:
        logging.error("数据库连接失败，无法继续抓取数据。")
        return

    cookies = {
        'PHPSESSID': 'assctqo7k3vhgfnls3v4a172qu',
        'Hm_lvt_fef8b6082a407b84e4b456c40b7e2f76': '1744937291',
        'Hm_lpvt_fef8b6082a407b84e4b456c40b7e2f76': '1744937291',
        'HMACCOUNT': '688496EF741F446F',
    }

    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'http://www.nbbidding.com',
        'Proxy-Connection': 'keep-alive',
        'Referer': 'http://www.nbbidding.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.95 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }

    page = 1
    while True:
        data = {
            'page': str(page),
            'keyword': '',
            'is_open': '1',
        }
        try:
            response = requests.post('http://www.nbbidding.com/Home/Notice/news_list', cookies=cookies, headers=headers, data=data, verify=False)
            response.raise_for_status()  # 检查请求是否成功
            if response.status_code == 200:
                json_data = response.json()
                data = json_data.get('data', {})
                items = data.get('list', [])
                # print(f"第 {page} 页数据: {items}")
        except requests.RequestException as e:
            logging.error(f"请求失败: {e}")
            break
        except ValueError as e:
            logging.error(f"解析 JSON 数据失败: {e}")
            break
        if not items:
            break
        stop_flag = False
        for item in items:
            try:
                # 从 JSON 数据中提取所需信息
                title = item.get('title', '')
                contents = item.get('contents', '')
                item_id = item.get('id', '')
                addtime = item.get('addtime', '')
                project_number = item.get('project_number', '') 
                # 尝试将 addtime 转换为日期对象
                publish_date = datetime.strptime(addtime, '%Y-%m-%d').date() if addtime else None
                if publish_date and (publish_date < start_date or publish_date > end_date):
                    stop_flag = True
                    break   
                # 存储匹配到的关键字
                matched_keywords = []
                for keyword in keywords:
                    if keyword in title or keyword in contents:
                        matched_keywords.append(keyword)
                if matched_keywords:
                    if db_manager.check_item_id_exists(item_id):
                        continue
                    # 获取详细内容
                    detail_url = f'http://www.nbbidding.com/Home/Notice/news_detail?id={item_id}'
                    try:
                        detail_response = requests.get(detail_url, cookies=cookies, headers=headers, verify=False)
                        detail_response.raise_for_status()
                        total_content = detail_response.text
                    except requests.RequestException as e:
                        logging.error(f"获取详细内容失败: {e}")
                        continue
                    title = '[国际招标网 匹配关键字' + ', '.join(matched_keywords) + '] ' + title
                    # 假设 project_id 和 data_source 可以从 item 中获取，这里需要根据实际情况修改
                    project_id = item_id
                    data_source = 'http://www.nbbidding.com'
                    print(f"标题: {title},  ID: {item_id}, 发布时间: {addtime}, 项目编号：{project_number}")
                    db_manager.insert_data(project_number, title, publish_date, total_content, project_id, total_content, data_source, detail_url)
            except ValueError as e:
                logging.warning(f"日期转换失败: {e}")
                continue
        if stop_flag:
            break
        conn.commit()
        page += 1
        # 随机延时 1 到 3 秒，可根据实际情况调整范围
        time.sleep(random.uniform(1, 3))

    db_manager.close_connection()

if __name__ == "__main__":
    scrape_data()
    