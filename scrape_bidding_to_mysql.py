import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import pandas as pd


def get_total_pages(soup):
    try:
        # 查找包含分页信息的 td 标签
        td_tag = soup.find('td', nowrap="true", style="width:40%")
        if td_tag:
            # 提取 td 标签中的文本
            pagination_text = td_tag.get_text(strip=True)
            # 从文本中提取总页数
            total_pages_str = pagination_text.split('/')[-1].split('页')[0].strip()
            total_pages = int(total_pages_str)
            return total_pages
        else:
            print("未找到包含分页信息的 td 标签")
    except Exception as e:
        print(f"获取总页数失败: {e}")
    return 2


def extract_hidden_fields(soup):
    """从页面中提取隐藏字段"""
    hidden_fields = {}
    for input_tag in soup.find_all('input', type='hidden'):
        name = input_tag.get('name')
        value = input_tag.get('value')
        if name and value:
            hidden_fields[name] = value
    return hidden_fields


def ensure_bidding_folder():
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    bidding_folder = os.path.join(desktop, "bidding")

    if not os.path.exists(bidding_folder):
        os.makedirs(bidding_folder)
        print(f"已创建文件夹: {bidding_folder}")

    return bidding_folder


def is_current_month(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        current_date = datetime.now()
        return date_obj.year == current_date.year and date_obj.month == current_date.month
    except ValueError:
        print(f"日期格式错误: {date_str}")
        return False


def read_data_config():
    try:
        with open('data_config_for_scrape.txt', 'r', encoding='utf-8') as f:
            data = f.read()
            data = data.strip()  # 去除首尾空白字符
            data = data.split('\n')  # 按行分割
            data_dict = {}
            for line in data:
                if '=' in line:
                    key, value = line.split('=', 1)
                    data_dict[key] = value
            return data_dict
    except FileNotFoundError:
        print("未找到 data_config_for_scrape.txt 文件")
        return {}


def get_bidding_info(noticetype):
    try:
        # 确保 bidding 文件夹存在
        bidding_folder = ensure_bidding_folder()
        all_data = []
        stop_fetching = False
        current_page = 1
        total_pages = 2  # 初始化为一个较大的值，确保至少执行一次循环
        cookies = {
            'ASP.NET_SessionId': '78240389EAB70F38E99ADEF9',
        }
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://zfcg.czj.ningbo.gov.cn',
            'Referer': f'https://zfcg.czj.ningbo.gov.cn/project/zcyNotice.aspx?noticetype={noticetype}',
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
            'noticetype': noticetype,
        }
        data_config = read_data_config()
        hidden_fields = {}
        while current_page <= total_pages and not stop_fetching:
            page_data = []
            try:
                data = data_config.copy()
                data['__EVENTARGUMENT'] = str(current_page)
                data.update(hidden_fields)  # 将隐藏字段添加到POST数据中

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
                    total_pages = get_total_pages(soup)
                    print(f"总页数: {total_pages}")
                    hidden_fields = extract_hidden_fields(soup)
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
                                    base_url = 'https://zfcg.czj.ningbo.gov.cn'
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
                                page_data.append(bidding_info)

                        if page_data:
                            all_data.extend(page_data)
                            print(f"在第 {current_page} 页找到 {len(page_data)} 条新记录")
                        else:
                            print("页面上未找到招标信息表格")
                            stop_fetching = True
                    else:
                        print(f"获取第 {current_page} 页失败，未找到符合条件的表格。状态码: {response.status_code}")
                        stop_fetching = True
                else:
                    print(f"获取第 {current_page} 页失败。状态码: {response.status_code}")
                    stop_fetching = True

            except Exception as e:
                print(f"获取第 {current_page} 页时出错: {str(e)}")
                stop_fetching = True

            current_page += 1
            import time
            time.sleep(2)  # 每次请求后添加 2 秒延迟，模拟人类操作

        if all_data:
            df = pd.DataFrame(all_data)
            total_count = len(df)
            print(f"\n本月共找到 {total_count} 条 {noticetype} 类型的记录")

            if not df.empty:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                csv_file = os.path.join(bidding_folder, f"bidding_info_{noticetype}_{timestamp}.csv")
                df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                print(f"CSV 数据已保存到 {csv_file}")
            return df
        else:
            print(f"未找到 {noticetype} 类型的数据")
            return None

    except Exception as e:
        print(f"发生错误: {str(e)}")
        return None


if __name__ == "__main__":
    print("开始采集招标信息...")
    # 采集原有的 noticetype=2 的信息
    get_bidding_info('2')
    print("开始采集中标信息...")
    # 采集 noticetype=51-52 的中标信息

    