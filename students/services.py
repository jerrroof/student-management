"""
核心功能服务层
包含：Excel导入导出、宿舍分配、自动分班、统计图表等
"""
import io
import pandas as pd
from datetime import datetime
from django.db import transaction
from django.db.models import Count, Sum, Q
from .models import (
    Student, Department, Major, StudentClass,
    DormitoryBuilding, DormitoryRoom,
    FeeItem, Payment, RegistrationTask, RegistrationRecord
)


# ==================== Excel 导入导出服务 ====================

class ExcelService:
    """Excel 导入导出服务"""
    
    @staticmethod
    def export_students_to_excel(queryset=None):
        """导出学生数据到Excel"""
        if queryset is None:
            queryset = Student.objects.select_related(
                'department', 'major', 'student_class', 'dormitory'
            ).all()
        
        data = []
        for student in queryset:
            data.append({
                '学号': student.student_id,
                '姓名': student.name,
                '性别': student.get_gender_display(),
                '身份证号': student.id_card,
                '出生日期': student.birthday.strftime('%Y-%m-%d') if student.birthday else '',
                '民族': student.ethnicity,
                '政治面貌': student.get_political_status_display(),
                '手机号': student.phone,
                '邮箱': student.email or '',
                'QQ': student.qq or '',
                '微信': student.wechat or '',
                '院系': student.department.name if student.department else '',
                '专业': student.major.name if student.major else '',
                '班级': student.student_class.name if student.student_class else '',
                '入学年份': student.enrollment_year,
                '准考证号': student.admission_ticket or '',
                '高考成绩': str(student.exam_score) if student.exam_score else '',
                '宿舍': str(student.dormitory) if student.dormitory else '',
                '床位号': student.bed_number or '',
                '状态': student.get_status_display(),
                '报到时间': student.registration_date.strftime('%Y-%m-%d %H:%M') if student.registration_date else '',
                '家庭地址': student.home_address or '',
                '紧急联系人': student.emergency_contact or '',
                '紧急联系人关系': student.emergency_relation or '',
                '紧急联系电话': student.emergency_phone or '',
            })
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='新生数据')
        output.seek(0)
        return output
    
    @staticmethod
    def get_import_template():
        """获取导入模板"""
        columns = [
            '学号', '姓名', '性别', '身份证号', '出生日期', '民族', '政治面貌',
            '手机号', '邮箱', '院系代码', '专业代码', '入学年份',
            '准考证号', '高考成绩', '家庭地址', '紧急联系人', '紧急联系人关系', '紧急联系电话'
        ]
        df = pd.DataFrame(columns=columns)
        # 添加示例数据
        df.loc[0] = [
            '2026001001', '张三', '男', '110101200601011234', '2006-01-01', '汉族', '共青团员',
            '13800138000', 'zhangsan@example.com', 'CS', 'CS001', 2026,
            '26110100001', '650', '北京市朝阳区xxx街道', '张父', '父亲', '13900139000'
        ]
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='新生导入模板')
        output.seek(0)
        return output
    
    @staticmethod
    @transaction.atomic
    def import_students_from_excel(file):
        """从Excel导入学生数据"""
        df = pd.read_excel(file, engine='openpyxl')
        
        # 性别映射
        gender_map = {'男': 'M', '女': 'F'}
        # 政治面貌映射
        political_map = {
            '群众': 'masses', '共青团员': 'league', 
            '中共党员': 'party', '中共预备党员': 'prep',
            '民主党派': 'democratic'
        }
        
        success_count = 0
        error_list = []
        imported_ids = []  # 记录新导入的学生ID
        
        for idx, row in df.iterrows():
            try:
                # 检查必填字段
                student_id = str(row.get('学号', '')).strip()
                name = str(row.get('姓名', '')).strip()
                id_card = str(row.get('身份证号', '')).strip()
                phone = str(row.get('手机号', '')).strip()
                
                if not all([student_id, name, id_card, phone]):
                    error_list.append(f"第{idx+2}行: 缺少必填字段")
                    continue
                
                # 检查是否已存在
                if Student.objects.filter(Q(student_id=student_id) | Q(id_card=id_card)).exists():
                    error_list.append(f"第{idx+2}行: 学号或身份证号已存在")
                    continue
                
                # 获取外键对象
                department = None
                major = None
                dept_code = str(row.get('院系代码', '')).strip()
                major_code = str(row.get('专业代码', '')).strip()
                
                if dept_code:
                    department = Department.objects.filter(code=dept_code).first()
                if major_code:
                    major = Major.objects.filter(code=major_code).first()
                
                # 处理出生日期
                birthday = None
                birthday_val = row.get('出生日期')
                if pd.notna(birthday_val):
                    if isinstance(birthday_val, str):
                        birthday = datetime.strptime(birthday_val, '%Y-%m-%d').date()
                    else:
                        birthday = birthday_val.date() if hasattr(birthday_val, 'date') else birthday_val
                
                # 创建学生记录
                student = Student.objects.create(
                    student_id=student_id,
                    name=name,
                    gender=gender_map.get(str(row.get('性别', '男')), 'M'),
                    id_card=id_card,
                    birthday=birthday,
                    ethnicity=str(row.get('民族', '汉族')) or '汉族',
                    political_status=political_map.get(str(row.get('政治面貌', '群众')), 'masses'),
                    phone=phone,
                    email=str(row.get('邮箱', '')) if pd.notna(row.get('邮箱')) else '',
                    department=department,
                    major=major,
                    enrollment_year=int(row.get('入学年份', datetime.now().year)),
                    admission_ticket=str(row.get('准考证号', '')) if pd.notna(row.get('准考证号')) else '',
                    exam_score=float(row.get('高考成绩')) if pd.notna(row.get('高考成绩')) else None,
                    home_address=str(row.get('家庭地址', '')) if pd.notna(row.get('家庭地址')) else '',
                    emergency_contact=str(row.get('紧急联系人', '')) if pd.notna(row.get('紧急联系人')) else '',
                    emergency_relation=str(row.get('紧急联系人关系', '')) if pd.notna(row.get('紧急联系人关系')) else '',
                    emergency_phone=str(row.get('紧急联系电话', '')) if pd.notna(row.get('紧急联系电话')) else '',
                    status='admitted'
                )
                imported_ids.append(student.id)
                success_count += 1
                
            except Exception as e:
                error_list.append(f"第{idx+2}行: {str(e)}")
        
        return {
            'success_count': success_count,
            'error_count': len(error_list),
            'errors': error_list,
            'imported_ids': imported_ids
        }


# ==================== 宿舍分配服务 ====================

class DormitoryService:
    """宿舍分配服务"""
    
    @staticmethod
    def get_available_rooms(gender=None, building_id=None):
        """获取可用房间列表"""
        rooms = DormitoryRoom.objects.filter(is_active=True).select_related('building')
        
        if building_id:
            rooms = rooms.filter(building_id=building_id)
        
        if gender:
            # 根据性别筛选宿舍楼类型
            gender_type_map = {'M': 'M', 'F': 'F'}
            rooms = rooms.filter(
                Q(building__gender_type=gender_type_map.get(gender)) | 
                Q(building__gender_type='X')  # 混合宿舍
            )
        
        # 过滤出有空余床位的房间
        available = []
        for room in rooms:
            if room.available_beds > 0:
                available.append({
                    'room': room,
                    'available_beds': room.available_beds,
                    'building_name': room.building.name,
                    'room_number': room.room_number
                })
        
        return available
    
    @staticmethod
    @transaction.atomic
    def auto_assign_dormitory(student_ids=None, strategy='sequential'):
        """
        自动分配宿舍
        strategy: 
            - sequential: 顺序分配（填满一个再下一个）
            - balanced: 均衡分配（尽量每个房间人数均衡）
            - by_class: 按班级分配（同班同学尽量在一起）
        """
        # 获取待分配的学生
        if student_ids:
            students = Student.objects.filter(
                id__in=student_ids,
                dormitory__isnull=True
            ).select_related('department', 'major', 'student_class')
        else:
            students = Student.objects.filter(
                dormitory__isnull=True,
                status__in=['admitted', 'pending', 'registered']
            ).select_related('department', 'major', 'student_class')
        
        # 按性别分组
        male_students = list(students.filter(gender='M'))
        female_students = list(students.filter(gender='F'))
        
        assigned_count = 0
        failed_list = []
        assigned_ids = []  # 记录成功分配的学生ID
        
        # 分配男生宿舍
        assigned, failed, ids = DormitoryService._assign_students_to_rooms(
            male_students, 'M', strategy
        )
        assigned_count += assigned
        failed_list.extend(failed)
        assigned_ids.extend(ids)
        
        # 分配女生宿舍
        assigned, failed, ids = DormitoryService._assign_students_to_rooms(
            female_students, 'F', strategy
        )
        assigned_count += assigned
        failed_list.extend(failed)
        assigned_ids.extend(ids)
        
        return {
            'assigned_count': assigned_count,
            'failed_count': len(failed_list),
            'failed_students': failed_list,
            'assigned_ids': assigned_ids
        }
    
    @staticmethod
    def _assign_students_to_rooms(students, gender, strategy):
        """执行实际的分配逻辑"""
        if not students:
            return 0, [], []
        
        # 获取可用房间
        rooms = DormitoryRoom.objects.filter(
            is_active=True
        ).filter(
            Q(building__gender_type=gender) | Q(building__gender_type='X')
        ).select_related('building').order_by('building__code', 'floor', 'room_number')
        
        assigned_count = 0
        failed_list = []
        assigned_ids = []  # 记录成功分配的学生ID
        
        if strategy == 'by_class':
            # 按班级分组
            from collections import defaultdict
            class_groups = defaultdict(list)
            for student in students:
                class_key = student.student_class_id or 0
                class_groups[class_key].append(student)
            
            # 按班级顺序分配
            students = []
            for class_id in sorted(class_groups.keys()):
                students.extend(class_groups[class_id])
        
        # 顺序分配
        room_idx = 0
        room_list = list(rooms)
        
        for student in students:
            assigned = False
            
            # 从当前索引开始查找可用房间
            for i in range(len(room_list)):
                idx = (room_idx + i) % len(room_list)
                room = room_list[idx]
                
                if room.available_beds > 0:
                    # 分配床位
                    bed_number = room.current_occupancy + 1
                    student.dormitory = room
                    student.bed_number = str(bed_number)
                    student.save(update_fields=['dormitory', 'bed_number'])
                    
                    assigned_count += 1
                    assigned_ids.append(student.id)  # 记录分配成功的学生ID
                    assigned = True
                    
                    if strategy == 'sequential':
                        room_idx = idx  # 继续从当前房间分配
                    else:
                        room_idx = (idx + 1) % len(room_list)  # 下一个房间
                    
                    break
            
            if not assigned:
                failed_list.append(student.name)
        
        return assigned_count, failed_list, assigned_ids


# ==================== 分班服务 ====================

class ClassAssignmentService:
    """分班服务"""
    
    @staticmethod
    @transaction.atomic
    def auto_assign_class(major_id=None, enrollment_year=None, class_size=30, strategy='balanced'):
        """
        自动分班
        strategy:
            - balanced: 均衡分配（按成绩均匀分布）
            - sequential: 顺序分配
            - random: 随机分配
        """
        # 获取待分班的学生
        students = Student.objects.filter(
            student_class__isnull=True,
            status__in=['admitted', 'pending', 'registered']
        )
        
        if major_id:
            students = students.filter(major_id=major_id)
        if enrollment_year:
            students = students.filter(enrollment_year=enrollment_year)
        
        students = list(students.select_related('major'))
        
        if not students:
            return {'assigned_count': 0, 'classes_created': 0, 'message': '没有待分班的学生'}
        
        # 按专业分组
        from collections import defaultdict
        major_groups = defaultdict(list)
        for student in students:
            major_key = student.major_id or 0
            major_groups[major_key].append(student)
        
        total_assigned = 0
        classes_created = 0
        
        for major_id, major_students in major_groups.items():
            if not major_id:
                continue
            
            major = Major.objects.filter(id=major_id).first()
            if not major:
                continue
            
            # 根据策略排序学生
            if strategy == 'balanced':
                # 按成绩排序，然后蛇形分配
                major_students.sort(key=lambda s: s.exam_score or 0, reverse=True)
            elif strategy == 'random':
                import random
                random.shuffle(major_students)
            
            # 计算需要创建的班级数
            year = enrollment_year or datetime.now().year
            num_classes = (len(major_students) + class_size - 1) // class_size
            
            # 获取已有班级的最大编号
            existing_classes = StudentClass.objects.filter(
                major=major,
                enrollment_year=year
            ).count()
            
            # 创建班级
            classes = []
            for i in range(num_classes):
                class_num = existing_classes + i + 1
                class_code = f"{major.code}{year}{class_num:02d}"
                class_name = f"{major.name}{class_num}班"
                
                student_class, created = StudentClass.objects.get_or_create(
                    code=class_code,
                    defaults={
                        'name': class_name,
                        'major': major,
                        'enrollment_year': year,
                    }
                )
                classes.append(student_class)
                if created:
                    classes_created += 1
            
            # 分配学生到班级
            if strategy == 'balanced':
                # 蛇形分配（成绩均衡）
                for idx, student in enumerate(major_students):
                    cycle = idx // len(classes)
                    if cycle % 2 == 0:
                        class_idx = idx % len(classes)
                    else:
                        class_idx = len(classes) - 1 - (idx % len(classes))
                    
                    student.student_class = classes[class_idx]
                    student.save(update_fields=['student_class'])
                    total_assigned += 1
            else:
                # 顺序/随机分配
                for idx, student in enumerate(major_students):
                    class_idx = idx // class_size
                    if class_idx < len(classes):
                        student.student_class = classes[class_idx]
                        student.save(update_fields=['student_class'])
                        total_assigned += 1
        
        return {
            'assigned_count': total_assigned,
            'classes_created': classes_created,
            'message': f'成功分配 {total_assigned} 名学生到 {classes_created} 个新班级'
        }


# ==================== 报到服务 ====================

class RegistrationService:
    """报到管理服务"""
    
    @staticmethod
    def get_student_by_id_or_card(identifier):
        """通过学号或身份证号查询学生"""
        return Student.objects.filter(
            Q(student_id=identifier) | Q(id_card=identifier)
        ).select_related('department', 'major', 'student_class', 'dormitory').first()
    
    @staticmethod
    def get_registration_progress(student):
        """获取学生报到进度"""
        tasks = RegistrationTask.objects.filter(is_active=True).order_by('order')
        
        records = {
            r.task_id: r for r in 
            RegistrationRecord.objects.filter(student=student)
        }
        
        progress = []
        completed_count = 0
        
        for task in tasks:
            record = records.get(task.id)
            status = record.status if record else 'pending'
            
            if status == 'completed':
                completed_count += 1
            
            progress.append({
                'task': task,
                'record': record,
                'status': status,
                'is_completed': status == 'completed'
            })
        
        total_required = tasks.filter(is_required=True).count()
        completed_required = RegistrationRecord.objects.filter(
            student=student,
            task__is_required=True,
            status='completed'
        ).count()
        
        # 计算完成率（基于必需任务）
        completion_rate = min(round(completed_required / total_required * 100, 1), 100) if total_required > 0 else 0
        
        return {
            'progress': progress,
            'completed_count': completed_count,
            'total_count': tasks.count(),
            'completion_rate': completion_rate,
            'all_required_completed': completed_required >= total_required
        }
    
    @staticmethod
    @transaction.atomic
    def complete_task(student, task_id, operator=''):
        """完成报到环节"""
        from django.utils import timezone
        
        task = RegistrationTask.objects.get(id=task_id)
        
        record, created = RegistrationRecord.objects.get_or_create(
            student=student,
            task=task,
            defaults={
                'status': 'completed',
                'completed_at': timezone.now(),
                'operator': operator
            }
        )
        
        if not created and record.status != 'completed':
            record.status = 'completed'
            record.completed_at = timezone.now()
            record.operator = operator
            record.save()
        
        # 检查是否所有必须环节都已完成
        progress = RegistrationService.get_registration_progress(student)
        
        if progress['all_required_completed']:
            # 更新学生状态
            if student.status in ['admitted', 'pending']:
                student.status = 'registered'
                student.registration_date = timezone.now()
                student.save(update_fields=['status', 'registration_date'])
        
        return record
    
    @staticmethod
    @transaction.atomic
    def quick_register(student, operator=''):
        """快速报到（一键完成所有环节）"""
        from django.utils import timezone
        
        tasks = RegistrationTask.objects.filter(is_active=True)
        
        for task in tasks:
            RegistrationRecord.objects.update_or_create(
                student=student,
                task=task,
                defaults={
                    'status': 'completed',
                    'completed_at': timezone.now(),
                    'operator': operator
                }
            )
        
        # 更新学生状态
        student.status = 'registered'
        student.registration_date = timezone.now()
        student.save(update_fields=['status', 'registration_date'])
        
        return True


# ==================== 统计图表服务 ====================

class ChartService:
    """统计图表服务（使用 pyecharts）"""
    
    @staticmethod
    def get_gender_pie_chart():
        """性别分布饼图"""
        from pyecharts.charts import Pie
        from pyecharts import options as opts
        
        male_count = Student.objects.filter(gender='M').count()
        female_count = Student.objects.filter(gender='F').count()
        
        data = [('男生', male_count), ('女生', female_count)]
        
        # 处理空数据
        if male_count == 0 and female_count == 0:
            data = [('暂无数据', 0)]
        
        pie = (
            Pie()
            .add(
                "",
                data,
                radius=["40%", "70%"],
                label_opts=opts.LabelOpts(formatter="{b}: {c} ({d}%)")
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="性别分布"),
                legend_opts=opts.LegendOpts(pos_left="left", orient="vertical")
            )
            .set_colors(["#3498db", "#e74c3c"])
        )
        
        return pie.render_embed()
    
    @staticmethod
    def get_department_bar_chart():
        """院系人数柱状图"""
        from pyecharts.charts import Bar
        from pyecharts import options as opts
        
        stats = Student.objects.filter(
            department__isnull=False
        ).values('department__name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        departments = [s['department__name'] for s in stats]
        counts = [s['count'] for s in stats]
        
        # 处理空数据
        if not departments:
            departments = ['暂无数据']
            counts = [0]
        
        bar = (
            Bar()
            .add_xaxis(departments)
            .add_yaxis("人数", counts, color="#3498db")
            .set_global_opts(
                title_opts=opts.TitleOpts(title="各院系新生人数 (Top 10)"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45)),
                datazoom_opts=[opts.DataZoomOpts()]
            )
        )
        
        return bar.render_embed()
    
    @staticmethod
    def get_status_pie_chart():
        """报到状态分布图"""
        from pyecharts.charts import Pie
        from pyecharts import options as opts
        
        status_map = {
            'admitted': '已录取',
            'pending': '待报到',
            'registered': '已报到',
            'completed': '已完成',
            'deferred': '保留学籍',
            'cancelled': '取消入学'
        }
        
        stats = Student.objects.values('status').annotate(count=Count('id'))
        data = [(status_map.get(s['status'], s['status']), s['count']) for s in stats]
        
        # 处理空数据
        if not data:
            data = [('暂无数据', 0)]
        
        pie = (
            Pie()
            .add(
                "",
                data,
                radius=["30%", "60%"],
                rosetype="radius",
                label_opts=opts.LabelOpts(formatter="{b}: {c}")
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="报到状态分布"),
                legend_opts=opts.LegendOpts(pos_right="right", orient="vertical")
            )
        )
        
        return pie.render_embed()
    
    @staticmethod
    def get_registration_trend_chart():
        """报到趋势图（按日期统计）"""
        from pyecharts.charts import Line
        from pyecharts import options as opts
        from django.db.models.functions import TruncDate
        
        stats = Student.objects.filter(
            registration_date__isnull=False
        ).annotate(
            date=TruncDate('registration_date')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        dates = [s['date'].strftime('%m-%d') for s in stats]
        counts = [s['count'] for s in stats]
        
        # 处理空数据
        if not dates:
            dates = ['暂无数据']
            counts = [0]
        
        # 累计人数
        cumulative = []
        total = 0
        for c in counts:
            total += c
            cumulative.append(total)
        
        line = (
            Line()
            .add_xaxis(dates)
            .add_yaxis("当日报到", counts, is_smooth=True, color="#3498db")
            .add_yaxis("累计报到", cumulative, is_smooth=True, color="#2ecc71")
            .set_global_opts(
                title_opts=opts.TitleOpts(title="报到趋势"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45)),
                datazoom_opts=[opts.DataZoomOpts(type_="inside")]
            )
        )
        
        return line.render_embed()
    
    @staticmethod
    def get_dormitory_occupancy_chart():
        """宿舍入住率图"""
        from pyecharts.charts import Bar
        from pyecharts import options as opts
        
        buildings = DormitoryBuilding.objects.filter(is_active=True)
        
        names = []
        total_beds = []
        occupied_beds = []
        
        for building in buildings:
            names.append(building.name)
            total_beds.append(building.total_beds)
            occupied_beds.append(building.occupied_beds)
        
        # 处理空数据
        if not names:
            names = ['暂无数据']
            total_beds = [0]
            occupied_beds = [0]
        
        bar = (
            Bar()
            .add_xaxis(names)
            .add_yaxis("总床位", total_beds, color="#95a5a6")
            .add_yaxis("已入住", occupied_beds, color="#3498db")
            .set_global_opts(
                title_opts=opts.TitleOpts(title="各宿舍楼入住情况"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45)),
                datazoom_opts=[opts.DataZoomOpts()]
            )
        )
        
        return bar.render_embed()
    
    @staticmethod
    def get_payment_stats_chart():
        """缴费统计图"""
        from pyecharts.charts import Gauge
        from pyecharts import options as opts
        
        total_fee = FeeItem.objects.aggregate(total=Sum('amount'))['total'] or 0
        paid_amount = Payment.objects.filter(status='confirmed').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        rate = round(paid_amount / total_fee * 100, 1) if total_fee > 0 else 0
        
        gauge = (
            Gauge()
            .add(
                "缴费率",
                [("缴费完成率", rate)],
                radius="80%",
                detail_label_opts=opts.LabelOpts(formatter="{value}%", font_size=25)
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="缴费完成率")
            )
        )
        
        return gauge.render_embed()
