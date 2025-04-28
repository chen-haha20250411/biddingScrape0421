import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from database_utils.db_manager import DBManager
from database_utils.utils import FileUtils, get_time_range
from threading import Lock

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 基础请求头模板
base_headers = {
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

# 基础请求数据模板
base_json_data = {
    'pageIndex': 1,
    'pageSize': 15,
    'classID': '21',
    'ZtbTypeId': None,
    'InfoTypeId': None,
}

# 线程安全的已处理ID集合
processed_ids = set()
processed_ids_lock = Lock()

def get_thread_safe_session():
    """为每个线程创建独立的会话和请求头"""
    session = requests.Session()
    # 创建线程特定的请求头
    headers = base_headers.copy()
    # 可以在这里添加线程特定的请求头修改
    session.headers.update(headers)
    return session

def parse_date(date_str):
    """解析日期字符串"""
    if not date_str:
        return None
    for fmt in ('%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    logging.warning(f"无法解析日期字符串 {date_str}")
    return None

def process_item(bulletinId, autoId, matched_keywords, bulletinTitle, prjNo, publish_date, current_page):
    """处理单个公告项"""
    with processed_ids_lock:
        if bulletinId in processed_ids:
            logging.info(f"公告ID {bulletinId} 已在处理中或已完成，跳过")
            return None
        processed_ids.add(bulletinId)
    
    try:
        # 为每个线程创建独立的会话
        session = get_thread_safe_session()
        detail_url = f"https://ygcg.nbcqjy.org/detail?bulletinId={autoId}"
        logging.info(f"正在抓取阳光网第{current_page}页数据: {detail_url}")
        
        # 使用会话发送请求
        detail_response = session.get(detail_url)
        
        if not detail_response:
            logging.error(f"获取公告 {bulletinId} 详情失败：无响应")
            with processed_ids_lock:
                processed_ids.remove(bulletinId)
            return None
            
        if detail_response.status_code != 200:
            logging.error(f"获取公告 {bulletinId} 详情失败：状态码 {detail_response.status_code}")
            with processed_ids_lock:
                processed_ids.remove(bulletinId)
            return None
            
        total_content = detail_response.text
        if not total_content:
            logging.error(f"获取公告 {bulletinId} 详情失败：内容为空")
            with processed_ids_lock:
                processed_ids.remove(bulletinId)
            return None
            
        title = f'阳光采购网 关键字:[{", ".join(matched_keywords)}] {bulletinTitle}'
        data_source = "https://ygcg.nbcqjy.org"
        
        # 提取主要内容作为 content
        try:
            soup = BeautifulSoup(total_content, 'html.parser')
            content = soup.get_text(strip=True)[:500]  # 取前500个字符作为摘要
        except Exception as e:
            logging.warning(f"解析公告 {bulletinId} 内容失败: {e}")
            content = total_content[:500]  # 如果解析失败，直接取前500个字符
        
        # 确保所有必要的字段都有值
        if not all([prjNo, title, publish_date, content, bulletinId, total_content, data_source, detail_url]):
            logging.error(f"公告 {bulletinId} 数据不完整")
            with processed_ids_lock:
                processed_ids.remove(bulletinId)
            return None
            
        return (
            prjNo,           # project_number
            title,           # project_name
            publish_date,    # publish_date
            content,         # content
            bulletinId,      # project_id
            total_content,   # total_content
            data_source,     # data_source
            detail_url       # html_url
        )
    except requests.exceptions.RequestException as e:
        logging.error(f"请求公告 {bulletinId} 详情时发生网络错误: {e}")
        with processed_ids_lock:
            processed_ids.remove(bulletinId)
        return None
    except KeyError as e:
        logging.warning(f"解析公告 {bulletinId} 项失败，缺少键 {e}")
        with processed_ids_lock:
            processed_ids.remove(bulletinId)
        return None
    except Exception as e:
        logging.error(f"处理公告 {bulletinId} 时发生异常: {e}")
        with processed_ids_lock:
            processed_ids.remove(bulletinId)
        return None

def scrape_data():
    keywords = FileUtils.read_keywords()
    db_manager = DBManager()
    conn = None
    try:
        conn = db_manager.connect_db()
        logging.info(f"数据库连接状态: {conn is not None}")
        if conn is None:
            logging.error("数据库连接失败，无法继续抓取数据。")
            return
        start_date, end_date = get_time_range()
        logging.info(f"获取的时间范围: 开始日期 {start_date}, 结束日期 {end_date}")
        if start_date is None or end_date is None:
            logging.error("无法获取有效的时间范围，无法继续抓取数据。")
            return
        page_index = 1
        stop_flag = False
        data_to_insert = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            while not stop_flag:
                current_page = page_index
                # 为每个请求创建独立的请求数据
                json_data = base_json_data.copy()
                json_data['pageIndex'] = current_page
                
                # 使用独立的会话发送请求
                session = get_thread_safe_session()
                response = session.post('https://ygcg.nbcqjy.org/api/Portal/GetBulletinList', 
                                      json=json_data)
                
                if not response or response.status_code != 200:
                    logging.error(f"请求失败，状态码: {response.status_code if response else '无响应'}")
                    stop_flag = True
                    break
                    
                try:
                    response_json = response.json()
                except ValueError:
                    logging.error("解析公告列表的 JSON 数据失败")
                    stop_flag = True
                    break
                    
                all_bulletin_info = response_json.get('body', {}).get('data', {}).get('bulletinList', [])
                if not all_bulletin_info:
                    stop_flag = True
                    logging.info(f"阳光网第 {current_page} 页无数据，停止抓取")
                    break
                
                futures = []
                for item in all_bulletin_info:
                    addtime = item.get('publishDate')
                    if not addtime:
                        logging.warning(f"公告项缺少发布日期: {item}")
                        continue
                    
                    publish_date = parse_date(addtime)
                    if not publish_date or publish_date < start_date or publish_date > end_date:
                        logging.debug(f"跳过超出时间范围的公告: {item.get('bulletinId')}")
                        stop_flag = True
                        break
                    
                    bulletinId = item.get('bulletinId')
                    prjNo = item.get('prjNo')
                    bulletinTitle = item.get('bulletinTitle')
                    autoId = item.get('autoId')
                    matched_keywords = [keyword for keyword in keywords if keyword in bulletinTitle]

                    if matched_keywords:
                        if db_manager.check_item_id_exists(prjNo, bulletinId):
                            logging.info(f"公告 {prjNo}-{bulletinId} 已存在，跳过")
                            continue
                        with processed_ids_lock:
                            if bulletinId not in processed_ids:
                                futures.append(executor.submit(process_item, bulletinId, autoId, matched_keywords, bulletinTitle, prjNo, publish_date, current_page))
                            else:
                                logging.info(f"公告ID {bulletinId} 已在处理队列中，跳过重复提交")
                
                for future in futures:
                    result = future.result()
                    if result:
                        data_to_insert.append(result)
                        # 每收集到一定数量的数据就进行批量插入
                        if len(data_to_insert) >= 100:
                            try:
                                success = db_manager.batch_insert_data(data_to_insert)
                                if success:
                                    logging.info(f"成功批量插入 {len(data_to_insert)} 条数据")
                                else:
                                    logging.error("批量插入数据失败")
                                data_to_insert = []  # 清空已插入的数据
                            except Exception as e:
                                logging.error(f"批量插入数据时发生异常: {e}")
                                raise
                
                page_index += 1
                time.sleep(random.uniform(1, 3))

        # 等待所有线程完成
        executor.shutdown(wait=True)
        
        # 处理剩余的数据
        if data_to_insert:
            try:
                success = db_manager.batch_insert_data(data_to_insert)
                if success:
                    logging.info(f"成功批量插入剩余的 {len(data_to_insert)} 条数据")
                else:
                    logging.error("批量插入剩余数据失败")
            except Exception as e:
                logging.error(f"批量插入剩余数据时发生异常: {e}")
                raise
    except Exception as e:
        logging.error(f"执行过程中发生错误: {e}")
        raise
    finally:
        # 确保关闭数据库连接
        if conn:
            try:
                conn.close()
                logging.info("数据库连接已关闭")
            except Exception as e:
                logging.error(f"关闭数据库连接时发生错误: {e}")

if __name__ == "__main__":
    try:
        scrape_data()
    except Exception as e:
        logging.error(f"执行 get_sun.py 时发生错误: {e}")
    