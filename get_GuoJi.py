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
    stop_flag = False
    data_to_insert = []  # 新增：存储待插入的数据
    
    while stop_flag == False:
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
                project_number = item.get('projectnum', '') 
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
                    if db_manager.check_item_id_exists(project_number, item_id):
                        logging.info(f"国际招标网记录 ID {item_id} 已存在于数据库中，跳过处理。")
                        continue

                    # 构建详情页URL
                    detail_url = f'http://www.nbbidding.com/Home/Notice/news_detail?id={item_id}'
                    
                    # 获取详细内容
                    detail_response = requests.get(detail_url, cookies=cookies, headers=headers, verify=False)
                    if detail_response:
                        total_content = detail_response.text
                        title = '国际招标网 关键字[' + ', '.join(matched_keywords) + '] ' + title
                        data_source = 'http://www.nbbidding.com'
                        
                        # 添加到待插入列表，而不是立即插入
                        data_to_insert.append((
                            project_number, title, publish_date, total_content,
                            item_id, total_content, data_source, detail_url
                        ))
                        
                        logging.info(f"准备插入: 标题: {title}, ID: {item_id}, 发布时间: {addtime}, 项目编号：{project_number}")
            except ValueError as e:
                logging.warning(f"日期转换失败: {e}")
                continue
                
        page += 1
        time.sleep(random.uniform(1, 3))

    # 批量插入数据
    if data_to_insert:
        try:
            success = db_manager.batch_insert_data(data_to_insert)
            if success:
                logging.info(f"成功批量插入 {len(data_to_insert)} 条数据")
            else:
                logging.error("批量插入数据失败")
        except Exception as e:
            logging.error(f"批量插入数据时发生异常: {e}")
            raise
        finally:
            # 修改为直接关闭连接
            if hasattr(db_manager, 'conn') and db_manager.conn:
                db_manager.conn.close()
                logging.info("数据库连接已关闭")


if __name__ == "__main__":
    try:
        scrape_data()
    except Exception as e:
        logging.error(f"执行 get_GuoJi.py 时发生错误: {e}")
    