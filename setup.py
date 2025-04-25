import mysql.connector
from werkzeug.security import generate_password_hash
import os

def setup_database():
    # 连接到MySQL服务器
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456"
    )
    cursor = conn.cursor()

    # Create database with UTF-8 character set
    cursor.execute("CREATE DATABASE IF NOT EXISTS charity_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    print("Database created successfully")

    # Use the created database
    cursor.execute("USE charity_platform")

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        user_type ENUM('volunteer', 'charity', 'admin') NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status ENUM('pending', 'approved', 'suspended') DEFAULT 'pending'
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("Users table created successfully")

    # Create volunteers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS volunteers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        name VARCHAR(100) NOT NULL,
        gender ENUM('male', 'female', 'other'),
        total_hours FLOAT DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("Volunteers table created successfully")

    # Create charities table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS charities (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        name VARCHAR(100) NOT NULL,
        address VARCHAR(255),
        description TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("Charities table created successfully")

    # Create events table
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("Events table created successfully")

    # Create registrations table (volunteers registering for events)
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("Registrations table created successfully")

    # Create event files table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS event_files (
        id INT AUTO_INCREMENT PRIMARY KEY,
        event_id INT NOT NULL,
        filename VARCHAR(255) NOT NULL,
        original_filename VARCHAR(255) NOT NULL,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("Event files table created successfully")

    # Check if admin account already exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    admin = cursor.fetchone()

    if not admin:
        # Create admin account
        admin_password = generate_password_hash('admin123')
        cursor.execute("""
        INSERT INTO users (username, password, email, user_type, status)
        VALUES (%s, %s, %s, %s, %s)
        """, ('admin', admin_password, 'admin@example.com', 'admin', 'approved'))
        print("Admin account created successfully (Username: admin, Password: admin123)")

    # Create uploads folder
    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
        print(f"Upload folder created successfully: {upload_folder}")

    # Commit changes and close connection
    conn.commit()
    cursor.close()
    conn.close()

    print("Database setup completed")

if __name__ == "__main__":
    setup_database()
