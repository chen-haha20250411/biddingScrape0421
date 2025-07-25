import requests
import time
import mysql.connector
import datetime
import logging
from database_utils.db_manager import DBManager
from database_utils.zbdb import process_and_insert_fengniao_data
from database_utils.utils import get_time_range
import configparser
import json
import concurrent.futures
import re


# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
cookies = {
    'app-uuid': 'WEB-F7D4A1D21B3A442F88C7B6937008EB40',
    'app-device': 'WEB',
    'first-authorization': '1750812224431',
    'userinfo': '%7B%22userId%22%3A1047343%2C%22inviteCode%22%3A%22AAA77CD0FD5060E8%22%2C%22nickName%22%3A%2218858484349%22%2C%22unionid%22%3A%22oTZAV6-phOA5LpyZBKiBhp-UU9CM%22%2C%22isVip%22%3Atrue%2C%22vipStatus%22%3A%22vip%22%2C%22mobile%22%3A%2218858484349%22%2C%22email%22%3Anull%2C%22timestamp%22%3A1753240057202%2C%22userNewType%22%3Atrue%2C%22vipTimeOut%22%3A1817%2C%22notGetLoginVip%22%3Afalse%2C%22vipExpireTime%22%3A1907855999000%2C%22isQueryRiskDoc%22%3Afalse%2C%22queryRiskDocSwitch%22%3A%221%22%2C%22status%22%3A%22vip%22%2C%22vipEndTime%22%3A%222030-06-16%22%7D',
    'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwYXNzd29yZCI6IjE3NzgxYTc5ZjJjMzdhYWFmNGYwNTgyNWI3YmNjYzJjIiwiZXhwIjoxNzUzMjQxODU3LCJ1c2VySWQiOjEwNDczNDMsInV1aWQiOiJhYjlkMjE1Yy01MDYxLTRmYjEtYWJhZC1hMDJhZGQ4OTg4NzIiLCJ1c2VybmFtZSI6IjE4ODU4NDg0MzQ5In0.CJ3DWl-t2vlDM3jcHVyaOCjt4up_kGGhJTrAR3JRuw8',
}

headers = {
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Connection': 'keep-alive',
    'Origin': 'https://www.riskbird.com',
    'Referer': 'https://www.riskbird.com/ent/%E5%AE%81%E6%B3%A2%E5%8D%8E%E5%8A%9B%E4%BF%A1%E6%81%AF%E7%B3%BB%E7%BB%9F%E5%B7%A5%E7%A8%8B%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8.html?entid=LZXobqTY8Q3&fuzzyId=43851205&position=1',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
    'accept': 'application/json',
    'app-device': 'WEB',
    'content-type': 'application/json',
    'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Microsoft Edge";v="138"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'xs-content-type': 'application/json',
    # 'Cookie': 'app-uuid=WEB-F7D4A1D21B3A442F88C7B6937008EB40; app-device=WEB; first-authorization=1750812224431; userinfo=%7B%22userId%22%3A1047343%2C%22inviteCode%22%3A%22AAA77CD0FD5060E8%22%2C%22nickName%22%3A%2218858484349%22%2C%22unionid%22%3A%22oTZAV6-phOA5LpyZBKiBhp-UU9CM%22%2C%22isVip%22%3Atrue%2C%22vipStatus%22%3A%22vip%22%2C%22mobile%22%3A%2218858484349%22%2C%22email%22%3Anull%2C%22timestamp%22%3A1753240057202%2C%22userNewType%22%3Atrue%2C%22vipTimeOut%22%3A1817%2C%22notGetLoginVip%22%3Afalse%2C%22vipExpireTime%22%3A1907855999000%2C%22isQueryRiskDoc%22%3Afalse%2C%22queryRiskDocSwitch%22%3A%221%22%2C%22status%22%3A%22vip%22%2C%22vipEndTime%22%3A%222030-06-16%22%7D; token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwYXNzd29yZCI6IjE3NzgxYTc5ZjJjMzdhYWFmNGYwNTgyNWI3YmNjYzJjIiwiZXhwIjoxNzUzMjQxODU3LCJ1c2VySWQiOjEwNDczNDMsInV1aWQiOiJhYjlkMjE1Yy01MDYxLTRmYjEtYWJhZC1hMDJhZGQ4OTg4NzIiLCJ1c2VybmFtZSI6IjE4ODU4NDg0MzQ5In0.CJ3DWl-t2vlDM3jcHVyaOCjt4up_kGGhJTrAR3JRuw8',
}


json_data = {
    'filterCnd': 0,
    'page': 1,
    'size': 100,
    'orderNo': 'WEB202507231413280608834',
    'extractType': 'managementBidNotice',
    'sortField': '',
    'filterMap': {},
}

# 定义常量，减少硬编码
URL = 'https://www.riskbird.com/riskbird-api/companyInfo/list'
REQUEST_DELAY = 1  # 请求间隔时间（秒）
MAX_CONCURRENT_REQUESTS = 5  # 最大并发请求数
max_page_num = 2 #翻页次数



def safe_float(value):
    if not value:
        return 0.0
    match = re.search(r'[-+]?\d+(?:\.\d+)?', str(value).strip())
    return round(float(match.group()), 1) if match else 0.0

def get_detail(url):
    detail_json_data = {'id': url.split('id=')[1].split('&')[0],'extractType': 'managementBidNotice','orderNo': url.split('orderNo=')[1]}
    response = requests.post(
        'https://www.riskbird.com/riskbird-api/companyInfo/detail',
        cookies=cookies,
        headers=headers,
        json=detail_json_data,
        timeout=10  # 关键！
    )
    if response.status_code == 200:
        Js_data = response.json().get("data")
        if not Js_data:
            logging.info("没有数据")
            return   0 ,'',''
        else :
            #  logging.info(Js_data.get("znum"))
            #  logging.info(Js_data.get("content"))
           num = safe_float(Js_data.get("znum"))
           return num ,Js_data.get("content"),Js_data.get("contentHtml")


    else:
            print(f"获取详情页失败。状态码: {response.status_code}")
            return   0 ,'',''

# 从配置文件读取信息
def read_config(file_path):
    try:
        config = configparser.ConfigParser(interpolation=None)
        config.read(file_path, encoding='utf-8')
        sup_dic = {}
        for key, value in config.items('sup_dic'):
            if '.' in key:
                index, sub_key = key.split('.', 1)
                if index not in sup_dic:
                    sup_dic[index] = {}
                sup_dic[index][sub_key] = value.strip("'\"")  # 去除可能的引号
        # logging.info(f"sup_dic: {sup_dic}")
        return sup_dic
    except FileNotFoundError:
        logging.error("配置文件未找到，请检查文件路径。")
        return {}
    except Exception as e:
        logging.error(f"读取配置文件时发生错误: {e}")
        return {}


# 解析日期
def parse_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        logging.warning(f"日期格式错误: {date_str}")
        return None


# 获取数据
def getdata(supName, enterpriseId, cookies, headers, json_data):
    data_all = []
    json_data['orderNo'] = enterpriseId
    db_manager = DBManager()
    conn = db_manager.connect_db()
    if not conn:
        logging.error(f"{supName} 数据库连接失败")
        return

    try:
        mycursor = conn.cursor(buffered=True)
        start_date, end_date = get_time_range()
        logging.info(f"风鸟网 {supName} 数据采集开始时间: {start_date} 结束时间: {end_date}")
        if start_date is None:
            logging.warning("无法获取有效的开始日期，使用默认值 2025-01-01")
            start_date = datetime.date(2025, 1, 1)
            end_date = datetime.date(2025, 12, 31)

        page_num = 1
        start_time = time.time()
        while page_num <= max_page_num:
            if time.time() - start_time > 120:  # 最多跑 2 分钟
                logging.warning(f"{supName} 运行超时，强制退出")
                break
            # 在 getdata() 的循环中添加
            if page_num % 5 == 0:
                elapsed = time.time() - start_time
                logging.info(f"{supName} 已处理 {page_num} 页, 耗时 {elapsed:.1f} 秒")
            json_data['page'] = page_num
            json_data['orderNo'] = enterpriseId
            # logging.info(f"风鸟网 {supName} 请求{json_data}")
            
            try:
                response = requests.post(
                    URL,
                    cookies=cookies,
                    headers=headers,
                    json=json_data,
                    timeout=10  # 关键！
                )
                response.raise_for_status()
                Js_data = response.json().get("data")
                if not Js_data:
                    logging.info(f"{supName} 没有数据")
                    break
                data_list = Js_data.get("apiData")
                if not data_list:
                    logging.info(f"{supName} 没有数据列表")
                    page_num += 1
                    continue
                for list_item in data_list:
                    publish_date_str = list_item.get("gdate")
                    if not publish_date_str:
                        continue
                    publish_date = parse_date(publish_date_str)
                    if not publish_date or publish_date < start_date or publish_date > end_date:
                        # logging.info(f"nowpage: {page_num} 【风鸟网】 {supName} 日期: {publish_date} 不符合区间")
                        continue  # 跳过本条，继续查下一条
                    if list_item.get("idStr") is None:
                        html_url = None
                    else:   
                        idstr=list_item.get("idStr")
                        html_url = f"https://www.riskbird.com/detail/bidding?id={idstr}&orderNo={enterpriseId}"
                        zb_number, detail_content,detail_html_content =get_detail(html_url)
                    info = [
                        publish_date_str,
                        list_item.get("idStr"),
                        list_item.get("tenderee") if list_item.get("tenderee") else None,
                        list_item.get("type"),
                        list_item.get('title'),
                        list_item.get("content") if list_item.get("content") else None,
                        zb_number,
                        list_item.get("provinceCn"),
                        supName,
                        html_url,
                        detail_html_content
                        
                    ]
                    data_all.append(info)
                page_num += 1
                continue
            except requests.RequestException as e:
                logging.error(f"{supName} 请求出错: {e}")
                break
            except json.JSONDecodeError as e:
                logging.error(f"{supName} JSON 解析出错: {e}")
                break
            finally:
                time.sleep(REQUEST_DELAY)

        # 数据插入，带重试
        for attempt in range(3):
            try:
                process_and_insert_fengniao_data(supName, conn, mycursor, data_all)
                # logging.info(f"{supName} 数据成功插入{len(data_all)-1}条")
                break
            except Exception as e:
                logging.error(f"{supName} 处理和插入数据时出错（第{attempt + 1}次）: {e}")
                if attempt == 2:
                    logging.error(f"{supName} 数据插入最终失败")
                else:
                    time.sleep(2)
    finally:
        try:
            if 'mycursor' in locals() and mycursor:
                mycursor.close()
            if conn and hasattr(conn, 'is_connected') and conn.is_connected():
                conn.close()
                logging.debug(f"{supName} 数据库连接已关闭")
        except Exception as e:
            logging.error(f"{supName} 关闭连接时发生错误: {e}")


def scrape_data():
    try:
        sup_dic = read_config('config/fengniao_cookies.txt')
        # 并发请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
            futures = []
            for value in sup_dic.values():
                # logging.info(f"请求{value.get('enterpriseid')}")
                futures.append(executor.submit(
                    getdata,
                    value.get("supname"),
                    value.get("enterpriseid"),
                    cookies,
                    headers,
                    json_data.copy()  # 每个线程用自己的json_data副本
                ))
            for future in concurrent.futures.as_completed(futures, timeout=None):
                try:
                    future.result(timeout=150)  # 单个任务超时 150 秒
                except concurrent.futures.TimeoutError:
                    logging.error("任务超时终止")
                except Exception as e:
                    logging.error(f"线程任务出错: {e}")

    except Exception as e:
        logging.error(f"执行 get_fengniao.py 时发生错误: {e}")
    finally:
        logging.info("所有采集任务完成")


if __name__ == "__main__":
    scrape_data()