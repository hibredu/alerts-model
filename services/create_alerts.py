import pymysql
import datetime
import pandas
import pickle
import os


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


def basicQuery(queryString):
    with database.cursor() as cursor:
        cursor.execute(queryString)
        result = cursor.fetchall()
        cursor.close()
    database.commit()
    return result


def studentAverageByTopicSubject():
    query = "SELECT st.id, st.classrooms_id, sucl.teachers_id, sucl.school_subjects_id, ac.name,TRUNCATE(SUM(acst.grade) / COUNT(acst.grade), 2) FROM students st INNER JOIN activities_students acst ON (st.id = acst.students_id) INNER JOIN activities ac ON (acst.activities_id = ac.id) INNER JOIN subjects_classrooms sucl ON (ac.owner_id = sucl.id) GROUP BY st.id, sucl.teachers_id, sucl.school_subjects_id, ac.name"
    return basicQuery(query)


def studentAverageBySubject():
    query = "SELECT st.id, st.name, st.classrooms_id, sucl.teachers_id, sucl.school_subjects_id, TRUNCATE(SUM(acst.grade) / COUNT(acst.grade), 2) FROM students st INNER JOIN activities_students acst ON (st.id = acst.students_id) INNER JOIN activities ac ON (acst.activities_id = ac.id) INNER JOIN subjects_classrooms sucl ON (ac.owner_id = sucl.id) GROUP BY st.id, sucl.teachers_id, st.classrooms_id, sucl.school_subjects_id"
    return basicQuery(query)


def studentAverageBySubjectFilterDate(initial, final):
    query = "SELECT st.id, sucl.teachers_id, ss.name, TRUNCATE(SUM(acst.grade) / COUNT(acst.grade), 2) FROM students st INNER JOIN activities_students acst ON (st.id = acst.students_id) INNER JOIN activities ac ON (acst.activities_id = ac.id) INNER JOIN subjects_classrooms sucl ON (ac.owner_id = sucl.id) INNER JOIN school_subjects ss ON (sucl.school_subjects_id = ss.id) WHERE acst.created_at BETWEEN '" + initial + "' AND '" + final + "' GROUP BY st.id, sucl.teachers_id, st.classrooms_id, sucl.school_subjects_id, ss.name;"
    return basicQuery(query)


def classroomAverageBySubject():
    query = "SELECT sucl.classrooms_id, sucl.teachers_id, sucl.school_subjects_id, TRUNCATE(SUM(acst.grade) / COUNT(acst.grade), 2) FROM activities_students acst INNER JOIN activities ac ON (acst.activities_id = ac.id) INNER JOIN subjects_classrooms sucl ON (ac.owner_id = sucl.id) GROUP BY sucl.classrooms_id, sucl.school_subjects_id, sucl.teachers_id"
    return basicQuery(query)


def averageDataframe(averages):
    columns = ['Matemática', 'Física', 'Português', 'História', 'Música']
    dataframe = pandas.DataFrame([[None, None, None, None, None]], columns=columns)

    for column in columns:
        average = [average for _, _, subjectName, average in averages if subjectName == column]
        if len(average) == 1:
            averageETECFormat = 0
            if (average[0] <= 10 and average[0] >= 8):
                averageETECFormat = 3
            elif (average[0] < 8 and average[0] >= 7):
                averageETECFormat = 2
            elif (average[0] < 7 and average[0] >= 6):
                averageETECFormat = 1
            else:
                averageETECFormat = 0

            dataframe[column] = averageETECFormat

    return dataframe


def predictLowFinalYearAverage(averages):
    predictResult = None

    dataframe = averageDataframe(averages)

    if not dataframe.isnull().values.any():
        model = pickle.load(open(os.path.join(os.path.dirname(__file__), '../model/knn_model.pkl'), 'rb'))
        predictResult = model.predict(dataframe)

    return predictResult


def studentsLowFinalYearAverage():
    students = []

    lastSemester = str(datetime.datetime.now() - datetime.timedelta(weeks=24))
    today = str(datetime.datetime.now())

    averages = studentAverageBySubjectFilterDate(lastSemester, today)
    uniqueStudentIds = set(studentId for studentId, _, _, _ in averages)

    for uniqueStudentId in uniqueStudentIds:
        averagesStudent = []
        for average in averages:
            if (average[0] == uniqueStudentId):
                averagesStudent.append(average)
        predictResult = predictLowFinalYearAverage(averagesStudent)
        if predictResult == "RETIDO":
            uniqueTeacherIds = set(teacherId for studentId, teacherId, _, _ in averages if studentId == studentId)
            for uniqueTeacherId in uniqueTeacherIds:
                students.append((uniqueStudentId, uniqueTeacherId))

    return students


def studentLowAveragesBySubject():
    averages = []

    classroomAverages = classroomAverageBySubject()
    studentAverages = studentAverageBySubject()

    for studentAverage in studentAverages:
        classroomAverage = [classroomAverage for classroomId, _, subjectId, classroomAverage in classroomAverages if
                            studentAverage[2] == classroomId and studentAverage[4] == subjectId]
        if (len(classroomAverage) > 0 and studentAverage[5] < classroomAverage[0]):
            averages.append(studentAverage)

    return averages


def studentLowAveragesByTopicSubject():
    averages = []

    studentAverages = studentAverageBySubject()
    studentAveragesTopic = studentAverageByTopicSubject()

    for studentAverageTopic in studentAveragesTopic:
        studentAverage = [studentAverage for studentId, _, _, _, subjectId, studentAverage in studentAverages if
                          studentAverageTopic[0] == studentId and studentAverageTopic[3] == subjectId]
        if (len(studentAverage) > 0 and studentAverageTopic[5] < studentAverage[0]):
            averages.append(studentAverageTopic)

    return averages


def finalYearAverageAlerts():
    alerts = []

    averages = studentsLowFinalYearAverage()
    for average in averages:
        alerts.append({
            "value": "Tem chances de repetir de ano",
            "level": "yellow",
            "teachers_id": average[1],
            "students_id": average[0],
            "subjects_id": None
        })

    return alerts


def subjectAverageAlerts():
    alerts = []

    averages = studentLowAveragesBySubject()
    for average in averages:
        alerts.append({
            "value": "Está com a média baixa em relação a sala",
            "level": "red",
            "teachers_id": average[3],
            "students_id": average[0],
            "subjects_id": average[4]
        })

    return alerts


def topicSubjectAverageAlerts():
    alerts = []

    averages = studentLowAveragesByTopicSubject()
    for average in averages:
        alerts.append({
            "value": f"Está com dificuldades em {average[4]}",
            "level": "red",
            "teachers_id": average[2],
            "students_id": average[0],
            "subjects_id": average[3]
        })

    return alerts


def create_alerts():
    alerts = []

    try:
        alerts += finalYearAverageAlerts()
        alerts += subjectAverageAlerts()
        alerts += topicSubjectAverageAlerts()
    except Exception as e:
        print(e)

    return alerts
