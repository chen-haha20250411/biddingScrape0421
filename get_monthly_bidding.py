import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import re
from lxml import etree

# Disable proxy settings
os.environ['no_proxy'] = '*'
os.environ['NO_PROXY'] = '*'
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

def ensure_bidding_folder():
    """Ensure the bidding folder exists on desktop"""
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    bidding_folder = os.path.join(desktop, "bidding")
    
    if not os.path.exists(bidding_folder):
        os.makedirs(bidding_folder)
        print(f"Created folder: {bidding_folder}")
    
    return bidding_folder

def get_latest_csv_file(bidding_folder):
    """Get the latest CSV file in the bidding folder"""
    csv_files = [f for f in os.listdir(bidding_folder) if f.endswith('.csv')]
    if not csv_files:
        return None
    
    # Sort files by creation time
    csv_files.sort(key=lambda x: os.path.getctime(os.path.join(bidding_folder, x)), reverse=True)
    return os.path.join(bidding_folder, csv_files[0])

def load_existing_records(csv_file):
    """Load existing records from CSV file"""
    if not csv_file or not os.path.exists(csv_file):
        return pd.DataFrame()
    
    try:
        return pd.read_csv(csv_file, encoding='utf-8-sig')
    except Exception as e:
        print(f"Error loading existing records: {str(e)}")
        return pd.DataFrame()

def is_current_month(date_str):
    """Check if the date is in the current month"""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        current_date = datetime.now()
        return date.year == current_date.year and date.month == current_date.month
    except:
        return False

def get_detail_info(url):
    """Get detailed bidding information from the view page"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        session = requests.Session()
        session.trust_env = False  # Disable proxy for this session
        response = session.get(url, headers=headers, proxies={})
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract the main content
            content_div = soup.find('div', {'class': 'content'})
            if content_div:
                # Get all text content
                detail_info = {
                    '页面内容': content_div.get_text(separator='\n', strip=True)
                }
                
                # Get original announcement link if exists
                original_link = soup.find('a', text='查看原公告')
                if original_link:
                    detail_info['原公告链接'] = original_link.get('href', '')
                
                return detail_info
            else:
                print("No content found on the detail page")
                return None
        else:
            print(f"Failed to fetch detail page. Status code: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error fetching detail information: {str(e)}")
        return None

def format_output(records):
    """Format records into a readable string"""
    output = []
    output.append("=" * 100)
    output.append("政府采购招标信息汇总")
    output.append("=" * 100)

    for idx, record in enumerate(records, 1):
        output.append(f"\n记录 {idx}:")
        output.append("-" * 50)
        output.append(f"区域: {record['区域']}")
        output.append(f"品目名称: {record['品目名称']}")
        output.append(f"公告名称: {record['公告名称']}")
        output.append(f"发布日期: {record['发布日期']}")
        output.append(f"详细链接: {record['详细链接']}")

        # 删除这行代码
        # details = record.get('详细信息')

        if record.get('详细信息') is not None:
            if isinstance(record.get('详细信息'), dict):
                for key, value in record.get('详细信息').items():  # 字典调用 items() 方法没问题
                    output.append(f"{key}: {value}")
            elif isinstance(record.get('详细信息'), list):
                output.append("详细信息为列表类型:")
                for item in record.get('详细信息'):
                    if isinstance(item, dict):
                        for key, value in item.items():  # 列表元素为字典时调用 items() 方法没问题
                            output.append(f"{key}: {value}")
                    else:
                        output.append(str(item))
            else:
                output.append(f"详细信息: {record.get('详细信息')}")
        else:
            output.append("详细信息: 无")

        output.append("-" * 50)

    return "\n".join(output)

def get_bidding_info():
    url = "https://zfcg.czj.ningbo.gov.cn/project/zcyNotice.aspx"
    params = {'noticetype': '2'}
    base_url = "https://zfcg.czj.ningbo.gov.cn/project/"
    
    try:
        # Ensure bidding folder exists
        bidding_folder = ensure_bidding_folder()
        
        # Initialize lists to store all data
        all_data = []
        max_pages = 20  # 设置最大翻页次数
        current_page = 1
        stop_fetching = False
        
        # Initialize session
        session = requests.Session()
        session.trust_env = False  # Disable proxy for this session
        
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
        }

        # Process all pages
        while current_page <= max_pages and not stop_fetching:
            print(f"\nFetching page {current_page}/{max_pages}...")
            
            # Update URL parameters for pagination
            page_params = params.copy()
            page_params['page'] = str(current_page)
            page_params['pagesize'] = '20'
            
            # Send GET request
            response = session.get(url, params=page_params, headers=headers)
            response.encoding = 'utf-8'
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Process current page
                table = None
                for t in soup.find_all('table'):
                    if t.find('tr') and t.find('td'):
                        headers = [th.text.strip() for th in t.find_all('th')]
                        if any('区域' in h for h in headers) or any('品目' in h for h in headers):
                            table = t
                            break
                
                if table:
                    rows = table.find_all('tr')[1:]
                    page_data = []
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 4:
                            date_str = cols[3].text.strip()
                            if not is_current_month(date_str):
                                stop_fetching = True
                                break
                                
                            # 从公告名称列中提取链接和文本
                            notice_col = cols[2]
                            notice_link = notice_col.find('a')
                            if notice_link:
                                notice_text = notice_link.text.strip()
                                notice_href = notice_link.get('href', '')
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
                        print(f"Found {len(page_data)} records on page {current_page}")
                        current_page += 1
                    else:
                        print("No data found on current page, stopping pagination")
                        break
                else:
                    print("No bidding information table found on the page")
                    break
            else:
                print(f"Failed to fetch page {current_page}. Status code: {response.status_code}")
                break
        
        if all_data:
            # Convert to DataFrame
            df = pd.DataFrame(all_data)
            total_count = len(df)
            print(f"\nTotal records found for current month: {total_count}")
            
            if not df.empty:
                # Get detailed information for all records
                df['详细信息'] = df['详细链接'].apply(lambda x: get_detail_info(x) if x else None)
                
                # 移除保存文本文件的代码
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                csv_file = os.path.join(bidding_folder, f"bidding_info_{timestamp}.csv")
                df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                print(f"CSV data saved to {csv_file}")
            
            return df
        else:
            print("No data found")
            return None
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

if __name__ == "__main__":
    print("Starting to scrape bidding information...")
    bidding_data = get_bidding_info()
    if bidding_data is not None:
        print("\nFirst few records:")
        print(bidding_data.head())