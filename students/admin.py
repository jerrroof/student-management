from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.db.models import Sum, Count
from .models import (
    Department, Major, StudentClass,
    DormitoryBuilding, DormitoryRoom,
    Student, FeeItem, Payment,
    RegistrationTask, RegistrationRecord,
    DocumentType, StudentDocument,
    SystemConfig, Announcement
)


# ==================== Admin 站点配置 ====================
admin.site.site_header = '新生管理系统'
admin.site.site_title = '新生管理系统'
admin.site.index_title = '欢迎使用新生管理系统'


# ==================== 基础信息管理 ====================

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'contact_person', 'contact_phone', 'major_count', 'student_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']
    list_editable = ['is_active']
    ordering = ['code']


@admin.register(Major)
class MajorAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'degree', 'duration', 'tuition_fee', 'student_count', 'is_active']
    list_filter = ['department', 'degree', 'is_active']
    search_fields = ['code', 'name']
    list_editable = ['is_active']
    autocomplete_fields = ['department']
    ordering = ['department', 'code']


@admin.register(StudentClass)
class StudentClassAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'major', 'enrollment_year', 'counselor', 'student_count', 'is_active']
    list_filter = ['enrollment_year', 'major__department', 'is_active']
    search_fields = ['code', 'name', 'counselor']
    list_editable = ['is_active']
    autocomplete_fields = ['major']
    ordering = ['-enrollment_year', 'code']


# ==================== 宿舍管理 ====================

@admin.register(DormitoryBuilding)
class DormitoryBuildingAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'gender_type', 'floors', 'total_rooms', 'total_beds', 'occupied_beds', 'manager', 'is_active']
    list_filter = ['gender_type', 'is_active']
    search_fields = ['code', 'name', 'manager']
    list_editable = ['is_active']
    ordering = ['code']


@admin.register(DormitoryRoom)
class DormitoryRoomAdmin(admin.ModelAdmin):
    list_display = ['building', 'room_number', 'floor', 'room_type', 'capacity', 'current_occupancy', 'available_beds', 'is_full', 'is_active']
    list_filter = ['building', 'floor', 'room_type', 'is_active']
    search_fields = ['room_number', 'building__name']
    list_editable = ['is_active']
    autocomplete_fields = ['building']
    ordering = ['building', 'floor', 'room_number']


# ==================== 新生管理 ====================

class FeeItemInline(admin.TabularInline):
    model = FeeItem
    extra = 1
    fields = ['fee_type', 'name', 'amount', 'academic_year', 'is_required']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ['payment_no', 'amount', 'payment_method', 'payment_time', 'status']
    readonly_fields = ['payment_no']
    
    def get_readonly_fields(self, request, obj=None):
        """新增时允许编辑 payment_time，编辑时只读"""
        if obj:  # 编辑现有记录
            return ['payment_no', 'payment_time']
        return ['payment_no']


class RegistrationRecordInline(admin.TabularInline):
    model = RegistrationRecord
    extra = 0
    fields = ['task', 'status', 'completed_at', 'operator']
    readonly_fields = ['completed_at']
    
    def get_formset(self, request, obj=None, **kwargs):
        """保存 request 以便在 formset 中使用"""
        formset = super().get_formset(request, obj, **kwargs)
        formset.request = request
        return formset


class StudentDocumentInline(admin.TabularInline):
    model = StudentDocument
    extra = 0
    fields = ['document_type', 'status', 'submitted_at', 'reviewed_at']
    readonly_fields = ['submitted_at', 'reviewed_at']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'name', 'gender_colored', 'department', 'major', 'student_class', 'status_badge', 'has_user_account', 'is_paid', 'created_at']
    list_filter = ['status', 'gender', 'department', 'enrollment_year']
    search_fields = ['student_id', 'name', 'id_card', 'phone']
    list_per_page = 20
    date_hierarchy = 'created_at'
    autocomplete_fields = ['department', 'major', 'student_class', 'dormitory']
    actions = ['mark_as_registered', 'mark_as_completed', 'create_user_accounts', 'export_selected']
    
    fieldsets = (
        ('基本信息', {
            'fields': (
                ('student_id', 'name'),
                ('gender', 'birthday', 'ethnicity'),
                ('id_card', 'political_status'),
                'photo'
            )
        }),
        ('联系方式', {
            'fields': (
                ('phone', 'email'),
                ('qq', 'wechat')
            )
        }),
        ('录取信息', {
            'fields': (
                ('department', 'major'),
                ('student_class', 'enrollment_year'),
                ('admission_ticket', 'exam_score')
            )
        }),
        ('宿舍信息', {
            'fields': (
                ('dormitory', 'bed_number'),
            )
        }),
        ('状态信息', {
            'fields': (
                ('status', 'registration_date'),
            )
        }),
        ('用户账户', {
            'fields': ('user',),
            'description': '关联的系统用户账户，学生可使用此账户登录系统'
        }),
        ('家庭信息', {
            'fields': (
                'home_address',
                'home_postcode'
            ),
            'classes': ('collapse',)
        }),
        ('紧急联系人', {
            'fields': (
                ('emergency_contact', 'emergency_relation'),
                'emergency_phone'
            ),
            'classes': ('collapse',)
        }),
        ('备注', {
            'fields': ('remark',),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [FeeItemInline, PaymentInline, RegistrationRecordInline, StudentDocumentInline]
    
    def gender_colored(self, obj):
        if obj.gender == 'M':
            return format_html('<span style="color: {};">♂ 男</span>', '#3498db')
        return format_html('<span style="color: {};">♀ 女</span>', '#e74c3c')
    gender_colored.short_description = '性别'
    gender_colored.admin_order_field = 'gender'
    
    def status_badge(self, obj):
        colors = {
            'admitted': '#6c757d',
            'pending': '#ffc107',
            'registered': '#17a2b8',
            'completed': '#28a745',
            'deferred': '#fd7e14',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = '状态'
    status_badge.admin_order_field = 'status'
    
    def is_paid(self, obj):
        return obj.is_paid
    is_paid.boolean = True
    is_paid.short_description = '已缴清'
    
    def has_user_account(self, obj):
        return obj.user is not None
    has_user_account.boolean = True
    has_user_account.short_description = '已创建账户'
    
    @admin.action(description='标记为已报到')
    def mark_as_registered(self, request, queryset):
        updated = queryset.filter(status__in=['admitted', 'pending']).update(
            status='registered',
            registration_date=timezone.now()
        )
        self.message_user(request, f'成功将 {updated} 名学生标记为已报到')
    
    @admin.action(description='标记为已完成')
    def mark_as_completed(self, request, queryset):
        updated = queryset.filter(status='registered').update(status='completed')
        self.message_user(request, f'成功将 {updated} 名学生标记为已完成')
    
    @admin.action(description='批量创建用户账户')
    def create_user_accounts(self, request, queryset):
        from .signals import create_user_for_student
        created_count = 0
        for student in queryset.filter(user__isnull=True):
            create_user_for_student(student)
            created_count += 1
        self.message_user(request, f'成功为 {created_count} 名学生创建用户账户（用户名为学号，初始密码为身份证后6位）')
    
    @admin.action(description='导出选中学生信息')
    def export_selected(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="students.csv"'
        response.write('\ufeff'.encode('utf-8'))  # BOM for Excel
        
        writer = csv.writer(response)
        writer.writerow(['学号', '姓名', '性别', '身份证号', '电话', '院系', '专业', '班级', '状态', '报到时间'])
        
        for student in queryset:
            writer.writerow([
                student.student_id,
                student.name,
                student.get_gender_display(),
                student.id_card,
                student.phone,
                student.department.name if student.department else '',
                student.major.name if student.major else '',
                student.student_class.name if student.student_class else '',
                student.get_status_display(),
                student.registration_date.strftime('%Y-%m-%d %H:%M') if student.registration_date else '',
            ])
        
        return response
    
    def save_formset(self, request, form, formset, change):
        """保存内联表单时处理缴费确认"""
        instances = formset.save(commit=False)
        
        # 收集待处理的报到记录
        registration_records_to_check = []
        
        for instance in instances:
            instance.save()
            # 如果是报到记录且是缴费确认环节已完成，先记录下来
            if isinstance(instance, RegistrationRecord):
                if instance.task.code == 'T003' and instance.status == 'completed':
                    registration_records_to_check.append(instance)
        
        formset.save_m2m()
        
        # 处理删除的对象
        for obj in formset.deleted_objects:
            obj.delete()
        
        # 最后处理自动创建缴费记录（避免和手动添加的冲突）
        for record in registration_records_to_check:
            self._auto_create_payment(record.student, request.user.username)
    
    def _auto_create_payment(self, student, operator):
        """自动创建缴费记录"""
        from django.db import IntegrityError
        
        # 检查是否已有确认的缴费记录
        if Payment.objects.filter(student=student, status='confirmed').exists():
            return
        
        fees = FeeItem.objects.filter(student=student)
        total = sum(f.amount for f in fees)
        
        if total > 0:
            # 生成唯一的缴费单号（使用时间戳+微秒）
            import time
            base_no = f'PAY{student.student_id}{int(time.time() * 1000)}'
            
            try:
                Payment.objects.create(
                    student=student,
                    payment_no=base_no,
                    amount=total,
                    payment_method='other',
                    payment_time=timezone.now(),
                    status='confirmed',
                    operator=operator,
                    remark='缴费确认时自动生成'
                )
            except IntegrityError:
                # 如果仍然冲突，说明已有记录，跳过
                pass


# ==================== 费用管理 ====================

@admin.register(FeeItem)
class FeeItemAdmin(admin.ModelAdmin):
    list_display = ['student', 'fee_type', 'name', 'amount', 'academic_year', 'is_required']
    list_filter = ['fee_type', 'academic_year', 'is_required']
    search_fields = ['student__name', 'student__student_id', 'name']
    autocomplete_fields = ['student']
    list_per_page = 30


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_no', 'student', 'amount', 'payment_method', 'payment_time', 'status', 'operator']
    list_filter = ['status', 'payment_method', 'payment_time']
    search_fields = ['payment_no', 'student__name', 'student__student_id', 'transaction_id']
    autocomplete_fields = ['student']
    date_hierarchy = 'payment_time'
    list_per_page = 30
    
    fieldsets = (
        ('基本信息', {
            'fields': (
                'student',
                ('payment_no', 'amount'),
                ('payment_method', 'payment_time'),
                'status'
            )
        }),
        ('关联信息', {
            'fields': (
                'fee_items',
                ('transaction_id', 'operator'),
                'remark'
            )
        }),
    )
    filter_horizontal = ['fee_items']


# ==================== 报到管理 ====================

@admin.register(RegistrationTask)
class RegistrationTaskAdmin(admin.ModelAdmin):
    list_display = ['order', 'code', 'name', 'location', 'is_required', 'is_active']
    list_display_links = ['code', 'name']
    list_filter = ['is_required', 'is_active']
    search_fields = ['code', 'name']
    list_editable = ['order', 'is_required', 'is_active']
    ordering = ['order']


@admin.register(RegistrationRecord)
class RegistrationRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'task', 'status', 'completed_at', 'operator']
    list_filter = ['status', 'task']
    search_fields = ['student__name', 'student__student_id', 'operator']
    autocomplete_fields = ['student', 'task']
    date_hierarchy = 'completed_at'
    
    def save_model(self, request, obj, form, change):
        """保存时自动处理缴费确认"""
        super().save_model(request, obj, form, change)
        
        # 如果是缴费确认环节且状态为已完成，自动创建缴费记录
        if obj.task.code == 'T003' and obj.status == 'completed':
            self._auto_create_payment(obj.student, request.user.username)
    
    def _auto_create_payment(self, student, operator):
        """自动创建缴费记录"""
        from django.db import IntegrityError
        
        # 检查是否已有确认的缴费记录
        if Payment.objects.filter(student=student, status='confirmed').exists():
            return
        
        # 计算应缴总额
        fees = FeeItem.objects.filter(student=student)
        total = sum(f.amount for f in fees)
        
        if total > 0:
            # 生成唯一的缴费单号（使用时间戳+微秒）
            import time
            base_no = f'PAY{student.student_id}{int(time.time() * 1000)}'
            
            try:
                Payment.objects.create(
                    student=student,
                    payment_no=base_no,
                    amount=total,
                    payment_method='other',
                    payment_time=timezone.now(),
                    status='confirmed',
                    operator=operator,
                    remark='缴费确认时自动生成'
                )
            except IntegrityError:
                # 如果仍然冲突，说明已有记录，跳过
                pass


# ==================== 材料管理 ====================

@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_required', 'is_active']
    list_filter = ['is_required', 'is_active']
    search_fields = ['code', 'name']
    list_editable = ['is_required', 'is_active']


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ['student', 'document_type', 'status', 'submitted_at', 'reviewed_at', 'reviewer']
    list_filter = ['status', 'document_type']
    search_fields = ['student__name', 'student__student_id', 'reviewer']
    autocomplete_fields = ['student', 'document_type']
    date_hierarchy = 'submitted_at'


# ==================== 系统配置 ====================

@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'description', 'is_active', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['key', 'description']
    list_editable = ['is_active']


# ==================== 通知公告 ====================

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'announcement_type', 'author', 'is_top', 'is_published', 'view_count', 'publish_date']
    list_filter = ['announcement_type', 'is_top', 'is_published']
    search_fields = ['title', 'content', 'author']
    list_editable = ['is_top', 'is_published']
    date_hierarchy = 'publish_date'
    ordering = ['-is_top', '-publish_date']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'announcement_type', 'author')
        }),
        ('内容', {
            'fields': ('content',)
        }),
        ('发布设置', {
            'fields': ('is_top', 'is_published')
        }),
    )
