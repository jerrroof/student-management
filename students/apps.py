from django.apps import AppConfig


class StudentsConfig(AppConfig):
    name = 'students'
    verbose_name = '新生管理'
    
    def ready(self):
        # 导入信号处理器
        import students.signals  # noqa
