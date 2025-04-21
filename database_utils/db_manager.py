import mysql.connector
import logging

class DBManager:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect_db(self):
        try:
            # 修改文件路径
            with open('config/mysqlcon.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                host = lines[0].strip()
                user = lines[1].strip()
                password = lines[2].strip()
                database = lines[3].strip()

            self.conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            self.cursor = self.conn.cursor()
            return self.conn
        except mysql.connector.Error as err:
            logging.error(f"连接数据库失败: {err}")
            return None
        except Exception as e:
            logging.error(f"读取数据库配置文件失败: {e}")
            return None
    def insert_data(self, project_number, project_name, publish_date, content, project_id, total_content, data_source, html_url):
        if self.conn and self.cursor:
            try:
                sql = "INSERT INTO bidding_info (project_number, project_name, publish_date, content, project_id, total_content, data_source, html_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                val = (project_number, project_name, publish_date, content, project_id, total_content, data_source, html_url)
                self.cursor.execute(sql, val)
            except mysql.connector.IntegrityError:
                # 处理重复数据
                pass

    def check_item_id_exists(self, item_id):
        if self.conn and self.cursor:
            sql = "SELECT 1 FROM bidding_info WHERE project_number = %s LIMIT 1"
            self.cursor.execute(sql, (item_id,))
            return self.cursor.fetchone() is not None

    def close_connection(self):
        if self.conn:
            self.conn.commit()
            self.cursor.close()
            self.conn.close()