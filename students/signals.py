"""
学生账户信号处理器
自动为学生创建关联的用户账户
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Student


def create_user_for_student(student):
    """
    为学生创建用户账户
    用户名: 学号
    初始密码: 身份证后6位
    """
    if student.user:
        return student.user
    
    # 检查用户名是否已存在
    username = student.student_id
    if User.objects.filter(username=username).exists():
        # 如果用户已存在，关联到学生
        user = User.objects.get(username=username)
        student.user = user
        student.save(update_fields=['user'])
        return user
    
    # 创建新用户
    # 初始密码为身份证后6位
    password = student.id_card[-6:] if student.id_card else '123456'
    
    user = User.objects.create_user(
        username=username,
        password=password,
        first_name=student.name,
        email=student.email or '',
        is_active=True,
        is_staff=False,  # 学生不是管理员
    )
    
    # 关联到学生
    student.user = user
    student.save(update_fields=['user'])
    
    return user


@receiver(post_save, sender=Student)
def auto_create_user(sender, instance, created, **kwargs):
    """
    学生保存后自动创建用户账户
    只在新建学生时自动创建，避免重复创建
    """
    # 如果是新创建且没有关联用户，自动创建
    if created and not instance.user:
        create_user_for_student(instance)
