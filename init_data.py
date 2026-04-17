"""
初始化数据脚本
运行: python manage.py shell < init_data.py
或者在 Django shell 中执行
"""
from students.models import (
    Department, Major, RegistrationTask, DormitoryBuilding, DormitoryRoom
)

# 创建报到环节
registration_tasks = [
    {'code': 'T01', 'name': '身份核验', 'order': 1, 'is_required': True, 'location': '报到大厅', 'description': '核验身份证、录取通知书'},
    {'code': 'T02', 'name': '缴费确认', 'order': 2, 'is_required': True, 'location': '财务处', 'description': '确认学费、住宿费已缴纳'},
    {'code': 'T03', 'name': '领取校园卡', 'order': 3, 'is_required': True, 'location': '一卡通中心', 'description': '领取校园一卡通'},
    {'code': 'T04', 'name': '宿舍入住', 'order': 4, 'is_required': True, 'location': '宿舍管理中心', 'description': '领取钥匙、入住宿舍'},
    {'code': 'T05', 'name': '领取军训服', 'order': 5, 'is_required': False, 'location': '体育馆', 'description': '领取军训服装'},
    {'code': 'T06', 'name': '体检', 'order': 6, 'is_required': True, 'location': '校医院', 'description': '入学体检'},
    {'code': 'T07', 'name': '班级报到', 'order': 7, 'is_required': True, 'location': '各学院', 'description': '到所在班级辅导员处报到'},
]

for task_data in registration_tasks:
    RegistrationTask.objects.get_or_create(
        code=task_data['code'],
        defaults=task_data
    )
print(f"创建了 {len(registration_tasks)} 个报到环节")

# 创建院系
departments = [
    {'code': 'CS', 'name': '计算机科学与技术学院'},
    {'code': 'EE', 'name': '电子信息工程学院'},
    {'code': 'ME', 'name': '机械工程学院'},
    {'code': 'MA', 'name': '数学与统计学院'},
    {'code': 'EC', 'name': '经济管理学院'},
]

for dept_data in departments:
    dept, created = Department.objects.get_or_create(
        code=dept_data['code'],
        defaults=dept_data
    )
    if created:
        print(f"创建院系: {dept.name}")

# 创建专业
majors = [
    {'code': 'CS001', 'name': '计算机科学与技术', 'department_code': 'CS', 'duration': 4, 'tuition_fee': 5500},
    {'code': 'CS002', 'name': '软件工程', 'department_code': 'CS', 'duration': 4, 'tuition_fee': 5500},
    {'code': 'CS003', 'name': '人工智能', 'department_code': 'CS', 'duration': 4, 'tuition_fee': 6000},
    {'code': 'EE001', 'name': '电子信息工程', 'department_code': 'EE', 'duration': 4, 'tuition_fee': 5500},
    {'code': 'EE002', 'name': '通信工程', 'department_code': 'EE', 'duration': 4, 'tuition_fee': 5500},
    {'code': 'ME001', 'name': '机械工程', 'department_code': 'ME', 'duration': 4, 'tuition_fee': 5000},
    {'code': 'MA001', 'name': '数学与应用数学', 'department_code': 'MA', 'duration': 4, 'tuition_fee': 4500},
    {'code': 'EC001', 'name': '工商管理', 'department_code': 'EC', 'duration': 4, 'tuition_fee': 5000},
]

for major_data in majors:
    dept = Department.objects.filter(code=major_data.pop('department_code')).first()
    if dept:
        major_data['department'] = dept
        Major.objects.get_or_create(
            code=major_data['code'],
            defaults=major_data
        )
print(f"创建了 {len(majors)} 个专业")

# 创建宿舍楼
buildings = [
    {'code': 'M1', 'name': '男生1号楼', 'gender_type': 'M', 'floors': 6},
    {'code': 'M2', 'name': '男生2号楼', 'gender_type': 'M', 'floors': 6},
    {'code': 'F1', 'name': '女生1号楼', 'gender_type': 'F', 'floors': 6},
    {'code': 'F2', 'name': '女生2号楼', 'gender_type': 'F', 'floors': 6},
]

for building_data in buildings:
    floors = building_data['floors']
    building, created = DormitoryBuilding.objects.get_or_create(
        code=building_data['code'],
        defaults=building_data
    )
    if created:
        print(f"创建宿舍楼: {building.name}")
        # 为每个宿舍楼创建房间
        for floor in range(1, floors + 1):
            for room_num in range(1, 11):  # 每层10个房间
                room_number = f"{floor}{room_num:02d}"
                DormitoryRoom.objects.get_or_create(
                    building=building,
                    room_number=room_number,
                    defaults={
                        'floor': floor,
                        'capacity': 4,
                        'fee_per_year': 1200
                    }
                )
        print(f"  - 创建了 {floors * 10} 个房间")

print("\n初始化数据完成！")
