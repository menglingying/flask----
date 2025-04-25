from flask import Flask
from config import config
import os

def create_app():
    # 创建应用实例
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(config['development'])

    # 确保上传文件夹存在
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # 导入路由
    from routes_main import main
    from routes_admin import admin
    from routes_volunteer import volunteer
    from routes_charity import charity

    # 注册蓝图
    app.register_blueprint(main)
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(volunteer, url_prefix='/volunteer')
    app.register_blueprint(charity, url_prefix='/charity')

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
