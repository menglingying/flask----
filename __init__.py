from flask import Flask
from config import config
import os
import mysql.connector

# 创建应用实例
app = Flask(__name__)

# 加载配置
app.config.from_object(config['development'])

# 创建数据库连接池
def get_db_connection():
    return mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )

# 确保上传文件夹存在
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
