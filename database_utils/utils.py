import logging
import configparser
from datetime import datetime
import os

class FileUtils:
    @staticmethod
    def read_keywords():
        try:
            with open('config/keywords.txt', 'r', encoding='utf-8') as f:
                return [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            logging.error("关键字文件 config/keywords.txt 未找到。")
            return []

    def read_VIEWSTATE_config():
        try:
            with open('config/data_config_for_scrape.txt', 'r', encoding='utf-8') as f:
                return [line.strip() for line in f.readlines()]
        except Exception as e:
            logging.error(f"读取文件失败: {e}")
            return []

# 读取时间范围配置的方法
def get_time_range():
    config = configparser.ConfigParser()
    config.read('config/TimeRange.ini')
    try:
        start_date_str = config.get('TimeRange', 'start_date')
        end_date_str = config.get('TimeRange', 'end_date')
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        return start_date, end_date
    except Exception as e:
        logging.error(f"读取时间范围配置失败: {e}")
        return None, None

if __name__ == '__main__':
    print(FileUtils.read_VIEWSTATE_config())