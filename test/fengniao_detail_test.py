from pandas.io.formats import printing
import requests
from lxml import html,etree
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
def get_detail_info(url):
    """从详情页获取详细招标信息，返回 HTML 格式内容"""
    # json_data = {
    #     'id': 'tGOkBDiauHbJ',
    #     'extractType': 'managementBidNotice',
    #     'orderNo': 'WEB202507250828411631052',
    # }
    # https://www.riskbird.com/detail/bidding?id=tGOkBDiauHbJ&orderNo=WEB202507250828411631052
    detail_json_data = {'id': url.split('id=')[1].split('&')[0],'extractType': 'managementBidNotice','orderNo': url.split('orderNo=')[1]}
    cookies = {
    'app-uuid': 'WEB-F7D4A1D21B3A442F88C7B6937008EB40',
    'app-device': 'WEB',
    'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwYXNzd29yZCI6IjE3NzgxYTc5ZjJjMzdhYWFmNGYwNTgyNWI3YmNjYzJjIiwiZXhwIjoxNzUzNDExNDAwLCJ1c2VySWQiOjEwNDczNDMsInV1aWQiOiIyZGRiNDAxZC0yZjViLTQzNmMtYmVjMC1iYzBjOTVhOTQyYzUiLCJ1c2VybmFtZSI6IjE4ODU4NDg0MzQ5In0.zl5I9Tki1bN3ypjTmnx3gUwc-yc8e6_1j7GLSkETAHY',
    'userinfo': '%7B%22userId%22%3A1047343%2C%22inviteCode%22%3A%22AAA77CD0FD5060E8%22%2C%22nickName%22%3A%2218858484349%22%2C%22unionid%22%3A%22oTZAV6-phOA5LpyZBKiBhp-UU9CM%22%2C%22isVip%22%3Atrue%2C%22vipStatus%22%3A%22vip%22%2C%22vipEndTime%22%3A%222030-06-16%22%2C%22mobile%22%3A%2218858484349%22%2C%22email%22%3Anull%2C%22timestamp%22%3A1753409600125%2C%22userNewType%22%3Atrue%2C%22vipTimeOut%22%3A1787%2C%22notGetLoginVip%22%3Afalse%2C%22vipExpireTime%22%3A1907855999000%2C%22isQueryRiskDoc%22%3Afalse%2C%22queryRiskDocSwitch%22%3A%221%22%2C%22status%22%3A%22vip%22%7D',
    'first-authorization': '1753409600125',
    }

    headers = {
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Connection': 'keep-alive',
        'Origin': 'https://www.riskbird.com',
        'Referer': 'https://www.riskbird.com/detail/bidding?id=tGOkBDiauHbJ&orderNo=WEB202507250828411631052',
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
        # 'Cookie': 'app-uuid=WEB-F7D4A1D21B3A442F88C7B6937008EB40; app-device=WEB; token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwYXNzd29yZCI6IjE3NzgxYTc5ZjJjMzdhYWFmNGYwNTgyNWI3YmNjYzJjIiwiZXhwIjoxNzUzNDExNDAwLCJ1c2VySWQiOjEwNDczNDMsInV1aWQiOiIyZGRiNDAxZC0yZjViLTQzNmMtYmVjMC1iYzBjOTVhOTQyYzUiLCJ1c2VybmFtZSI6IjE4ODU4NDg0MzQ5In0.zl5I9Tki1bN3ypjTmnx3gUwc-yc8e6_1j7GLSkETAHY; userinfo=%7B%22userId%22%3A1047343%2C%22inviteCode%22%3A%22AAA77CD0FD5060E8%22%2C%22nickName%22%3A%2218858484349%22%2C%22unionid%22%3A%22oTZAV6-phOA5LpyZBKiBhp-UU9CM%22%2C%22isVip%22%3Atrue%2C%22vipStatus%22%3A%22vip%22%2C%22vipEndTime%22%3A%222030-06-16%22%2C%22mobile%22%3A%2218858484349%22%2C%22email%22%3Anull%2C%22timestamp%22%3A1753409600125%2C%22userNewType%22%3Atrue%2C%22vipTimeOut%22%3A1787%2C%22notGetLoginVip%22%3Afalse%2C%22vipExpireTime%22%3A1907855999000%2C%22isQueryRiskDoc%22%3Afalse%2C%22queryRiskDocSwitch%22%3A%221%22%2C%22status%22%3A%22vip%22%7D; first-authorization=1753409600125',
    }


    response = requests.post(
        'https://www.riskbird.com/riskbird-api/companyInfo/detail',
        cookies=cookies,
        headers=headers,
        json=detail_json_data,
    )
    if response.status_code == 200:
        Js_data = response.json().get("data")
        if not Js_data:
            logging.info("没有数据")
        else :
             logging.info(Js_data.get("znum"))
             logging.info(Js_data.get("content"))
        return      Js_data.get("znum") ,Js_data.get("content")


    else:
            print(f"获取详情页失败。状态码: {response.status_code}")



if __name__ == "__main__":
    url = 'https://www.riskbird.com/detail/bidding?id=tGOkBDiauHbJ&orderNo=WEB202507250828411631052'  # 替换为实际的 URL
    get_detail_info(url)
    
