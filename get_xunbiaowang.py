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
cookies = {
    'BIDUPSID': '492CB91B3DBB7AA3C6CABE2D96EF2175',
    'PSTM': '1740119325',
    'BAIDUID': '24BC67949EE49EAEF346876A6B08BC08:FG=1',
    'H_PS_PSSID': '61027_61680_62080_62169_62279_62136_62325_62343_62346_62328_62366_62370_62421_62422_62426',
    'BAIDUID_BFESS': '24BC67949EE49EAEF346876A6B08BC08:FG=1',
    'ZFY': 'kh3XlEglVT4lGdR0KB1aRrTkk9SohTyhw3Vk:AZu8WQI:C',
    '__bid_n': '1965602168b7184e639cee',
    'sensorsdata2015jssdkcross': '%7B%22distinct_id%22%3A%22196560217636fd-025770b96a673e2-4c657b58-1440000-19656021764a16%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E8%87%AA%E7%84%B6%E6%90%9C%E7%B4%A2%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Fcn.bing.com%2F%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTk2NTYwMjE3NjM2ZmQtMDI1NzcwYjk2YTY3M2UyLTRjNjU3YjU4LTE0NDAwMDAtMTk2NTYwMjE3NjRhMTYifQ%3D%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%22196560217636fd-025770b96a673e2-4c657b58-1440000-19656021764a16%22%7D',
    'BCLID': '9156577324754163912',
    'BCLID_BFESS': '9156577324754163912',
    'BDSFRCVID': 'ueCOJeC62iQjY8osWTHnt8u5kqVCqNnTH6_n5lyb1qI6_3O43aroEG0PmM8g0KFhNWRFogKKKgOTHIDF_2uxOjjg8UtVJeC6EG0Ptf8g0x5',
    'BDSFRCVID_BFESS': 'ueCOJeC62iQjY8osWTHnt8u5kqVCqNnTH6_n5lyb1qI6_3O43aroEG0PmM8g0KFhNWRFogKKKgOTHIDF_2uxOjjg8UtVJeC6EG0Ptf8g0x5',
    'H_BDCLCKID_SF': 'JJ48oD_XJI03fP36q4JjqJIVqxby2C62aJ3t0lOvWJ5TMCoY0t6Ze-4y3nO72J0ObRTWQxQn-lr_ShPCBPIhhbFVDqQAtq4eBbPe34oO3l02Vb6Ee-t2yUKJXRJN0tRMW23i0h7mWpTUsxA45J7cM4IseboJLfT-0bc4KKJxbnLWeIJ9jj6jK4JKjHDqJTjP',
    'H_BDCLCKID_SF_BFESS': 'JJ48oD_XJI03fP36q4JjqJIVqxby2C62aJ3t0lOvWJ5TMCoY0t6Ze-4y3nO72J0ObRTWQxQn-lr_ShPCBPIhhbFVDqQAtq4eBbPe34oO3l02Vb6Ee-t2yUKJXRJN0tRMW23i0h7mWpTUsxA45J7cM4IseboJLfT-0bc4KKJxbnLWeIJ9jj6jK4JKjHDqJTjP',
    'Hm_lvt_8cfca2ee1c078aaed86e031c3eb09486': '1745199700,1745571751',
    'HMACCOUNT': '7D437D9CCB86FB23',
    'RT': '"z=1&dm=baidu.com&si=e5c9a3e0-266e-4597-b4fd-f8883eecfd62&ss=m9wkcmp3&sl=4&tt=4oc&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf"',
    'Hm_lpvt_8cfca2ee1c078aaed86e031c3eb09486': '1745571776',
    'ab_sr': '1.0.1_Mzc1MDcyNjYyZDI1MzE5Y2FmNzY0MTZjMTZiYTQyNjA5OTA0ZDhkZjIwNWI5MDc2YWRkNjM0ZDk0M2M1OTM3OTVhOTllN2EyYjdmYTAxMjA4NDczOGU4NGQ0ZmUxYjc0MzRkMGQ3NmQyYWYyNDhiNjJmOTg1Y2U0ZmJhNDI0MTcxYmI5MzBhM2NmMWU3MzczNTdjYTdmYmUwZWZhYTM5Mg==',
}

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Acs-Token': '1745553923658_1745571778363_HquGDI7JzsCB4ZWNQjSVXPdVKwH0sWeSascqKloDfWuWWWxRb9erjb0NSSWbgr340mnzvHSOHuHDxrpbVDqYtZmYj6mOwZUBKyk8WReFqDG0joUwN3BEnKrZ02S7CMThTtE2Mkfat2cVktB/txFsJxVymHSBq0H9/vqeYY2Ebq82qRALlfif0zVXaCQ5JUP2d+emU5DSb/mqrUl8UKpLAXBqmxEWICXr23nbLSx/OxHu0K0q5eVMN+suddfqL+X+csDx2vMrFc0T8XIbwXmB9c0ECC3WrpsZQNEVa+A3ayUU+nplwLFvy/wPjVXl7fJMP/1oDYwy41UaRE/QCck8tYue+F33Y1vai9zrbdmliaFprQFS7Cg5nJjtxUxMy2gliCIQ4EhYAeUa60Dye9EHnw==',
    'Api-Version': '0',
    'Auth-Type': 'PAAS',
    'Client-Version': '0',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json;charset=UTF-8',
    'Env': 'WEB',
    'Origin': 'https://xunbiaobao.baidu.com',
    'Referer': 'https://xunbiaobao.baidu.com/company?id=MTAyNDY2MjY0MTYxMjI0&source=self',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0',
    'User-Info': 'uc_id=;uc_appid=585;acc_token=;acc_id=;login_id=;device_type=;paas_appid=16;version=12;login_type=',
    'X-Requested-With': 'XMLHttpRequest',
    'X-Sourceid': '802f3e321e6b046a0066fa0e081a7ebb',
    'X-Timestamp': '1745571720',
    'sec-ch-ua': '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    # 'Cookie': 'BIDUPSID=492CB91B3DBB7AA3C6CABE2D96EF2175; PSTM=1740119325; BAIDUID=24BC67949EE49EAEF346876A6B08BC08:FG=1; H_PS_PSSID=61027_61680_62080_62169_62279_62136_62325_62343_62346_62328_62366_62370_62421_62422_62426; BAIDUID_BFESS=24BC67949EE49EAEF346876A6B08BC08:FG=1; ZFY=kh3XlEglVT4lGdR0KB1aRrTkk9SohTyhw3Vk:AZu8WQI:C; __bid_n=1965602168b7184e639cee; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22196560217636fd-025770b96a673e2-4c657b58-1440000-19656021764a16%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E8%87%AA%E7%84%B6%E6%90%9C%E7%B4%A2%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Fcn.bing.com%2F%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTk2NTYwMjE3NjM2ZmQtMDI1NzcwYjk2YTY3M2UyLTRjNjU3YjU4LTE0NDAwMDAtMTk2NTYwMjE3NjRhMTYifQ%3D%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%22196560217636fd-025770b96a673e2-4c657b58-1440000-19656021764a16%22%7D; BCLID=9156577324754163912; BCLID_BFESS=9156577324754163912; BDSFRCVID=ueCOJeC62iQjY8osWTHnt8u5kqVCqNnTH6_n5lyb1qI6_3O43aroEG0PmM8g0KFhNWRFogKKKgOTHIDF_2uxOjjg8UtVJeC6EG0Ptf8g0x5; BDSFRCVID_BFESS=ueCOJeC62iQjY8osWTHnt8u5kqVCqNnTH6_n5lyb1qI6_3O43aroEG0PmM8g0KFhNWRFogKKKgOTHIDF_2uxOjjg8UtVJeC6EG0Ptf8g0x5; H_BDCLCKID_SF=JJ48oD_XJI03fP36q4JjqJIVqxby2C62aJ3t0lOvWJ5TMCoY0t6Ze-4y3nO72J0ObRTWQxQn-lr_ShPCBPIhhbFVDqQAtq4eBbPe34oO3l02Vb6Ee-t2yUKJXRJN0tRMW23i0h7mWpTUsxA45J7cM4IseboJLfT-0bc4KKJxbnLWeIJ9jj6jK4JKjHDqJTjP; H_BDCLCKID_SF_BFESS=JJ48oD_XJI03fP36q4JjqJIVqxby2C62aJ3t0lOvWJ5TMCoY0t6Ze-4y3nO72J0ObRTWQxQn-lr_ShPCBPIhhbFVDqQAtq4eBbPe34oO3l02Vb6Ee-t2yUKJXRJN0tRMW23i0h7mWpTUsxA45J7cM4IseboJLfT-0bc4KKJxbnLWeIJ9jj6jK4JKjHDqJTjP; Hm_lvt_8cfca2ee1c078aaed86e031c3eb09486=1745199700,1745571751; HMACCOUNT=7D437D9CCB86FB23; RT="z=1&dm=baidu.com&si=e5c9a3e0-266e-4597-b4fd-f8883eecfd62&ss=m9wkcmp3&sl=4&tt=4oc&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf"; Hm_lpvt_8cfca2ee1c078aaed86e031c3eb09486=1745571776; ab_sr=1.0.1_Mzc1MDcyNjYyZDI1MzE5Y2FmNzY0MTZjMTZiYTQyNjA5OTA0ZDhkZjIwNWI5MDc2YWRkNjM0ZDk0M2M1OTM3OTVhOTllN2EyYjdmYTAxMjA4NDczOGU4NGQ0ZmUxYjc0MzRkMGQ3NmQyYWYyNDhiNjJmOTg1Y2U0ZmJhNDI0MTcxYmI5MzBhM2NmMWU3MzczNTdjYTdmYmUwZWZhYTM5Mg==',
}

json_data = {
    'query': {
        'enterpriseId': 'MTAyNDY2MjY0MTYxMjI0',
        'keyword': '',
        'provinceCodes': [],
        'enterpriseMatchFields': [
            'winner',
        ],
        'informationTypes': [],
        'startTime': '',
        'endTime': '',
        'pageNum': 1,
        'pageSize': 20,
        'tenderPrincipalTypeCodes': [],
        'platform': 'pc',
    },
}

# 定义常量，减少硬编码
URL = 'https://xunbiaobao.baidu.com/crm/web/bid/xbb/na/bidding/search/api/enterprise'
REQUEST_DELAY = 1  # 请求间隔时间（秒）
MAX_CONCURRENT_REQUESTS = 2  # 最大并发请求数

# 从配置文件读取信息
def read_config(file_path):
    try:
        config = configparser.ConfigParser(interpolation=None)
        config.read(file_path, encoding='utf-8')
        sup_dic = {}
        for key, value in config.items('sup_dic'):
            index, sub_key = key.split('.')
            if index not in sup_dic:
                sup_dic[index] = {}
            sup_dic[index][sub_key] = value
        return sup_dic
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
        logging.error(f"{supName} 数据库连接失败")
        return

    try:
        mycursor = conn.cursor(buffered=True)
        start_date, end_date = get_time_range()
        if start_date is None:
            logging.warning("无法获取有效的开始日期，使用默认值 2025-04-01")
            start_date = datetime.date(2025, 4, 1)
            end_date = datetime.date(2025, 12, 31)

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
                response.raise_for_status()
                Js_data = response.json().get("data")
                if not Js_data:
                    logging.info(f"{supName} 没有数据")
                    break
                data_list = Js_data.get("dataList")
                if not data_list:
                    logging.info(f"{supName} 没有数据列表")
                    break
                for list_item in data_list:
                    publish_date_str = list_item.get("publishDate")
                    if not publish_date_str:
                        continue
                    publish_date = parse_date(publish_date_str)
                    if not publish_date or publish_date < start_date or publish_date > end_date:
                        logging.info(f"【寻标网】 {supName} 日期: {publish_date} 不符合区间")
                        break

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
                break
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
                process_and_insert_data(supName,conn, mycursor, data_all)
                # logging.info(f"{supName} 数据成功插入{len(data_all)-1}条")
                break
            except Exception as e:
                logging.error(f"{supName} 处理和插入数据时出错（第{attempt+1}次）: {e}")
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
        sup_dic = read_config('config/xunbiaow_cookies.txt')
        # sup_dic={
        #     '1': {
        #         'supname': '宁波华力信息系统工程有限公司',
        #         'enterpriseid': 'NTc0NTgzMzE3MjU5MTI4'}
        # }
        
        # 并发请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
            futures = []
            for value in sup_dic.values():
                futures.append(executor.submit(
                    getdata,
                    value.get("supname"),
                    value.get("enterpriseid"),
                    cookies,
                    headers,
                    json_data.copy()  # 每个线程用自己的json_data副本
                ))
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"线程任务出错: {e}")
    except Exception as e:
        logging.error(f"执行 get_xunbiaowang.py 时发生错误: {e}")

if __name__ == "__main__":
    scrape_data()