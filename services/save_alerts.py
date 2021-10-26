import pymysql


def getDatabase():
    try:
        return pymysql.connect(
            host="hibredu-database.cguowhbso4nk.us-east-2.rds.amazonaws.com",
            user="user_hibredu",
            password="hibredu_password_123",
            database="hibredu_db"
        )
    except pymysql.MySQLError as err:
        print(err)


database = getDatabase()


def alertExists(alert):
    query = "SELECT id FROM alerts WHERE value = %s AND level = %s AND teachers_id = %s AND students_id = %s AND subjects_id <=> %s"
    params = (alert['value'], alert['level'], alert['teachers_id'], alert['students_id'], alert['subjects_id'])
    cursor = database.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall()
    cursor.close()
    return len(result) > 0


def insertAlert(alert):
    query = "INSERT INTO alerts (value, level, teachers_id, students_id, subjects_id) VALUES (%s, %s, %s, %s, %s)"
    params = (alert['value'], alert['level'], alert['teachers_id'], alert['students_id'], alert['subjects_id'])
    cursor = database.cursor()
    cursor.execute(query, params)
    database.commit()
    cursor.close()


def save_alerts(alerts):
    for alert in alerts:
        if not alertExists(alert):
            insertAlert(alert)
