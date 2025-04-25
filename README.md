# 慈善平台

这是一个基于Flask的慈善平台Web应用程序，旨在连接志愿者与慈善组织。

## 功能

- 志愿者可以浏览和注册参与机会
- 慈善组织可以发布和管理项目
- 管理员可以监督平台运营

## 技术栈

- 前端：HTML5、CSS、JavaScript、jQuery
- 后端：Flask、Python 3
- 数据库：MySQL 5.7

## 运行说明

### 前提条件

- Python 3.6+
- MySQL 5.7
- 虚拟环境（推荐）

### 安装步骤

1. 激活虚拟环境（如果使用）
   ```
   E:\pythonProject\venv_new\Scripts\activate
   ```

2. 安装依赖
   ```
   install_dependencies.bat
   ```
   或手动安装：
   ```
   pip install flask mysql-connector-python werkzeug
   ```

3. 初始化数据库并启动应用
   ```
   start.bat
   ```
   或手动执行：
   ```
   python setup.py
   python run.py
   ```

4. 在浏览器中访问 http://localhost:5000

### 默认账户

- 管理员账户：
  - 用户名：admin
  - 密码：admin123

## 项目结构

- `app.py`: 应用入口文件
- `config.py`: 配置文件
- `models.py`: 数据模型
- `routes_main.py`: 主路由
- `routes_admin.py`: 管理员路由
- `routes_volunteer.py`: 志愿者路由
- `routes_charity.py`: 慈善机构路由
- `utils.py`: 工具函数
- `setup.py`: 数据库初始化脚本
- `static/`: 静态文件（CSS、JS、图片等）
- `templates/`: HTML模板
