from app import app
import os

if __name__ == '__main__':
    # 确保上传文件夹存在
    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    app.run(debug=True)
