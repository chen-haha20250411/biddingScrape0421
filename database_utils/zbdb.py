def process_and_insert_data(mycursor, data_all, batch_size=100):
    update_data = []
    insert_data = []

    for row in data_all[1:]:
        publish_date, project_no, customer, notice_type, title, product_labels, winner_amount, remark, winner_principal = row
        check_query = "SELECT * FROM zhongbiao WHERE `projectNo` = %s"
        mycursor.execute(check_query, (project_no,))
        existing_row = mycursor.fetchone()
        # 确保结果被完全读取
        mycursor.fetchall()  

        if existing_row:
            existing_amount = existing_row[6]
            if float(existing_amount) != float(winner_amount):
                update_data.append((publish_date, customer, notice_type, title, product_labels, winner_amount, remark, winner_principal, project_no))
        else:
            insert_data.append((publish_date, project_no, customer, notice_type, title, product_labels, winner_amount, remark, winner_principal))

    for i in range(0, len(update_data), batch_size):
        batch = update_data[i:i + batch_size]
        update_query = """
        UPDATE zhongbiao 
        SET `publishDate` = %s, `customer` = %s, `noticeType` = %s, `title` = %s, 
            `productLabels` = %s, `winnerAmount` = %s, `remark` = %s, `winnerPrincipal` = %s 
        WHERE `projectNo` = %s
        """
        try:
            mycursor.executemany(update_query, batch)
        except Exception as e:
            print(f"更新数据时出错: {e}")

    for i in range(0, len(insert_data), batch_size):
        batch = insert_data[i:i + batch_size]
        insert_query = """
        INSERT INTO zhongbiao (`publishDate`, `projectNo`, `customer`, `noticeType`, `title`, `productLabels`, `winnerAmount`, `remark`, `winnerPrincipal`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            mycursor.executemany(insert_query, batch)
        except Exception as e:
            print(f"插入数据时出错: {e}")

    