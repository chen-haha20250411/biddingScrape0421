import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import time
import random
from lxml import html, etree
import logging
from database_utils.utils import FileUtils, get_time_range  # 导入 FileUtils 和 get_time_range 函数
from database_utils.db_manager import DBManager  # 导入 DBManager 类

# 禁用代理设置
os.environ['no_proxy'] = '*'
os.environ['NO_PROXY'] = '*'
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

# 全局变量
cookies = {
    'ASP.NET_SessionId': 'A04C7BCF5A774099812F7986',
}

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://zfcg.czj.ningbo.gov.cn',
    'Referer': 'https://zfcg.czj.ningbo.gov.cn/project/zcyNotice.aspx?noticetype=2',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0',
    'sec-ch-ua': '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    # 'Cookie': 'ASP.NET_SessionId=A04C7BCF5A774099812F7986',
}


def get_detail_info(url):
    """从详情页获取详细招标信息，返回 HTML 格式内容"""
    try:
        detail_params = {'Id': url.split('Id=')[1]}
        response = requests.get(
            'https://zfcg.czj.ningbo.gov.cn/project/zcyNotice_view.aspx',
            params=detail_params,
            cookies=cookies,
            headers=headers
        )
        response.encoding = 'utf-8'
        if response.status_code == 200:
            tree = etree.HTML(response.text)
            total_content = response.text if response.text else ''
            try:
                # 提取项目编号到项目名称之间的内容
                project_number = tree.xpath('//text()[contains(., "项目编号：")]/following::text()[1]')
                project_number1 = tree.xpath('//text()[contains(., "项目编号")]')
                if project_number:
                    project_number_text = project_number[0].split("项目名称")[0].strip()
                    if project_number_text == '':
                        project_number_text = (project_number1[0].split("项目名称")[0].strip()).split("：")[1].strip()
                else:
                    project_number_text = ''
                # 或者更精确地提取项目编号
                project_title = tree.xpath('//text()[contains(., "项目名称：")]/following::text()[1]')
                if project_title:
                    project_title_text = project_title[0].split("预算金额")[0].strip()
                else:
                    project_title_text = ''
                return project_number_text,total_content
            except Exception as e:
                print(f"提取政府招标网详细页面时出错: {str(e)}")
                return '', '', total_content
        else:
            print(f"获取政府招标网详情页失败。状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"请求详情页时出错: {str(e)}")
        return None


def scrape_data():
    print("政府采购网开始采集招标信息...")
    min_delay = 1
    max_delay = 3
    start_date, end_date = get_time_range()
    print(f"开始时间: {start_date} 结束时间: {end_date}")
    if start_date is None or end_date is None or start_date=='' or end_date=='':
        print("无法获取有效的时间范围。")
        return None
    else:
        start_date = '2025-04-01'
        end_date = '2025-05-30'
    
    # 将字符串日期转换为datetime对象
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    keywords = FileUtils.read_keywords()
    VIEWSTATE = FileUtils.read_VIEWSTATE_config()
    # 确保 VIEWSTATE 不是列表
    if isinstance(VIEWSTATE, list):
        VIEWSTATE = VIEWSTATE[0] if VIEWSTATE else ''

    try:
        db_manager = DBManager()
        db_manager.connect_db()
        all_data = []
        stop_fetching = False
        current_page = 1
        max_retries = 3  # 添加最大重试次数
        retry_count = 0  # 添加重试计数器
        processed_project_ids = set()
        processed_project_numbers = set()

        while not stop_fetching :
            try:
                params = {'noticetype': '2',}
                page_data = []
                data_dict = { 
                    'ddlNoticeCategory': '2',
                    'ddlRegion': '',
                    'txtProjectCode': '',
                    'txtNoticeTitle': '',
                    'txtNoticeDate1': '',
                    'txtNoticeDate2': '',
                    'pager_input': '1',
                    '__EVENTARGUMENT': str(current_page),
                    '__EVENTVALIDATION': '/wEdAAEAAAD/////AQAAAAAAAAAPAQAAACoAAAAI7B8geKJluxAY6QJJ5FpDT0iTMrvMNu4/mFgs0qE5TPNwkzCG3ehzstMxLQ3kd1t0cIhQbRs8OAdGImrXITIU2QRNXonJ6kw0h09aFU0PzNj8bp8ZMCkemwxI3etR436dz/Kor9S2t8I0syNvqRPlHeCnwkZkOF1576jJ8mTw4Y2hZUU3TViMvPaSE6fwcWEfe92rsqbOWyzx57p9OEI7Cs4Vz75f8UBACwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIFzi/EY1615mwTY4oYTBF8XDUum+hHov71XPUszGnSq',
                    '__EVENTTARGET': 'pager',
                }
                data_dict['__VIEWSTATE']= VIEWSTATE

                proxies = {
                    'http': None,
                    'https': None
                }

                if current_page == 1:
                    response = requests.get('https://zfcg.czj.ningbo.gov.cn/project/zcyNotice.aspx', params=params, cookies=cookies, headers=headers)
                else:
                    # print(f"正在处理第 {current_page} 页, {data_dict}")
                    
                    response = requests.post(
                        'https://zfcg.czj.ningbo.gov.cn/project/zcyNotice.aspx',
                        params=params,
                        cookies=cookies,
                        headers=headers,
                        data=data_dict,
                        proxies=proxies,
                    )

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    table = None
                    for t in soup.find_all('table'):
                        if t.find('tr') and t.find('td'):
                            headers_list = [th.text.strip() for th in t.find_all('th')]
                            if any('区域' in h for h in headers_list) or any('品目' in h for h in headers_list):
                                table = t
                                break
                    if table :
                        rows = table.find_all('tr')[1:]
                        if not rows:  # 如果表格没有数据行
                            print(f"政府采购网第 {current_page} 页表格为空，停止抓取")
                            stop_fetching = True
                            break

                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols)==4:
                                date_str = cols[3].text.strip()
                                publish_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
                                
                                # 检查日期是否在范围内
                                if publish_date:
                                    if publish_date < start_datetime or publish_date > end_datetime:
                                        print(f"政府采购网日期 {publish_date} 不在配置范围内，停止抓取")
                                        stop_fetching = True
                                        break

                                notice_col = cols[2]
                                notice_link = notice_col.find('a')
                                if notice_link:
                                    notice_text = notice_link.text.strip()
                                    notice_href = notice_link.get('href', '')
                                    base_url = 'https://zfcg.czj.ningbo.gov.cn'  # 假设 base_url
                                    if notice_href and not notice_href.startswith('http'):
                                        notice_href = base_url + notice_href
                                else:
                                    notice_text = notice_col.text.strip()
                                    notice_href = None
                                
                                data_source = 'https://zfcg.czj.ningbo.gov.cn'
                                matched_keywords = []
                                for keyword in keywords:
                                    if keyword in notice_text or keyword in cols[1].text.strip():
                                        matched_keywords.append(keyword)
                                   
                                if matched_keywords:
                                    project_title = f"政府采购网 关键字【{matched_keywords}】{notice_text}"
                                    project_id = notice_href.split('Id=')[1] if notice_href else ''
                                    # 检查project_id是否已存在
                                    if project_id in processed_project_ids:
                                        print(f"政府采购网记录ID {project_id} 已处理，跳过")
                                        continue
                                    # 检查数据库中是否存在
                                    if db_manager.check_project_id_exists((project_id,)):
                                        print(f"政府采购网记录ID {project_id} 已存在于数据库，跳过")
                                        processed_project_ids.add(project_id)
                                        continue
                                    html_url = f"https://zfcg.czj.ningbo.gov.cn/project/zcyNotice_view.aspx?Id={project_id}"
                                    # 检查project_number是否已存在
                                    if project_id in processed_project_numbers:
                                        print(f"政府采购网项目编号 {project_id} 已处理，跳过")
                                        continue
                                    # 不存在则查询详情页
                                    project_number, detail_result = get_detail_info(notice_href)
                                    print(f"第{current_page}页 ,发布日期： {publish_date}, 项目编号: {project_number}, 项目名称: {project_title}, 详情页链接: {notice_href}")  # 调试用，打印项目信息和详情页链接
                                    if project_number:
                                        # 添加到已处理集合
                                        processed_project_ids.add(project_id)
                                        processed_project_numbers.add(project_number)
                                        # 将数据封装成元组
                                        page_data.append((project_number, project_title, publish_date, '', project_id, detail_result, data_source, html_url))
                        if page_data:
                            all_data.extend(page_data)
                            print(f"在政府采购网第 {current_page} 页找到 {len(page_data)} 条新记录")
                            retry_count = 0  # 重置重试计数
                        else:
                            print(f"政府采购网获取第 {current_page} 页成功，但未找到新数据。")
                            retry_count += 1  # 增加重试计数
                            if retry_count >= max_retries:
                                print(f"连续 {max_retries} 页未找到新数据，停止抓取")
                                stop_fetching = True
                                break
                    else:
                        print(f"政府采购网获取第 {current_page} 页成功，但未找到表格。")
                        retry_count += 1
                        if retry_count >= max_retries:
                            print(f"连续 {max_retries} 页未找到表格，停止抓取")
                            stop_fetching = True
                            break

                else:
                    print(f"政府采购网获取第 {current_page} 页失败。状态码: {response.status_code}")
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"连续 {max_retries} 次请求失败，停止抓取")
                        stop_fetching = True
                        break

                current_page += 1
                time.sleep(random.uniform(min_delay, max_delay))

            except Exception as e:
                print(f"政府采购网获取第 {current_page} 页时出错: {str(e)}")
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"连续 {max_retries} 次发生错误，停止抓取")
                    stop_fetching = True
                    break

        if all_data:
            try:
                success = db_manager.batch_insert_data(all_data)
                if success:
                    print(f"政府采购网成功批量插入 {len(all_data)} 条数据")
                else:
                    logging.error("政府采购网批量插入数据失败")
            except Exception as e:
                logging.error(f"政府采购网批量插入数据时发生异常: {e}")
                raise
            finally:
                if hasattr(db_manager, 'conn') and db_manager.conn:
                    db_manager.conn.close()
                    print("数据库连接已关闭")
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return None


if __name__ == "__main__":
    scrape_data()
    