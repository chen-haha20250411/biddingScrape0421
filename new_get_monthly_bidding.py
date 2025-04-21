import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import time  # 导入 time 模块用于添加延迟
# 导入新文件中的函数
from detail_info_fetcher import get_detail_info

# 禁用代理设置
os.environ['no_proxy'] = '*'
os.environ['NO_PROXY'] = '*'
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''


def ensure_bidding_folder():
    """确保桌面的 bidding 文件夹存在"""
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    bidding_folder = os.path.join(desktop, "bidding")

    if not os.path.exists(bidding_folder):
        os.makedirs(bidding_folder)
        print(f"已创建文件夹: {bidding_folder}")

    return bidding_folder


def is_current_month(date_str):
    """检查日期是否为本月"""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        current_date = datetime.now()
        return date.year == current_date.year and date.month == current_date.month
    except Exception as e:
        print(f"日期解析错误: {str(e)}")
        return False


def get_bidding_info():
    try:
        # 确保 bidding 文件夹存在
        bidding_folder = ensure_bidding_folder()

        all_data = []
        total_pages = 2
        stop_fetching = False
        current_page = 1  # 定义并初始化 current_page
        while current_page <= total_pages and not stop_fetching:
            try:
                cookies = {'ASP.NET_SessionId': '78240389EAB70F38E99ADEF9',}
                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
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
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.95 Safari/537.36',
                    'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"', }
                params = { 'noticetype': '2',}
                page_data = []
                # 获取data_config_for_scrape.txt的内容
                with open('data_config_for_scrape.txt', 'r', encoding='utf-8') as f:
                    data = f.read()
                    data = data.strip()  # 去除首尾空白字符
                    data = data.split('\n')  # 按行分割
                    # 假设 data 最终需要转换为字典，这里简单拼接示例
                    data_str = '\n'.join(data)
                    data_dict = {}
                    # 简单按 key=value 格式解析，可根据实际情况调整
                    for line in data_str.split('\n'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            data_dict[key] = value
                    data = data_dict
                    data['__EVENTARGUMENT'] = str(current_page)
                # 明确不使用代理
                proxies = {
                    'http': None,
                    'https': None
                }
                response = requests.post(
                    'https://zfcg.czj.ningbo.gov.cn/project/zcyNotice.aspx',
                    params=params,
                    cookies=cookies,
                    headers=headers,
                    data=data,
                    proxies=proxies
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

                    if table:
                        rows = table.find_all('tr')[1:]
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) >= 4:
                                date_str = cols[3].text.strip()
                                if not is_current_month(date_str):
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

                                bidding_info = {
                                    '区域': cols[0].text.strip(),
                                    '品目名称': cols[1].text.strip(),
                                    '公告名称': notice_text,
                                    '发布日期': date_str,
                                    '详细链接': notice_href
                                }

                                # 检查数据是否重复
                                # if bidding_info not in all_data:
                                #     page_data.append(bidding_info)
                                page_data.append(bidding_info)

                        if page_data:
                            all_data.extend(page_data)
                            print(f"在第 {current_page} 页找到 {len(page_data)} 条新记录")
                        else:
                            print("页面上未找到招标信息表格")
                            stop_fetching = True
                    else:
                        print(f"获取第 {current_page} 页失败。状态码: {response.status_code}")
                        stop_fetching = True

            except Exception as e:
                print(f"获取第 {current_page} 页时出错: {str(e)}")
                stop_fetching = True

            current_page += 1
            time.sleep(2)  # 每次请求后添加 2 秒延迟，模拟人类操作

        if all_data:
            df = pd.DataFrame(all_data)
            total_count = len(df)
            print(f"\n本月共找到 {total_count} 条记录")

            if not df.empty:
                # df['详细信息'] = df['详细链接'].apply(lambda x: get_detail_info(x) if x else None)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                csv_file = os.path.join(bidding_folder, f"bidding_info_{timestamp}.csv")
                df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                print(f"CSV 数据已保存到 {csv_file}")
            return df
        else:
            print("未找到数据")
            return None

    except Exception as e:
        print(f"发生错误: {str(e)}")
        return None


if __name__ == "__main__":
    print("开始采集招标信息...")
    bidding_data = get_bidding_info()
    if bidding_data is not None:
        print("\n所有记录:")
        print(bidding_data[['区域', '品目名称', '公告名称', '发布日期', '详细链接']])
