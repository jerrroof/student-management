from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from django.utils import timezone


# ==================== 基础信息模型 ====================

class Department(models.Model):
    """院系模型"""
    name = models.CharField('院系名称', max_length=100, unique=True)
    code = models.CharField('院系代码', max_length=20, unique=True)
    description = models.TextField('院系简介', blank=True)
    contact_person = models.CharField('联系人', max_length=50, blank=True)
    contact_phone = models.CharField('联系电话', max_length=20, blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '院系'
        verbose_name_plural = '院系管理'
        ordering = ['code']
    
    def __str__(self):
        return self.name
    
    @property
    def student_count(self):
        """院系学生总数"""
        return self.students.count()
    
    @property
    def major_count(self):
        """院系专业数"""
        return self.majors.count()


class Major(models.Model):
    """专业模型"""
    DEGREE_CHOICES = [
        ('bachelor', '本科'),
        ('master', '硕士'),
        ('doctor', '博士'),
        ('junior', '专科'),
    ]
    
    name = models.CharField('专业名称', max_length=100)
    code = models.CharField('专业代码', max_length=20, unique=True)
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        related_name='majors',
        verbose_name='所属院系'
    )
    degree = models.CharField('学历层次', max_length=20, choices=DEGREE_CHOICES, default='bachelor')
    duration = models.IntegerField('学制(年)', default=4)
    tuition_fee = models.DecimalField('学费标准(元/年)', max_digits=10, decimal_places=2, default=0)
    description = models.TextField('专业简介', blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '专业'
        verbose_name_plural = '专业管理'
        ordering = ['department', 'code']
    
    def __str__(self):
        return f"{self.department.name} - {self.name}"
    
    @property
    def student_count(self):
        """专业学生数"""
        return self.students.count()


class StudentClass(models.Model):
    """班级模型"""
    name = models.CharField('班级名称', max_length=50)
    code = models.CharField('班级代码', max_length=20, unique=True)
    major = models.ForeignKey(
        Major,
        on_delete=models.CASCADE,
        related_name='classes',
        verbose_name='所属专业'
    )
    enrollment_year = models.IntegerField('入学年份')
    counselor = models.CharField('辅导员', max_length=50, blank=True)
    counselor_phone = models.CharField('辅导员电话', max_length=20, blank=True)
    classroom = models.CharField('班级教室', max_length=50, blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '班级'
        verbose_name_plural = '班级管理'
        ordering = ['-enrollment_year', 'code']
    
    def __str__(self):
        return self.name
    
    @property
    def student_count(self):
        """班级学生数"""
        return self.students.count()


# ==================== 宿舍管理模型 ====================

class DormitoryBuilding(models.Model):
    """宿舍楼模型"""
    GENDER_CHOICES = [
        ('M', '男生宿舍'),
        ('F', '女生宿舍'),
        ('X', '混合宿舍'),
    ]
    
    name = models.CharField('楼栋名称', max_length=50, unique=True)
    code = models.CharField('楼栋编号', max_length=20, unique=True)
    gender_type = models.CharField('宿舍类型', max_length=1, choices=GENDER_CHOICES, default='X')
    floors = models.IntegerField('楼层数', default=6)
    manager = models.CharField('楼管姓名', max_length=50, blank=True)
    manager_phone = models.CharField('楼管电话', max_length=20, blank=True)
    address = models.CharField('位置描述', max_length=200, blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '宿舍楼'
        verbose_name_plural = '宿舍楼管理'
        ordering = ['code']
    
    def __str__(self):
        return self.name
    
    @property
    def total_rooms(self):
        """房间总数"""
        return self.rooms.count()
    
    @property
    def total_beds(self):
        """床位总数"""
        return sum(room.capacity for room in self.rooms.all())
    
    @property
    def occupied_beds(self):
        """已入住床位数"""
        return sum(room.current_occupancy for room in self.rooms.all())


class DormitoryRoom(models.Model):
    """宿舍房间模型"""
    ROOM_TYPE_CHOICES = [
        ('standard', '标准间'),
        ('deluxe', '豪华间'),
        ('single', '单人间'),
    ]
    
    building = models.ForeignKey(
        DormitoryBuilding,
        on_delete=models.CASCADE,
        related_name='rooms',
        verbose_name='所属楼栋'
    )
    room_number = models.CharField('房间号', max_length=20)
    floor = models.IntegerField('所在楼层')
    capacity = models.IntegerField('床位数', default=4)
    room_type = models.CharField('房间类型', max_length=20, choices=ROOM_TYPE_CHOICES, default='standard')
    has_bathroom = models.BooleanField('独立卫浴', default=False)
    has_air_conditioner = models.BooleanField('空调', default=False)
    fee_per_year = models.DecimalField('住宿费(元/年)', max_digits=8, decimal_places=2, default=1200)
    remark = models.TextField('备注', blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '宿舍房间'
        verbose_name_plural = '宿舍房间管理'
        unique_together = ['building', 'room_number']
        ordering = ['building', 'floor', 'room_number']
    
    def __str__(self):
        return f"{self.building.name}-{self.room_number}"
    
    @property
    def current_occupancy(self):
        """当前入住人数"""
        return self.students.count()
    
    @property
    def available_beds(self):
        """空余床位"""
        return self.capacity - self.current_occupancy
    
    @property
    def is_full(self):
        """是否已满"""
        return self.current_occupancy >= self.capacity
    
    @property
    def occupancy_rate(self):
        """入住率"""
        if self.capacity == 0:
            return 0
        return round(self.current_occupancy / self.capacity * 100, 1)


# ==================== 学生信息模型 ====================

class Student(models.Model):
    """新生信息模型"""
    GENDER_CHOICES = [
        ('M', '男'),
        ('F', '女'),
    ]
    
    STATUS_CHOICES = [
        ('admitted', '已录取'),
        ('pending', '待报到'),
        ('registered', '已报到'),
        ('completed', '已完成'),
        ('deferred', '保留学籍'),
        ('cancelled', '取消入学'),
    ]
    
    POLITICAL_CHOICES = [
        ('masses', '群众'),
        ('league', '共青团员'),
        ('party', '中共党员'),
        ('prep', '中共预备党员'),
        ('democratic', '民主党派'),
    ]
    
    # 手机号验证器
    phone_validator = RegexValidator(
        regex=r'^1[3-9]\d{9}$',
        message='请输入有效的手机号码'
    )
    
    # 身份证验证器
    id_card_validator = RegexValidator(
        regex=r'^\d{17}[\dXx]$',
        message='请输入有效的身份证号码'
    )
    
    # === 基本信息 ===
    student_id = models.CharField('学号', max_length=20, unique=True)
    name = models.CharField('姓名', max_length=50)
    gender = models.CharField('性别', max_length=1, choices=GENDER_CHOICES)
    id_card = models.CharField('身份证号', max_length=18, unique=True, validators=[id_card_validator])
    birthday = models.DateField('出生日期', null=True, blank=True)
    ethnicity = models.CharField('民族', max_length=20, default='汉族')
    political_status = models.CharField('政治面貌', max_length=20, choices=POLITICAL_CHOICES, default='masses')
    photo = models.ImageField('照片', upload_to='photos/', blank=True, null=True)
    
    # === 联系方式 ===
    phone = models.CharField('联系电话', max_length=20, validators=[phone_validator])
    email = models.EmailField('邮箱', blank=True)
    qq = models.CharField('QQ号', max_length=20, blank=True)
    wechat = models.CharField('微信号', max_length=50, blank=True)
    
    # === 录取信息 ===
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        related_name='students',
        verbose_name='院系'
    )
    major = models.ForeignKey(
        Major,
        on_delete=models.SET_NULL,
        null=True,
        related_name='students',
        verbose_name='专业'
    )
    student_class = models.ForeignKey(
        StudentClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name='班级'
    )
    enrollment_year = models.IntegerField('入学年份')
    admission_ticket = models.CharField('准考证号', max_length=30, blank=True)
    exam_score = models.DecimalField('高考成绩', max_digits=6, decimal_places=2, null=True, blank=True)
    
    # === 宿舍信息 ===
    dormitory = models.ForeignKey(
        DormitoryRoom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name='宿舍'
    )
    bed_number = models.CharField('床位号', max_length=10, blank=True)
    
    # === 报到状态 ===
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='admitted')
    registration_date = models.DateTimeField('报到时间', null=True, blank=True)
    
    # === 家庭信息 ===
    home_address = models.TextField('家庭地址', blank=True)
    home_postcode = models.CharField('邮政编码', max_length=10, blank=True)
    
    # === 紧急联系人 ===
    emergency_contact = models.CharField('紧急联系人', max_length=50, blank=True)
    emergency_relation = models.CharField('与本人关系', max_length=20, blank=True)
    emergency_phone = models.CharField('紧急联系电话', max_length=20, blank=True)
    
    # === 备注 ===
    remark = models.TextField('备注', blank=True)
    
    # === 用户账户 ===
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_profile',
        verbose_name='关联用户'
    )
    
    # === 时间戳 ===
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '新生'
        verbose_name_plural = '新生管理'
        ordering = ['-enrollment_year', 'student_id']
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['id_card']),
            models.Index(fields=['status']),
            models.Index(fields=['enrollment_year']),
        ]
    
    def __str__(self):
        return f"{self.student_id} - {self.name}"
    
    @property
    def total_tuition(self):
        """应缴学费总额"""
        return sum(fee.amount for fee in self.fee_items.all())
    
    @property
    def paid_tuition(self):
        """已缴学费总额"""
        return sum(
            payment.amount 
            for payment in self.payments.filter(status='confirmed')
        )
    
    @property
    def tuition_balance(self):
        """学费余额"""
        return self.total_tuition - self.paid_tuition
    
    @property
    def is_paid(self):
        """是否已缴清学费"""
        return self.paid_tuition >= self.total_tuition
    
    @property
    def age(self):
        """年龄"""
        if self.birthday:
            from datetime import date
            today = date.today()
            return today.year - self.birthday.year - (
                (today.month, today.day) < (self.birthday.month, self.birthday.day)
            )
        return None


# ==================== 费用管理模型 ====================

class FeeItem(models.Model):
    """收费项目模型"""
    FEE_TYPE_CHOICES = [
        ('tuition', '学费'),
        ('accommodation', '住宿费'),
        ('textbook', '教材费'),
        ('insurance', '保险费'),
        ('military', '军训服装费'),
        ('physical', '体检费'),
        ('other', '其他费用'),
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='fee_items',
        verbose_name='学生'
    )
    fee_type = models.CharField('费用类型', max_length=20, choices=FEE_TYPE_CHOICES)
    name = models.CharField('费用名称', max_length=100)
    amount = models.DecimalField('金额', max_digits=10, decimal_places=2)
    academic_year = models.CharField('学年', max_length=20)  # 如: 2026-2027
    is_required = models.BooleanField('是否必缴', default=True)
    remark = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '收费项目'
        verbose_name_plural = '收费项目管理'
        ordering = ['student', 'fee_type']
    
    def __str__(self):
        return f"{self.student.name} - {self.name}: ¥{self.amount}"


class Payment(models.Model):
    """缴费记录模型"""
    PAYMENT_METHOD_CHOICES = [
        ('cash', '现金'),
        ('card', '银行卡'),
        ('alipay', '支付宝'),
        ('wechat', '微信支付'),
        ('transfer', '银行转账'),
        ('loan', '助学贷款'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待确认'),
        ('confirmed', '已确认'),
        ('rejected', '已退回'),
        ('refunded', '已退款'),
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='学生'
    )
    payment_no = models.CharField('缴费单号', max_length=50, unique=True, blank=True)
    amount = models.DecimalField('缴费金额', max_digits=10, decimal_places=2)
    payment_method = models.CharField('支付方式', max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_time = models.DateTimeField('缴费时间', default=timezone.now)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # 关联收费项目(可选)
    fee_items = models.ManyToManyField(
        FeeItem,
        blank=True,
        related_name='payments',
        verbose_name='关联收费项目'
    )
    
    transaction_id = models.CharField('交易流水号', max_length=100, blank=True)
    operator = models.CharField('操作员', max_length=50, blank=True)
    remark = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '缴费记录'
        verbose_name_plural = '缴费记录管理'
        ordering = ['-payment_time']
    
    def save(self, *args, **kwargs):
        """保存时自动生成唯一的缴费单号"""
        if not self.payment_no:
            import time
            # 使用学号+毫秒时间戳生成唯一单号
            self.payment_no = f'PAY{self.student.student_id}{int(time.time() * 1000)}'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.payment_no} - {self.student.name}: ¥{self.amount}"


# ==================== 报到管理模型 ====================

class RegistrationTask(models.Model):
    """报到任务/环节模型"""
    name = models.CharField('环节名称', max_length=100)
    code = models.CharField('环节代码', max_length=20, unique=True)
    description = models.TextField('环节说明', blank=True)
    location = models.CharField('办理地点', max_length=200, blank=True)
    order = models.IntegerField('顺序', default=0)
    is_required = models.BooleanField('是否必须', default=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '报到环节'
        verbose_name_plural = '报到环节管理'
        ordering = ['order']
    
    def __str__(self):
        return self.name


class RegistrationRecord(models.Model):
    """报到记录模型"""
    STATUS_CHOICES = [
        ('pending', '待办理'),
        ('completed', '已完成'),
        ('skipped', '已跳过'),
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='registration_records',
        verbose_name='学生'
    )
    task = models.ForeignKey(
        RegistrationTask,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name='报到环节'
    )
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)
    operator = models.CharField('操作员', max_length=50, blank=True)
    remark = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '报到记录'
        verbose_name_plural = '报到记录管理'
        unique_together = ['student', 'task']
        ordering = ['student', 'task__order']
    
    def __str__(self):
        return f"{self.student.name} - {self.task.name}"


# ==================== 材料管理模型 ====================

class DocumentType(models.Model):
    """材料类型模型"""
    name = models.CharField('材料名称', max_length=100)
    code = models.CharField('材料代码', max_length=20, unique=True)
    description = models.TextField('材料说明', blank=True)
    is_required = models.BooleanField('是否必须', default=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '材料类型'
        verbose_name_plural = '材料类型管理'
        ordering = ['code']
    
    def __str__(self):
        return self.name


class StudentDocument(models.Model):
    """学生材料模型"""
    STATUS_CHOICES = [
        ('pending', '待提交'),
        ('submitted', '已提交'),
        ('approved', '已审核'),
        ('rejected', '已退回'),
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='学生'
    )
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.CASCADE,
        related_name='student_documents',
        verbose_name='材料类型'
    )
    file = models.FileField('文件', upload_to='documents/', blank=True, null=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField('提交时间', null=True, blank=True)
    reviewed_at = models.DateTimeField('审核时间', null=True, blank=True)
    reviewer = models.CharField('审核人', max_length=50, blank=True)
    reject_reason = models.TextField('退回原因', blank=True)
    remark = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '学生材料'
        verbose_name_plural = '学生材料管理'
        unique_together = ['student', 'document_type']
        ordering = ['student', 'document_type']
    
    def __str__(self):
        return f"{self.student.name} - {self.document_type.name}"


# ==================== 通知公告模型 ====================

class Announcement(models.Model):
    """通知公告模型"""
    TYPE_CHOICES = [
        ('notice', '通知'),
        ('news', '新闻'),
        ('guide', '指南'),
        ('important', '重要公告'),
    ]
    
    title = models.CharField('标题', max_length=200)
    content = models.TextField('内容')
    announcement_type = models.CharField('类型', max_length=20, choices=TYPE_CHOICES, default='notice')
    is_top = models.BooleanField('置顶', default=False)
    is_published = models.BooleanField('已发布', default=True)
    author = models.CharField('发布人', max_length=50, blank=True)
    view_count = models.IntegerField('浏览次数', default=0)
    publish_date = models.DateTimeField('发布时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '通知公告'
        verbose_name_plural = '通知公告管理'
        ordering = ['-is_top', '-publish_date']
    
    def __str__(self):
        return self.title


# ==================== 系统配置模型 ====================

class SystemConfig(models.Model):
    """系统配置模型"""
    key = models.CharField('配置键', max_length=100, unique=True)
    value = models.TextField('配置值')
    description = models.CharField('配置说明', max_length=200, blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '系统配置'
        verbose_name_plural = '系统配置管理'
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"
