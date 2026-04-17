from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count, F
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
import json
from .models import (
    Student, Department, Major, StudentClass,
    DormitoryBuilding, DormitoryRoom,
    FeeItem, Payment, RegistrationTask, RegistrationRecord,
    DocumentType, StudentDocument, Announcement
)
from .services import (
    ExcelService, DormitoryService, ClassAssignmentService,
    RegistrationService, ChartService
)


def home(request):
    """首页 - 数据概览"""
    # 基本统计
    total_students = Student.objects.count()
    pending_count = Student.objects.filter(status='pending').count()
    admitted_count = Student.objects.filter(status='admitted').count()
    registered_count = Student.objects.filter(status='registered').count()
    completed_count = Student.objects.filter(status='completed').count()
    
    # 缴费统计
    total_tuition = FeeItem.objects.aggregate(total=Sum('amount'))['total'] or 0
    paid_tuition = Payment.objects.filter(status='confirmed').aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'total_students': total_students,
        'pending_count': pending_count,
        'admitted_count': admitted_count,
        'registered_count': registered_count,
        'completed_count': completed_count,
        'total_tuition': total_tuition,
        'paid_tuition': paid_tuition,
        'recent_students': Student.objects.select_related('department', 'major').all()[:10],
    }
    return render(request, 'students/home.html', context)


def student_list(request):
    """新生列表"""
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    department_id = request.GET.get('department', '')
    
    students = Student.objects.select_related('department', 'major', 'student_class', 'dormitory').all()
    
    if query:
        students = students.filter(
            Q(student_id__icontains=query) |
            Q(name__icontains=query) |
            Q(phone__icontains=query)
        )
    
    if status:
        students = students.filter(status=status)
    
    if department_id:
        students = students.filter(department_id=department_id)
    
    # 分页
    paginator = Paginator(students, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 获取所有院系用于筛选
    departments = Department.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'status': status,
        'department_id': department_id,
        'departments': departments,
    }
    return render(request, 'students/student_list.html', context)


def student_detail(request, pk):
    """新生详情"""
    student = get_object_or_404(
        Student.objects.select_related('department', 'major', 'student_class', 'dormitory'),
        pk=pk
    )
    # 获取缴费记录
    fee_items = student.fee_items.all()
    payments = student.payments.all()
    # 获取报到记录
    registration_records = student.registration_records.select_related('task').all()
    # 获取材料提交记录
    documents = student.documents.select_related('document_type').all()
    
    context = {
        'student': student,
        'fee_items': fee_items,
        'payments': payments,
        'registration_records': registration_records,
        'documents': documents,
    }
    return render(request, 'students/student_detail.html', context)


def dormitory_list(request):
    """宿舍列表"""
    # 获取所有宿舍楼
    buildings = DormitoryBuilding.objects.filter(is_active=True).prefetch_related('rooms')
    
    # 获取所有房间
    rooms = DormitoryRoom.objects.filter(is_active=True).select_related('building')
    
    # 统计信息
    total_buildings = buildings.count()
    total_rooms = rooms.count()
    total_capacity = sum(room.capacity for room in rooms)
    total_occupied = sum(room.current_occupancy for room in rooms)
    
    context = {
        'buildings': buildings,
        'rooms': rooms,
        'total_buildings': total_buildings,
        'total_rooms': total_rooms,
        'total_capacity': total_capacity,
        'total_occupied': total_occupied,
        'available_beds': total_capacity - total_occupied,
    }
    return render(request, 'students/dormitory_list.html', context)


def statistics(request):
    """统计报表"""
    # 性别统计
    gender_stats = {
        'male': Student.objects.filter(gender='M').count(),
        'female': Student.objects.filter(gender='F').count(),
    }
    
    # 院系统计
    department_stats = Student.objects.filter(
        department__isnull=False
    ).values(
        'department__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    # 状态统计
    status_stats = {
        'admitted': Student.objects.filter(status='admitted').count(),
        'pending': Student.objects.filter(status='pending').count(),
        'registered': Student.objects.filter(status='registered').count(),
        'completed': Student.objects.filter(status='completed').count(),
    }
    
    # 缴费统计
    total_fee = FeeItem.objects.aggregate(total=Sum('amount'))['total'] or 0
    paid_amount = Payment.objects.filter(status='confirmed').aggregate(total=Sum('amount'))['total'] or 0
    
    # 统计未缴清学生数
    students_with_fee = Student.objects.filter(fee_items__isnull=False).distinct()
    unpaid_students = sum(1 for s in students_with_fee if not s.is_paid)
    
    payment_stats = {
        'total': total_fee,
        'paid': paid_amount,
        'unpaid_students': unpaid_students,
    }
    
    context = {
        'gender_stats': gender_stats,
        'department_stats': department_stats,
        'status_stats': status_stats,
        'payment_stats': payment_stats,
    }
    return render(request, 'students/statistics.html', context)


# ==================== Excel 导入导出 ====================

def export_students(request):
    """导出学生数据到 Excel"""
    # 获取筛选条件
    status = request.GET.get('status', '')
    department_id = request.GET.get('department', '')
    
    queryset = Student.objects.select_related('department', 'major', 'student_class', 'dormitory')
    
    if status:
        queryset = queryset.filter(status=status)
    if department_id:
        queryset = queryset.filter(department_id=department_id)
    
    # 生成 Excel
    output = ExcelService.export_students_to_excel(queryset)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="students_export.xlsx"'
    return response


def download_import_template(request):
    """下载导入模板"""
    output = ExcelService.get_import_template()
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="import_template.xlsx"'
    return response


def import_students(request):
    """导入学生数据页面"""
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            messages.error(request, '请选择要导入的文件')
            return redirect('students:import_students')
        
        if not file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, '请上传 Excel 文件 (.xlsx 或 .xls)')
            return redirect('students:import_students')
        
        result = ExcelService.import_students_from_excel(file)
        
        # 导入成功，跳转到成功页面
        if result['success_count'] > 0:
            # 获取新导入的学生信息
            imported_students = Student.objects.filter(
                id__in=result['imported_ids']
            ).select_related('department', 'major').order_by('student_id')
            
            return render(request, 'students/import_success.html', {
                'success_count': result['success_count'],
                'error_count': result['error_count'],
                'errors': result['errors'][:10],  # 最多显示10条错误
                'students': imported_students,
            })
        
        # 全部失败
        if result['errors']:
            error_msg = '<br>'.join(result['errors'][:10])
            if len(result['errors']) > 10:
                error_msg += f'<br>... 共 {len(result["errors"])} 条错误'
            messages.error(request, f"导入失败: {error_msg}")
        
        return redirect('students:import_students')
    
    return render(request, 'students/import_students.html')


# ==================== 报到管理 ====================

def registration(request):
    """报到管理页面"""
    student = None
    progress = None
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'search':
            # 查询学生
            identifier = request.POST.get('identifier', '').strip()
            if identifier:
                student = RegistrationService.get_student_by_id_or_card(identifier)
                if student:
                    progress = RegistrationService.get_registration_progress(student)
                else:
                    messages.warning(request, '未找到该学生')
        
        elif action == 'complete_task':
            # 完成某个环节
            student_id = request.POST.get('student_id')
            task_id = request.POST.get('task_id')
            student = Student.objects.get(id=student_id)
            RegistrationService.complete_task(student, task_id, request.user.username if request.user.is_authenticated else '')
            progress = RegistrationService.get_registration_progress(student)
            messages.success(request, '报到环节已完成')
        
        elif action == 'quick_register':
            # 快速报到
            student_id = request.POST.get('student_id')
            student = Student.objects.get(id=student_id)
            RegistrationService.quick_register(student, request.user.username if request.user.is_authenticated else '')
            progress = RegistrationService.get_registration_progress(student)
            messages.success(request, '快速报到已完成')
    
    # 统计信息
    stats = {
        'total': Student.objects.count(),
        'registered': Student.objects.filter(status__in=['registered', 'completed']).count(),
        'pending': Student.objects.filter(status__in=['admitted', 'pending']).count(),
    }
    
    context = {
        'student': student,
        'progress': progress,
        'stats': stats,
    }
    return render(request, 'students/registration.html', context)


# ==================== 宿舍分配 ====================

def dormitory_assignment(request):
    """宿舍分配页面"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'auto_assign':
            strategy = request.POST.get('strategy', 'sequential')
            result = DormitoryService.auto_assign_dormitory(strategy=strategy)
            
            # 分配成功，跳转到成功页面
            if result['assigned_count'] > 0:
                # 获取新分配的学生信息
                assigned_students = Student.objects.filter(
                    id__in=result['assigned_ids']
                ).select_related('department', 'major', 'dormitory', 'dormitory__building').order_by('dormitory__building__name', 'dormitory__room_number', 'bed_number')
                
                return render(request, 'students/dormitory_assignment_success.html', {
                    'assigned_count': result['assigned_count'],
                    'failed_count': result['failed_count'],
                    'failed_students': result['failed_students'],
                    'students': assigned_students,
                    'strategy': strategy,
                })
            
            # 全部失败
            if result['failed_students']:
                messages.error(
                    request,
                    f"分配失败：{result['failed_count']} 名学生无法分配（床位不足）"
                )
            else:
                messages.info(request, "没有需要分配的学生")
    
    # 统计信息
    unassigned_count = Student.objects.filter(
        dormitory__isnull=True,
        status__in=['admitted', 'pending', 'registered']
    ).count()
    
    buildings = DormitoryBuilding.objects.filter(is_active=True)
    
    context = {
        'unassigned_count': unassigned_count,
        'buildings': buildings,
        'available_rooms': DormitoryService.get_available_rooms(),
    }
    return render(request, 'students/dormitory_assignment.html', context)


# ==================== 分班管理 ====================

def class_assignment(request):
    """分班管理页面"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'auto_assign':
            major_id = request.POST.get('major_id') or None
            enrollment_year = request.POST.get('enrollment_year') or None
            class_size = int(request.POST.get('class_size', 30))
            strategy = request.POST.get('strategy', 'balanced')
            
            if enrollment_year:
                enrollment_year = int(enrollment_year)
            
            result = ClassAssignmentService.auto_assign_class(
                major_id=major_id,
                enrollment_year=enrollment_year,
                class_size=class_size,
                strategy=strategy
            )
            
            messages.success(request, result['message'])
    
    # 统计信息
    unassigned_count = Student.objects.filter(
        student_class__isnull=True,
        status__in=['admitted', 'pending', 'registered']
    ).count()
    
    majors = Major.objects.filter(is_active=True).select_related('department')
    classes = StudentClass.objects.filter(is_active=True).select_related('major')
    
    # 获取年份列表
    from datetime import datetime
    current_year = datetime.now().year
    years = list(range(current_year - 2, current_year + 2))
    
    context = {
        'unassigned_count': unassigned_count,
        'majors': majors,
        'classes': classes,
        'years': years,
    }
    return render(request, 'students/class_assignment.html', context)


# ==================== 统计图表 ====================

def charts(request):
    """统计图表页面"""
    context = {
        'gender_chart': ChartService.get_gender_pie_chart(),
        'department_chart': ChartService.get_department_bar_chart(),
        'status_chart': ChartService.get_status_pie_chart(),
        'registration_trend_chart': ChartService.get_registration_trend_chart(),
        'dormitory_chart': ChartService.get_dormitory_occupancy_chart(),
        'payment_chart': ChartService.get_payment_stats_chart(),
    }
    return render(request, 'students/charts.html', context)


# ==================== 学生登录与个人中心 ====================

def student_login(request):
    """学生登录页面"""
    # 如果是学生用户已登录，重定向到个人中心
    if request.user.is_authenticated:
        if hasattr(request.user, 'student_profile') and request.user.student_profile:
            return redirect('students:student_profile')
        # 管理员用户可以继续访问登录页（用于测试学生账号）
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # 检查是否是学生账户
            if hasattr(user, 'student_profile') and user.student_profile:
                messages.success(request, f'欢迎回来，{user.student_profile.name}！')
                return redirect('students:student_profile')
            else:
                messages.success(request, f'欢迎，{user.username}！')
                return redirect('students:home')
        else:
            messages.error(request, '学号或密码错误')
    
    return render(request, 'students/login.html')


def student_logout(request):
    """学生退出登录"""
    logout(request)
    messages.success(request, '您已成功退出登录')
    return redirect('students:student_login')


@login_required(login_url='students:student_login')
def student_profile(request):
    """学生个人中心"""
    # 检查是否是学生账户
    if not hasattr(request.user, 'student_profile') or not request.user.student_profile:
        messages.warning(request, '您不是学生用户，无法访问个人中心')
        return redirect('students:home')
    
    student = request.user.student_profile
    
    # 获取报到进度
    registration_records = RegistrationRecord.objects.filter(
        student=student
    ).select_related('task').order_by('task__order')
    
    # 计算报到完成度（只统计必需任务）
    total_tasks = RegistrationTask.objects.filter(is_active=True, is_required=True).count()
    completed_tasks = registration_records.filter(status='completed', task__is_required=True).count()
    registration_progress = min(round(completed_tasks / total_tasks * 100, 1), 100) if total_tasks > 0 else 0
    
    # 获取缴费信息
    fee_items = FeeItem.objects.filter(student=student)
    payments = Payment.objects.filter(student=student).order_by('-payment_time')
    
    total_fee = fee_items.aggregate(total=Sum('amount'))['total'] or 0
    paid_fee = payments.filter(status='confirmed').aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'student': student,
        'registration_records': registration_records,
        'registration_progress': registration_progress,
        'fee_items': fee_items,
        'payments': payments,
        'total_fee': total_fee,
        'paid_fee': paid_fee,
        'fee_balance': total_fee - paid_fee,
    }
    return render(request, 'students/profile.html', context)


@login_required(login_url='students:student_login')
def change_password(request):
    """修改密码"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if not request.user.check_password(old_password):
            messages.error(request, '原密码错误')
        elif new_password != confirm_password:
            messages.error(request, '两次输入的新密码不一致')
        elif len(new_password) < 6:
            messages.error(request, '新密码长度不能少于6位')
        else:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, '密码修改成功，请重新登录')
            return redirect('students:student_login')
    
    return render(request, 'students/change_password.html')


# ==================== 学生端扩展功能 ====================

def announcement_list(request):
    """通知公告列表"""
    announcements = Announcement.objects.filter(is_published=True)
    
    # 筛选类型
    ann_type = request.GET.get('type', '')
    if ann_type:
        announcements = announcements.filter(announcement_type=ann_type)
    
    # 分页
    paginator = Paginator(announcements, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_type': ann_type,
        'type_choices': Announcement.TYPE_CHOICES,
    }
    return render(request, 'students/announcement_list.html', context)


def announcement_detail(request, pk):
    """通知公告详情"""
    announcement = get_object_or_404(Announcement, pk=pk, is_published=True)
    
    # 增加浏览次数
    announcement.view_count += 1
    announcement.save(update_fields=['view_count'])
    
    # 获取上一篇、下一篇
    prev_ann = Announcement.objects.filter(
        is_published=True, publish_date__gt=announcement.publish_date
    ).order_by('publish_date').first()
    
    next_ann = Announcement.objects.filter(
        is_published=True, publish_date__lt=announcement.publish_date
    ).order_by('-publish_date').first()
    
    context = {
        'announcement': announcement,
        'prev_ann': prev_ann,
        'next_ann': next_ann,
    }
    return render(request, 'students/announcement_detail.html', context)


@login_required(login_url='students:student_login')
def my_documents(request):
    """我的材料"""
    if not hasattr(request.user, 'student_profile') or not request.user.student_profile:
        messages.warning(request, '您不是学生用户')
        return redirect('students:home')
    
    student = request.user.student_profile
    
    # 获取所有材料类型
    document_types = DocumentType.objects.filter(is_active=True)
    
    # 获取学生已提交的材料
    submitted_docs = {doc.document_type_id: doc for doc in student.documents.all()}
    
    # 构建材料列表
    documents = []
    for doc_type in document_types:
        doc = submitted_docs.get(doc_type.id)
        documents.append({
            'type': doc_type,
            'document': doc,
            'status': doc.status if doc else 'pending',
        })
    
    context = {
        'student': student,
        'documents': documents,
    }
    return render(request, 'students/my_documents.html', context)


@login_required(login_url='students:student_login')
def upload_document(request, type_id):
    """上传材料"""
    if not hasattr(request.user, 'student_profile') or not request.user.student_profile:
        return JsonResponse({'success': False, 'message': '您不是学生用户'})
    
    student = request.user.student_profile
    doc_type = get_object_or_404(DocumentType, pk=type_id, is_active=True)
    
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            messages.error(request, '请选择要上传的文件')
            return redirect('students:my_documents')
        
        # 检查文件大小 (最大 10MB)
        if file.size > 10 * 1024 * 1024:
            messages.error(request, '文件大小不能超过 10MB')
            return redirect('students:my_documents')
        
        # 获取或创建文档记录
        from django.utils import timezone
        doc, created = StudentDocument.objects.get_or_create(
            student=student,
            document_type=doc_type,
            defaults={'status': 'submitted', 'submitted_at': timezone.now()}
        )
        
        # 更新文件
        doc.file = file
        doc.status = 'submitted'
        doc.submitted_at = timezone.now()
        doc.reject_reason = ''
        doc.save()
        
        messages.success(request, f'{doc_type.name} 上传成功')
        return redirect('students:my_documents')
    
    return redirect('students:my_documents')


@login_required(login_url='students:student_login')
def my_registration(request):
    """我的报到进度"""
    if not hasattr(request.user, 'student_profile') or not request.user.student_profile:
        messages.warning(request, '您不是学生用户')
        return redirect('students:home')
    
    student = request.user.student_profile
    
    # 获取所有报到环节
    tasks = RegistrationTask.objects.filter(is_active=True).order_by('order')
    
    # 获取学生的报到记录
    records = {r.task_id: r for r in student.registration_records.all()}
    
    # 构建报到进度列表
    progress_list = []
    for task in tasks:
        record = records.get(task.id)
        progress_list.append({
            'task': task,
            'record': record,
            'status': record.status if record else 'pending',
            'completed_at': record.completed_at if record else None,
        })
    
    # 计算完成度
    total_required = tasks.filter(is_required=True).count()
    completed = sum(1 for p in progress_list if p['status'] == 'completed' and p['task'].is_required)
    progress_percent = round(completed / total_required * 100, 1) if total_required > 0 else 0
    
    context = {
        'student': student,
        'progress_list': progress_list,
        'progress_percent': progress_percent,
        'total_tasks': tasks.count(),
        'completed_tasks': sum(1 for p in progress_list if p['status'] == 'completed'),
    }
    return render(request, 'students/my_registration.html', context)


@login_required(login_url='students:student_login')
def my_class(request):
    """我的班级"""
    if not hasattr(request.user, 'student_profile') or not request.user.student_profile:
        messages.warning(request, '您不是学生用户')
        return redirect('students:home')
    
    student = request.user.student_profile
    student_class = student.student_class
    
    # 获取同班同学
    classmates = []
    if student_class:
        classmates = Student.objects.filter(
            student_class=student_class
        ).exclude(pk=student.pk).select_related('dormitory')[:50]
    
    context = {
        'student': student,
        'student_class': student_class,
        'classmates': classmates,
    }
    return render(request, 'students/my_class.html', context)


@login_required(login_url='students:student_login')
def my_dormitory(request):
    """我的宿舍"""
    if not hasattr(request.user, 'student_profile') or not request.user.student_profile:
        messages.warning(request, '您不是学生用户')
        return redirect('students:home')
    
    student = request.user.student_profile
    dormitory = student.dormitory
    
    # 获取室友
    roommates = []
    if dormitory:
        roommates = Student.objects.filter(
            dormitory=dormitory
        ).exclude(pk=student.pk)
    
    context = {
        'student': student,
        'dormitory': dormitory,
        'roommates': roommates,
    }
    return render(request, 'students/my_dormitory.html', context)


@login_required(login_url='students:student_login')
def my_fees(request):
    """我的费用"""
    if not hasattr(request.user, 'student_profile') or not request.user.student_profile:
        messages.warning(request, '您不是学生用户')
        return redirect('students:home')
    
    student = request.user.student_profile
    
    # 获取费用项目
    fee_items = FeeItem.objects.filter(student=student)
    
    # 获取缴费记录
    payments = Payment.objects.filter(student=student).order_by('-payment_time')
    
    # 统计
    total_fee = sum(f.amount for f in fee_items)
    paid_fee = sum(p.amount for p in payments.filter(status='confirmed'))
    
    context = {
        'student': student,
        'fee_items': fee_items,
        'payments': payments,
        'total_fee': total_fee,
        'paid_fee': paid_fee,
        'balance': total_fee - paid_fee,
    }
    return render(request, 'students/my_fees.html', context)


