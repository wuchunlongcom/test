#!/usr/bin/env python

import os
import django
import datetime
import xlrd


def getData(sql):
    import cx_Oracle
    db = cx_Oracle.connect("jw_user", "Hdlgdx18", "172.20.8.37:1521/orcl", encoding="UTF-8")
    cur = db.cursor()
    cur.execute(sql)
    result = cur.fetchall()
    ret = [[j or '' for j in i] for i in result]
    cur.close
    db.close()
    return ret


def readWorkbook(workbookPath, x=0, index=0):
    ''' 电子表格
        workbookPath: os.path.join(BASE_DIR, 'excel', 'classroom.xls')
        x: 从x行开始 0,1,2...
        index: 工作表序号
    '''

    workbook = xlrd.open_workbook(filename=workbookPath)
    sheet = workbook.sheet_by_index(index)

    myList = []
    for row_num in range(x, sheet.nrows):
        row = sheet.row(row_num)  # row -- [empty:'', empty:'', text:'HZ-616S', number:10000.0]
        v = [r.value.strip() for r in row]
        myList.append(v)

    return myList


def syncdb(classrooms, schedules):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "courseinfo.settings")
    django.setup()
    from django.contrib.auth.models import User, Group, Permission
    if not User.objects.filter(username='admin'):
        user = User.objects.create_superuser('admin', 'admin@test.com', 'admin')
        user.save()

    from classroom.models import Campus, Building, ClassroomType, Classroom, Teacher, Term, Course

    # Import classroom
    items = set(i[4] for i in classrooms) # 从classrooms中获得校区{'徐汇校区', '金山校区', '奉贤校区'}    
    # 下面两条语句，确保校区不会被重复写入到数据库Campus
    [i.delete() for i in Campus.objects.all() if i.name not in items] #  删除数据库Campus记录 （不是校区{'徐汇校区', '金山校区', '奉贤校区'}的记录） 
    items = items - set(Campus.objects.all().values_list('name', flat=True))  # items = {'a','b','c'} - set(['b','c']) --> {'a'}
    items = [Campus(name=i) for i in items]
    Campus.objects.bulk_create(items, batch_size=20)

    items = set(i[3] for i in classrooms)
    [i.delete() for i in ClassroomType.objects.all() if i.name not in items]
    items = items - set(ClassroomType.objects.all().values_list('name', flat=True))
    items = [ClassroomType(name=i) for i in items]
    ClassroomType.objects.bulk_create(items, batch_size=20)

    items = set((i[4], i[2]) for i in classrooms)
    [i.delete() for i in Building.objects.all() if (i.campus.name, i.name) not in items]
    items = items - set(Building.objects.all().values_list('campus__name', 'name'))
    items = [Building(campus=Campus.objects.get(name=k), name=v) for (k,v) in items]
    Building.objects.bulk_create(items, batch_size=20)

    items = {i[0]:i for i in classrooms} # {id:classrooms1,...}    classrooms1<=>classrooms第一条记录
    [i.delete() for i in Classroom.objects.all() if i.id not in items]
    items = {i:items[i] for i in set(items)-set(Classroom.objects.all().values_list('id', flat=True))} # {id1:classrooms1,...}  set({'a':1,'b':2,'c':3})={'c', 'b', 'a'} set使序列发生了变化
    items = [(v, Campus.objects.get(name=v[4])) for (k,v) in items.items()]  # [(v<=>classrooms1, campus1)...]
    items = [(i[0], Building.objects.get(campus=i[1], name=i[0][2])) for i in items] # [(i[0]<=>classrooms1, building1),...]
    items = [(i[0], i[1], ClassroomType.objects.get(name=i[0][3])) for i in items] # [(i[0]<=>classrooms1, building1, classroomType1),...]
    items = [Classroom(id=i[0][0], name=i[0][1], building=i[1], classroomType=i[2]) for i in items]
    Classroom.objects.bulk_create(items, batch_size=20)

    # Import schedule
    items = set((i[3], i[4]) for i in schedules)
    [i.delete() for i in Teacher.objects.all() if (i.id, i.name) not in items]
    items = items - set(Teacher.objects.all().values_list('id', 'name'))
    items = [Teacher(id=i[0], name=i[1]) for i in items]
    Teacher.objects.bulk_create(items, batch_size=20)

    items = set(i[1] for i in schedules)
    items = items - set(Term.objects.all().values_list('name', flat=True))
    today = datetime.date.today()
    items = [Term(name=i, firstMonday=today, start=today, end=today) for i in items]
    Term.objects.bulk_create(items, batch_size=20)


    [i.delete() for i in Course.objects.all()]
    items = [i for i in schedules if i[5].isdigit()]
    for i in range(len(items)):
        if items[i][12] and not items[i][13]:
            items[i][13] = items[i][12]
    items = [(
        i, Term.objects.get(name=i[1]), Teacher.objects.get(id=i[3]),
        Classroom.objects.get(id=i[8])) for i in items]
    items = [Course(
        courseid=i[0][0], term=i[1], name=i[0][2], teacher=i[2], CLASS_TIME=i[0][5],
        START_TIME=i[0][6], classroom=i[3], XQ=i[0][9], KS=i[0][10] or 0,
        JS=i[0][11] or 0, ZC1=i[0][12] or 0, ZC2=i[0][13] or 0,
        SJBZ=i[0][14] or 0, showtext=i[0][15] or 0) for i in items]
    Course.objects.bulk_create(items, batch_size=20)


def main():
    # import os
    # BASE_DIR = os.path.dirname(__file__)
    # classroomExcel = os.path.join(BASE_DIR, 'excel', 'classroom.xls')
    # classrooms = readWorkbook(classroomExcel)
    # scheduleExcel = os.path.join(BASE_DIR, 'excel', 'schedule.xls')
    # schedules = readWorkbook(scheduleExcel, x=1)

    classrooms = getData('select * from VIEW_DJZX_CLASSROOM')
    # print(type(classrooms[0]), classrooms[0:10])
    schedules = getData("select * from VIEW_DJZX_SCHEDULE where TERMNAME='2019-2020-1'")
       
    # print(type(schedules[0]), schedules[0:10])
    syncdb(classrooms, schedules)


if __name__ == "__main__":
    main()
