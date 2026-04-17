# 新生管理系统

基于 Django 6.0.3 + SimpleUI + Bootstrap 5 构建的高校新生管理系统，实现新生信息管理、报到流程管理、宿舍自动分配、自动分班及数据统计分析等功能。

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | Django 6.0.3 |
| 后台管理 | Django Admin + SimpleUI |
| 前端框架 | Bootstrap 5 |
| 数据可视化 | pyecharts 2.1.0 |
| 数据处理 | pandas + openpyxl |
| 数据库 | SQLite |
| 部署平台 | PythonAnywhere |

## 功能模块

### 1. 新生管理
- 学生信息录入、查询、修改、删除
- Excel 批量导入/导出学生数据
- 导入模板下载

### 2. 报到管理
- 报到状态流转（已录取 → 待报到 → 已报到 → 已完成）
- 报到环节管理
- 缴费确认与记录

### 3. 宿舍分配
- 三种分配策略：顺序分配、均衡分配、按班级分配
- 宿舍楼/房间/床位管理
- 分配结果展示

### 4. 自动分班
- 蛇形分配算法，按高考成绩均衡分班
- 支持自定义班级数量

### 5. 统计分析
- 性别分布统计
- 院系人数统计
- 报到状态统计
- 宿舍入住率统计

### 6. 学生端
- 学生登录（学号 + 身份证后6位）
- 个人信息查看
- 报到信息、班级信息、宿舍信息、缴费信息查询
- 密码修改

### 7. 通知公告
- 公告发布与管理
- 学生端公告浏览

## 项目结构

```
├── student_management/     # Django 项目配置
│   ├── settings.py         # 项目配置
│   ├── urls.py             # 主路由
│   └── wsgi.py             # WSGI 入口
├── students/               # 学生管理应用
│   ├── models.py           # 数据模型
│   ├── views.py            # 视图函数
│   ├── urls.py             # 应用路由
│   ├── admin.py            # 后台管理配置
│   ├── services.py         # 业务逻辑层
│   └── templatetags/       # 自定义模板标签
├── templates/              # 模板文件
│   ├── base.html           # 基础模板
│   ├── students/           # 学生相关页面
│   └── student_portal/     # 学生端页面
├── static/                 # 静态文件
├── media/                  # 媒体文件
├── requirements.txt        # 依赖列表
├── build.sh                # 构建脚本
├── init_data.py            # 初始化数据脚本
├── manage.py               # Django 管理脚本
└── db.sqlite3              # 数据库文件
```

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/jerrroof/student-management.git
cd student-management
```

### 2. 创建虚拟环境

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 数据库迁移

```bash
python manage.py migrate
```

### 5. 创建超级用户

```bash
python manage.py createsuperuser
```

### 6. 初始化数据

```bash
python init_data.py
```

### 7. 启动服务

```bash
python manage.py runserver
```

### 8. 访问系统

| 页面 | 地址 |
|------|------|
| 系统首页 | http://127.0.0.1:8000/ |
| 后台管理 | http://127.0.0.1:8000/admin/ |
| 学生登录 | http://127.0.0.1:8000/student/login/ |

## 主要接口

| URL | 方法 | 功能 |
|-----|------|------|
| `/` | GET | 数据概览首页 |
| `/students/list/` | GET | 新生列表 |
| `/students/import/` | POST | Excel 批量导入 |
| `/students/export/` | GET | Excel 导出 |
| `/registration/` | GET/POST | 报到管理 |
| `/dormitories/` | GET | 宿舍概况 |
| `/dormitories/assignment/` | POST | 宿舍自动分配 |
| `/classes/auto-assign/` | POST | 自动分班 |
| `/charts/` | GET | 统计图表 |
| `/student/login/` | GET/POST | 学生登录 |
| `/student/profile/` | GET | 个人信息 |

## 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 学生 | 学号 | 身份证后6位 |

## 环境要求

- Python >= 3.12
- Django >= 6.0.3

## 线上地址

- https://jerrroof.pythonanywhere.com

## License

MIT License
