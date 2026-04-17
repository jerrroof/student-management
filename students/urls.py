from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # 首页
    path('', views.home, name='home'),
    
    # 新生管理
    path('students/', views.student_list, name='student_list'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    
    # Excel 导入导出
    path('students/export/', views.export_students, name='export_students'),
    path('students/import/', views.import_students, name='import_students'),
    path('students/import/template/', views.download_import_template, name='download_import_template'),
    
    # 报到管理
    path('registration/', views.registration, name='registration'),
    
    # 宿舍管理
    path('dormitories/', views.dormitory_list, name='dormitory_list'),
    path('dormitories/assignment/', views.dormitory_assignment, name='dormitory_assignment'),
    
    # 分班管理
    path('classes/assignment/', views.class_assignment, name='class_assignment'),
    
    # 统计报表
    path('statistics/', views.statistics, name='statistics'),
    path('charts/', views.charts, name='charts'),
    
    # 通知公告
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/<int:pk>/', views.announcement_detail, name='announcement_detail'),
    
    # 学生登录与个人中心
    path('login/', views.student_login, name='student_login'),
    path('logout/', views.student_logout, name='student_logout'),
    path('profile/', views.student_profile, name='student_profile'),
    path('password/change/', views.change_password, name='change_password'),
    
    # 学生端功能
    path('my/documents/', views.my_documents, name='my_documents'),
    path('my/documents/upload/<int:type_id>/', views.upload_document, name='upload_document'),
    path('my/registration/', views.my_registration, name='my_registration'),
    path('my/class/', views.my_class, name='my_class'),
    path('my/dormitory/', views.my_dormitory, name='my_dormitory'),
    path('my/fees/', views.my_fees, name='my_fees'),
]
