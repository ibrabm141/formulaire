import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password="""MysqL#Admin2025@""",
        database='survey_db'
    )
    print("اتصال ناجح!")
    conn.close()
except mysql.connector.Error as e:
    print("خطأ في الاتصال:", e)
