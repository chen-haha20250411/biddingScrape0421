
from math import log
import requests,re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
import time
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

cookies = {
    'ASP.NET_SessionId': '3764A518622AB32C6E288CF1',
}

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    # 'Cookie': 'ASP.NET_SessionId=3764A518622AB32C6E288CF1',
    'Origin': 'https://zfcg.czj.ningbo.gov.cn',
    'Referer': 'https://zfcg.czj.ningbo.gov.cn/project/zcyNotice.aspx?noticetype=2',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.95 Safari/537.36',
    'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

params = {
    'noticetype': '2',
}
              
def read_keywords():
        try:
            with open('../config/keywords.txt', 'r', encoding='utf-8') as f:
                return [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            logging.error("关键字文件 config/keywords.txt 未找到。")
            return []

def get_detail_info(url):
    """从详情页获取详细招标信息，返回 HTML 格式内容"""
    try:
        params = {'Id': url.split('Id=')[1]}
        # print(f"params: {params}")
        cookies = {
            'ASP.NET_SessionId': '78240389EAB70F38E99ADEF9',
        }

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Referer': 'https://zfcg.czj.ningbo.gov.cn/project/zcyNotice.aspx?noticetype=2',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.95 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        response = requests.get(
            'https://zfcg.czj.ningbo.gov.cn/project/zcyNotice_view.aspx',
            params=params,
            cookies=cookies,
            headers=headers
        )

        response.encoding = 'utf-8'
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            total_content = response.text if response.text else ''
            project_number = soup.xpath('//*[@id="floor"]/div/div/div[2]/div/table/tbody/tr/td/p[10]/span/span[2]')[0].strip() if soup.xpath('//*[@id="floor"]/div/div/div[2]/div/table/tbody/tr/td/p[10]/span/span[2]') else ''
            custname= soup.xpath('//*[@id="floor"]/div/div/div[2]/div/table/tbody/tr/td/p[100]/span')[0].strip() if soup.xpath('//*[@id="floor"]/div/div/div[2]/div/table/tbody/tr/td/p[100]/span') else ''
            return total_content, project_number, custname
        else:
            print(f"获取详情页失败。状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"获取详细信息时出错: {str(e)}")
        return None

def scrape_data():
    # 获取时间范围和关键字列表
    # 手动设置时间范围作为临时解决方案
    start_date = datetime.strptime("2025-04-21", "%Y-%m-%d").date()
    end_date = datetime.strptime("2025-12-31", "%Y-%m-%d").date()
    logging.info(f"使用默认时间范围: 开始日期 {start_date}, 结束日期 {end_date}")
    keywords = read_keywords()
    seen_items = set()  # 用于存储已见过的项目，避免重复
    records = {}
    session = requests.Session()  # 使用session保持会话状态
    # 获取初始页面
    initial_response = session.get(
        'https://zfcg.czj.ningbo.gov.cn/project/zcyNotice.aspx',
        params=params,
        headers=headers
    )
    
    if initial_response.status_code != 200:
        print('初始页面获取失败，状态码：', initial_response.status_code)
        return
    
    page = 1
    stop_flag = False
    while  not stop_flag:
        print(f"\n正在获取第 {page} 页...")
        
        if page == 1:
            response = initial_response
        else:
            # 解析当前页面获取ViewState等参数
            current_soup = BeautifulSoup(response.text, 'html.parser')
            viewstate = current_soup.find('input', {'name': '__VIEWSTATE'})['value']
            eventvalidation = current_soup.find('input', {'name': '__EVENTVALIDATION'})['value']
            form_data = {
                '__EVENTTARGET': '',  # 下页按钮的事件目标
                '__EVENTARGUMENT': str(page),  # 下页按钮的事件参数
                '__VIEWSTATE': viewstate,
                '__EVENTVALIDATION': eventvalidation,
                'ddlNoticeCategory': '2',
                'ddlRegion': '',
                'txtProjectCode': '',
                'txtNoticeTitle': '',
                'txtNoticeDate1': '',
                'txtNoticeDate2': '',
                'pager_input': '1',
                '__EVENTTARGET': 'pager'
           
            }
            # 发送POST请求获取下一页
            response = session.post(
                'https://zfcg.czj.ningbo.gov.cn/project/zcyNotice.aspx',
                params=params,
                headers=headers,
                data=form_data
            )
            
            if response.status_code != 200:
                print(f'第 {page} 页请求失败，状态码：{response.status_code}')
                break
        
        soup = BeautifulSoup(response.text, 'lxml')
        table = soup.find('table', id='gdvNotice3')
        new_items_count = 0
        rows = table.find_all('tr')
        # 提取第2到第16行数据
        for i in range(1, len(rows)):
            row = rows[i]
            cells = row.find_all('td')
            if len(cells) >= 4:
                area = cells[0].text.strip() if cells[0] else ""
                item_name = cells[1].text.strip() if cells[1] else ""
                notice_name = cells[2].text.strip() if cells[2] else ""
                publish_date = cells[3].text.strip() if cells[3] else ""
                publish_date_formart = datetime.strptime(publish_date, '%Y-%m-%d').date()
                # 提取a标签的href属性
                link = cells[2].find('a')
                if link:
                    href = link.get('href', '')
                    project_id = href.split('Id=')[1] if 'Id=' in href else ''
                    # 获取详情页信息
                    detail_info = get_detail_info(href)
                    if detail_info is None:
                        continue
                    total_content, project_NO, custname = detail_info
                    
                if publish_date_formart < start_date or publish_date_formart > end_date:
                    stop_flag = True
                    break
                matched_keywords = [k for k in keywords if k in item_name or k in notice_name]
                if not matched_keywords:
                    continue
                
                records[item_name] = {
                    "title": notice_name,
                    "publish_date": publish_date_formart,
                    "item_name": item_name,
                    "notice_name": notice_name,
                    "url": href,
                    "project_id": project_id,
                    "project_NO": project_NO,
                    "content": total_content,
                    "custname": custname
                }
                logging.info(f"发现新记录: {item_name}")
                new_items_count += 1
        
        print(f"第 {page} 页发现 {new_items_count} 条新记录")
        page += 1
        # 添加适当的延时，避免请求过快
        time.sleep(2)
    
    return records

if __name__ == "__main__":
    scrape_data()