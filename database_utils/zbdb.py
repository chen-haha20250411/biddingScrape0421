import logging
from math import log
import mysql.connector

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_and_insert_fengniao_data(supName,connection, mycursor, data_all, batch_size=100):
    update_data = []
    insert_data = []
    
    for row in data_all[1:]:
        publish_date, project_no, customer, notice_type, title, product_labels, winner_amount, remark, winner_principal,html_url = row

        # 处理 projectNo 为空的情况
        if project_no == '' or project_no is None:
           continue   
        project_no_condition = "`projectNo` = %s"

        check_query = f"SELECT publishDate,projectNo, customer, winnerprincipal, noticeType FROM zhongbiao WHERE {project_no_condition}  and winnerPrincipal = %s "
        
        query_params = (project_no,winner_principal)

        try:
            mycursor.execute(check_query, query_params)
            existing_row = mycursor.fetchone()
            mycursor.fetchall()
        except mysql.connector.Error as err:
            logging.error(f"检查数据时出错: {err}")
            continue

        if existing_row:
            # logging.info(f"存在 日期：{publish_date},客户: {customer},  编号：{project_no},公告类型: {notice_type} ")
            exisit_publish_date = existing_row[0]
            exisit_customer = existing_row[2]
            exisit_winner_principal = existing_row[3]
            if   exisit_publish_date != publish_date and exisit_customer!= customer and exisit_winner_principal != winner_principal:
                update_data.append((publish_date, customer, notice_type, title, product_labels, winner_amount, remark, winner_principal, project_no,html_url))
        else:
            logging.info(f"风鸟网新增 供应商: {supName} , 日期：{publish_date},编号：{project_no}, 客户: {customer},公告类型: {notice_type} ")
            insert_data.append((publish_date, project_no, customer, notice_type, title, product_labels, winner_amount, remark, winner_principal,html_url))

    try:
        # 执行更新操作
        if update_data:
            for i in range(0, len(update_data), batch_size):
                batch = update_data[i:i + batch_size]
                update_query = """
                UPDATE zhongbiao 
                SET `publishDate` = %s, `customer` = %s, `noticeType` = %s, `title` = %s, 
                    `productLabels` = %s, `winnerAmount` = %s, `remark` = %s, `winnerPrincipal` = %s ,`html_url` = %s
                WHERE `projectNo` = %s
                """
                mycursor.executemany(update_query, batch)
                # logging.info(f"更新了 {len(batch)} 条数据")

        # 执行插入操作
        if insert_data:
            for i in range(0, len(insert_data), batch_size):
                batch = insert_data[i:i + batch_size]
                insert_query = """
                INSERT INTO zhongbiao (`publishDate`, `projectNo`, `customer`, `noticeType`, `title`, `productLabels`, `winnerAmount`, `remark`, `winnerPrincipal`,`is_del`,`html_url`)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,0,%s)
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

def process_and_insert_data(supName,connection, mycursor, data_all, batch_size=100):
    update_data = []
    insert_data = []
    
    for row in data_all[1:]:
        publish_date, project_no, customer, notice_type, title, product_labels, winner_amount, remark, winner_principal = row

        # 处理 projectNo 为空的情况
        if project_no == '' or project_no is None:
            project_no_condition = "(`projectNo` = '' OR `projectNo` IS NULL)"
        else:
            project_no_condition = "`projectNo` = %s"

        check_query = f"SELECT publishDate,projectNo, customer, winnerAmount, noticeType FROM zhongbiao WHERE {project_no_condition} and customer = %s and winnerAmount = %s and noticeType = %s and productLabels = %s"
        if project_no == ''or project_no is None:
            query_params = (customer, winner_amount, notice_type, product_labels)
        else:
            query_params = (project_no, customer, winner_amount, notice_type, product_labels)

        try:
            mycursor.execute(check_query, query_params)
            existing_row = mycursor.fetchone()
            mycursor.fetchall()
        except mysql.connector.Error as err:
            logging.error(f"检查数据时出错: {err}")
            continue

        if existing_row:
            # logging.info(f"存在 日期：{publish_date},客户: {customer},  中标金额: {winner_amount},公告类型: {notice_type} ")
            # logging.info(f"金额：{existing_row[2]},公告类型:{existing_row[3]}")
            exisit_publish_date = existing_row[0]
            exisit_customer = existing_row[2]
            existing_amount = existing_row[3]
            existing_notice_type = existing_row[4]
            if float(existing_amount) != float(winner_amount) and existing_notice_type != notice_type and exisit_publish_date != publish_date and exisit_customer!= customer:
                update_data.append((publish_date, customer, notice_type, title, product_labels, winner_amount, remark, winner_principal, project_no))
        else:
            logging.info(f"寻标网新增 日期：{publish_date},编号：{project_no}, 客户: {customer},  中标金额: {winner_amount},公告类型: {notice_type} ")
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
                INSERT INTO zhongbiao (`publishDate`, `projectNo`, `customer`, `noticeType`, `title`, `productLabels`, `winnerAmount`, `remark`, `winnerPrincipal`,`is_del`)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,1)
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
