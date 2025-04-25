import mysql.connector
from werkzeug.security import generate_password_hash

def init_db():
    # 连接到MySQL服务器
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456"
    )
    cursor = conn.cursor()
    
    # 创建数据库
    cursor.execute("CREATE DATABASE IF NOT EXISTS charity_platform")
    print("数据库创建成功")
    
    # 使用创建的数据库
    cursor.execute("USE charity_platform")
    
    # 创建用户表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        user_type ENUM('volunteer', 'charity', 'admin') NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status ENUM('pending', 'approved', 'suspended') DEFAULT 'pending'
    )
    """)
    print("用户表创建成功")
    
    # 创建志愿者表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS volunteers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        name VARCHAR(100) NOT NULL,
        gender ENUM('male', 'female', 'other'),
        total_hours FLOAT DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)
    print("志愿者表创建成功")
    
    # 创建慈善机构表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS charities (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        name VARCHAR(100) NOT NULL,
        address VARCHAR(255),
        description TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)
    print("慈善机构表创建成功")
    
    # 创建活动表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INT AUTO_INCREMENT PRIMARY KEY,
        charity_id INT NOT NULL,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        location VARCHAR(255),
        start_time DATETIME NOT NULL,
        end_time DATETIME NOT NULL,
        required_skills TEXT,
        status ENUM('pending', 'approved', 'rejected', 'completed') DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (charity_id) REFERENCES charities(id) ON DELETE CASCADE
    )
    """)
    print("活动表创建成功")
    
    # 创建注册表（志愿者注册活动）
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registrations (
        id INT AUTO_INCREMENT PRIMARY KEY,
        volunteer_id INT NOT NULL,
        event_id INT NOT NULL,
        status ENUM('pending', 'approved', 'rejected', 'completed') DEFAULT 'pending',
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        hours_contributed FLOAT DEFAULT 0,
        FOREIGN KEY (volunteer_id) REFERENCES volunteers(id) ON DELETE CASCADE,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
        UNIQUE KEY (volunteer_id, event_id)
    )
    """)
    print("注册表创建成功")
    
    # 创建活动文件表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS event_files (
        id INT AUTO_INCREMENT PRIMARY KEY,
        event_id INT NOT NULL,
        filename VARCHAR(255) NOT NULL,
        original_filename VARCHAR(255) NOT NULL,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
    )
    """)
    print("活动文件表创建成功")
    
    # 检查是否已存在管理员账户
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    admin = cursor.fetchone()
    
    if not admin:
        # 创建管理员账户
        admin_password = generate_password_hash('admin123')
        cursor.execute("""
        INSERT INTO users (username, password, email, user_type, status)
        VALUES (%s, %s, %s, %s, %s)
        """, ('admin', admin_password, 'admin@example.com', 'admin', 'approved'))
        print("管理员账户创建成功 (用户名: admin, 密码: admin123)")
    
    # 提交更改并关闭连接
    conn.commit()
    cursor.close()
    conn.close()
    
    print("数据库初始化完成")

if __name__ == "__main__":
    init_db()
