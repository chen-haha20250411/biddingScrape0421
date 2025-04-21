import os
import requests
from bs4 import BeautifulSoup

# 禁用代理设置
os.environ['no_proxy'] = '*'
os.environ['NO_PROXY'] = '*'
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

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
            return response.text
        else:
            print(f"获取详情页失败。状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"获取详细信息时出错: {str(e)}")
        return None

if __name__ == "__main__": 
    url = f'https://zfcg.czj.ningbo.gov.cn/project/zcyNotice_view.aspx?Id=202504151700291912068500248203264'
    detail_info = get_detail_info(url)
    if detail_info:
        print("详细信息（HTML 格式）:")
        print(detail_info)