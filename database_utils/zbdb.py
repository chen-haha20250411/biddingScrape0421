import logging
from math import log
import mysql.connector

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_and_insert_data(supName,connection, mycursor, data_all, batch_size=100):
    update_data = []
    insert_data = []
    
    for row in data_all[1:]:
        publish_date, project_no, customer, notice_type, title, product_labels, winner_amount, remark, winner_principal = row
        logging.info(f"项目编号: {project_no}, 客户: {customer}, 公告类型: {notice_type}, 标题: {title}, 产品标签: {product_labels}, 中标金额: {winner_amount}, 备注: {remark}, 中标人: {winner_principal}")
        check_query = "SELECT projectNo, customer, winnerAmount, noticeType FROM zhongbiao WHERE `projectNo` = %s"
        try:
            mycursor.execute(check_query, (project_no,))
            existing_row = mycursor.fetchone()
            mycursor.fetchall()
        except mysql.connector.Error as err:
            logging.error(f"检查数据时出错: {err}")
            continue

        if existing_row:
            # logging.info(f"金额：{existing_row[2]},公告类型:{existing_row[3]}")
            existing_amount = existing_row[2]
            existing_notice_type = existing_row[3]
            if float(existing_amount) != float(winner_amount) and existing_notice_type != notice_type:
                update_data.append((publish_date, customer, notice_type, title, product_labels, winner_amount, remark, winner_principal, project_no))
        else:
            insert_data.append((publish_date, project_no, customer, notice_type, title, product_labels, winner_amount, remark, winner_principal))

    try:
        # 执行更新操作
        if update_data:
            for i in range(0, len(update_data), batch_size):
                batch = update_data[i:i + batch_size]
                update_query = """
                UPDATE zhongbiao 
                SET `publishDate` = %s, `customer` = %s, `noticeType` = %s, `title` = %s, 
                    `productLabels` = %s, `winnerAmount` = %s, `remark` = %s, `winnerPrincipal` = %s 
                WHERE `projectNo` = %s
                """
                mycursor.executemany(update_query, batch)
                # logging.info(f"更新了 {len(batch)} 条数据")

        # 执行插入操作
        if insert_data:
            for i in range(0, len(insert_data), batch_size):
                batch = insert_data[i:i + batch_size]
                insert_query = """
                INSERT INTO zhongbiao (`publishDate`, `projectNo`, `customer`, `noticeType`, `title`, `productLabels`, `winnerAmount`, `remark`, `winnerPrincipal`)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                mycursor.executemany(insert_query, batch)
                # logging.info(f"插入了 {len(batch)} 条数据")

        # 提交事务
        connection.commit()
        if len(update_data) > 0 or len(insert_data) > 0:
             logging.info(f"{supName}成功提交事务，更新了 {len(update_data)} 条数据，插入了 {len(insert_data)} 条数据")
        
    except mysql.connector.Error as err:
        logging.error(f"数据库操作出错: {err}")
        connection.rollback()
        raise  # 重新抛出异常，让调用方知道发生了错误