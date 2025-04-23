import requests
import time
import mysql.connector
import datetime
import logging
from database_utils.db_manager import DBManager
from database_utils.zbdb import process_and_insert_data
from database_utils.utils import get_time_range
import configparser
import json
import concurrent.futures

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 定义常量，减少硬编码
URL = 'https://xunbiaobao.baidu.com/crm/web/bid/xbb/na/bidding/search/api/enterprise'
REQUEST_DELAY = 1  # 请求间隔时间（秒）
MAX_CONCURRENT_REQUESTS = 2  # 最大并发请求数

# 从配置文件读取信息
def read_config(file_path):
    try:
        config = configparser.ConfigParser(interpolation=None)
        config.read(file_path, encoding='utf-8')
        cookies = dict(config.items('cookies'))
        headers = dict(config.items('headers'))
        json_data = {'query': {}}
        for key, value in config.items('json_data'):
            if key.startswith('query.'):
                sub_key = key.split('.')[1]
                try:
                    json_data['query'][sub_key] = json.loads(value)
                except json.JSONDecodeError:
                    json_data['query'][sub_key] = value
        sup_dic = {}
        for key, value in config.items('sup_dic'):
            index, sub_key = key.split('.')
            if index not in sup_dic:
                sup_dic[index] = {}
            sup_dic[index][sub_key] = value
        return cookies, headers, json_data, sup_dic
    except FileNotFoundError:
        logging.error("配置文件未找到，请检查文件路径。")
        return {}, {}, {}, {}
    except Exception as e:
        logging.error(f"读取配置文件时发生错误: {e}")
        return {}, {}, {}, {}

# 解析日期
def parse_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        logging.warning(f"日期格式错误: {date_str}")
        return None

# 获取数据
def getdata(supName, enterpriseId, cookies, headers, json_data):
    data_all = [['日期', '项目编号', '客户', '类型', '标题', '货品名称', '合计金额', '备注', '供应商']]
    json_data['query']['enterpriseId'] = enterpriseId
    db_manager = DBManager()
    conn = db_manager.connect_db()
    if not conn:
        logging.error("数据库连接失败")
        return

    mycursor = conn.cursor(buffered=True)
    start_date, end_date = get_time_range()
    if start_date is None:
        logging.warning("无法获取有效的开始日期，使用默认值 2025-04-01")
        start_date = datetime.date(2025, 4, 1)

    page_num = 1
    while True:
        json_data['query']['pageNum'] = page_num
        try:
            response = requests.post(
                URL,
                cookies=cookies,
                headers=headers,
                json=json_data
            )
            response.raise_for_status()  # 检查请求是否成功
            Js_data = response.json().get("data")
            if not Js_data:
                break  # 没有数据则退出循环
            data_list = Js_data.get("dataList")
            if not data_list:
                break  # 没有数据列表则退出循环
            for list_item in data_list:
                publish_date_str = list_item.get("publishDate")
                if not publish_date_str:
                    continue
                publish_date = parse_date(publish_date_str)
                if publish_date and publish_date < start_date:
                    break  # 日期小于开始日期则跳出内层循环

                info = [
                    publish_date_str,
                    list_item.get("projectNo"),
                    list_item.get("tenderPrincipal")[0].get("name") if list_item.get("tenderPrincipal") else None,
                    list_item.get("noticeType"),
                    list_item.get('title'),
                    str(list_item.get('productLabels')).strip("[]'").replace("'", ""),
                    list_item.get("winnerAmount") if list_item.get("winnerAmount") else 0,
                    str(list_item.get("displayTags")).strip("[]'").replace("'", ""),
                    list_item.get("winnerPrincipal")[0].get("name") if list_item.get("winnerPrincipal") else None
                ]
                data_all.append(info)
            else:
                page_num += 1
                continue
            break  # 日期小于开始日期则跳出外层循环
        except requests.RequestException as e:
            logging.error(f"请求出错: {e}")
            break
        except json.JSONDecodeError as e:
            logging.error(f"JSON 解析出错: {e}")
            break
        finally:
            time.sleep(REQUEST_DELAY)  # 每次请求后等待一段时间

    try:
        process_and_insert_data(mycursor, data_all)
        logging.info(f"{supName} 数据插入成功")
    except Exception as e:
        logging.error(f"{supName} 处理和插入数据时出错: {e}")
    finally:
        try:
            if 'mycursor' in locals() and mycursor:
                mycursor.close()
            if conn and hasattr(conn, 'is_connected') and conn.is_connected():
                conn.close()
                logging.debug("数据库连接已关闭")
        except Exception as e:
            logging.error(f"关闭连接时发生错误: {e}")
        finally:
            pass


def scrape_data():
    try:
        # 使用封装的函数读取配置
        cookies, headers, json_data, sup_dic = read_config('config/xunbiaow_cookies.txt')
        
        # 并发请求
        future_to_value = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
            for value in sup_dic.values():
                future = executor.submit(getdata, value.get("supname"), value.get("enterpriseid"), cookies, headers, json_data)
                future_to_value[future] = value

        for future in concurrent.futures.as_completed(future_to_value):
            value = future_to_value[future]
            try:
                future.result()
                logging.info(f"{value.get('supname')} 任务完成")
            except Exception as e:
                logging.error(f"{value.get('supname')} 任务出错: {e}")
    except Exception as e:
        logging.error(f"执行 get_xunbiaowang.py 时发生错误: {e}")

if __name__ == "__main__":
    try:
        scrape_data()
    except Exception as e:
        logging.error(f"执行 get_GuoJi.py 时发生错误: {e}")