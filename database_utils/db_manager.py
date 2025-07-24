import mysql.connector
from mysql.connector import pooling
import logging

class DBManager:
    def __init__(self):
        self.connection_pool = None
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

            # 创建连接池
            self.connection_pool = pooling.MySQLConnectionPool(
                pool_name="mypool",
                pool_size=5,
                host=host,
                user=user,
                password=password,
                database=database
            )
            
            # 从连接池获取连接
            self.conn = self.connection_pool.get_connection()
            self.cursor = self.conn.cursor()
            return self.conn
        except mysql.connector.Error as err:
            logging.error(f"连接数据库失败: {err}")
            return None
        except Exception as e:
            logging.error(f"读取数据库配置文件失败: {e}")
            return None
    def insert_data(self, project_number, project_name, publish_date, content, project_id, total_content, data_source, html_url):
        """单条插入方法，保持兼容性"""
        try:
            # 从连接池获取新连接
            conn = self.connection_pool.get_connection()
            cursor = conn.cursor()
            
            sql = "INSERT INTO bidding_info (project_number, project_name, publish_date, content, project_id, total_content, data_source, html_url,is_del) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            val = (project_number, project_name, publish_date, content, project_id, total_content, data_source, html_url,0)
            cursor.execute(sql, val)
            conn.commit()
        except mysql.connector.IntegrityError:
            # 处理重复数据
            pass
        except Exception as e:
            logging.error(f"插入数据时出错: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
   
    def batch_insert_data(self, data_list, batch_size=100):
        """批量插入方法"""
        try:
            # 从连接池获取新连接
            conn = self.connection_pool.get_connection()
            cursor = conn.cursor()
            
            sql = """INSERT INTO bidding_info 
                    (project_number, project_name, publish_date, content, project_id, total_content, data_source, html_url,is_del) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s,0)"""
            
            # 使用事务处理批量插入
            conn.start_transaction()
            try:
                # 分批处理数据
                for i in range(0, len(data_list), batch_size):
                    batch = data_list[i:i + batch_size]
                    cursor.executemany(sql, batch)
                
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                logging.error(f"批量插入时发生错误: {e}")
                return False
        except mysql.connector.Error as err:
            logging.error(f"批量插入数据失败: {err}")
            return False
        except Exception as e:
            logging.error(f"批量插入时发生未知错误: {e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    def check_project_id_exists(self, project_id):
        try:
            cursor = self.conn.cursor()
            # 假设表名为 your_table，列名为 item_id 和 project_number，根据实际情况修改
            query = "SELECT 1 FROM bidding_info WHERE project_id = %s"
            cursor.execute(query, (project_id))
            result = cursor.fetchone()
            return result is not None
        except Exception as e:
            logging.error(f"检查记录是否存在时出错: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
    def check_item_id_exists(self, project_number, item_id):
        try:
            cursor = self.conn.cursor()
            # 假设表名为 your_table，列名为 item_id 和 project_number，根据实际情况修改
            query = "SELECT 1 FROM bidding_info WHERE project_id = %s AND project_number = %s"
            cursor.execute(query, (item_id, project_number))
            result = cursor.fetchone()
            return result is not None
        except Exception as e:
            logging.error(f"检查记录是否存在时出错: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def close_connection(self):
        """优化后的连接关闭方法"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn and self.conn.is_connected():
                # 确保事务已提交或回滚
                if self.conn.unread_result:
                    self.conn.rollback()
                self.conn.close()
        except Exception as e:
            logging.error(f"关闭连接时发生错误: {e}")
        finally:
            # 保留连接池不关闭
            self.conn = None
            self.cursor = None

        # 关闭连接池
        if self.connection_pool:
            self.connection_pool.close()
