from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import mysql.connector

# 创建数据库连接池
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",
        database="charity_platform",
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci"
    )

class User:
    def __init__(self, id=None, username=None, email=None, password=None, user_type=None, status='pending', created_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password
        self.user_type = user_type
        self.status = status
        self.created_at = created_at or datetime.now()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_by_id(cls, user_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if user_data:
            return cls(**user_data)
        return None

    @classmethod
    def get_by_username(cls, username):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if user_data:
            return cls(**user_data)
        return None

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()

        if self.id:
            # 更新现有用户
            cursor.execute("""
                UPDATE users
                SET username = %s, email = %s, password = %s, user_type = %s, status = %s
                WHERE id = %s
            """, (self.username, self.email, self.password_hash, self.user_type, self.status, self.id))
        else:
            # 创建新用户
            cursor.execute("""
                INSERT INTO users (username, email, password, user_type, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.username, self.email, self.password_hash, self.user_type, self.status))
            self.id = cursor.lastrowid

        conn.commit()
        cursor.close()
        conn.close()
        return self.id


class Volunteer:
    def __init__(self, id=None, user_id=None, name=None, gender=None, total_hours=0):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.gender = gender
        self.total_hours = total_hours

    @classmethod
    def get_by_user_id(cls, user_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM volunteers WHERE user_id = %s", (user_id,))
        volunteer_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if volunteer_data:
            return cls(**volunteer_data)
        return None

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()

        if self.id:
            # 更新现有志愿者
            cursor.execute("""
                UPDATE volunteers
                SET name = %s, gender = %s, total_hours = %s
                WHERE id = %s
            """, (self.name, self.gender, self.total_hours, self.id))
        else:
            # 创建新志愿者
            cursor.execute("""
                INSERT INTO volunteers (user_id, name, gender, total_hours)
                VALUES (%s, %s, %s, %s)
            """, (self.user_id, self.name, self.gender, self.total_hours))
            self.id = cursor.lastrowid

        conn.commit()
        cursor.close()
        conn.close()
        return self.id


class Charity:
    def __init__(self, id=None, user_id=None, name=None, address=None, description=None):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.address = address
        self.description = description

    @classmethod
    def get_by_user_id(cls, user_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM charities WHERE user_id = %s", (user_id,))
        charity_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if charity_data:
            return cls(**charity_data)
        return None

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()

        if self.id:
            # 更新现有慈善机构
            cursor.execute("""
                UPDATE charities
                SET name = %s, address = %s, description = %s
                WHERE id = %s
            """, (self.name, self.address, self.description, self.id))
        else:
            # 创建新慈善机构
            cursor.execute("""
                INSERT INTO charities (user_id, name, address, description)
                VALUES (%s, %s, %s, %s)
            """, (self.user_id, self.name, self.address, self.description))
            self.id = cursor.lastrowid

        conn.commit()
        cursor.close()
        conn.close()
        return self.id


class Event:
    def __init__(self, id=None, charity_id=None, name=None, description=None, location=None,
                 start_time=None, end_time=None, required_skills=None, status='pending', created_at=None):
        self.id = id
        self.charity_id = charity_id
        self.name = name
        self.description = description
        self.location = location
        self.start_time = start_time
        self.end_time = end_time
        self.required_skills = required_skills
        self.status = status
        self.created_at = created_at or datetime.now()

    @classmethod
    def get_by_id(cls, event_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
        event_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if event_data:
            return cls(**event_data)
        return None

    @classmethod
    def get_all_approved(cls):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM events WHERE status = 'approved' ORDER BY start_time")
        events_data = cursor.fetchall()
        cursor.close()
        conn.close()

        return [cls(**event) for event in events_data]

    @classmethod
    def get_by_charity_id(cls, charity_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM events WHERE charity_id = %s ORDER BY created_at DESC", (charity_id,))
        events_data = cursor.fetchall()
        cursor.close()
        conn.close()

        return [cls(**event) for event in events_data]

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()

        if self.id:
            # 更新现有活动
            cursor.execute("""
                UPDATE events
                SET charity_id = %s, name = %s, description = %s, location = %s,
                    start_time = %s, end_time = %s, required_skills = %s, status = %s
                WHERE id = %s
            """, (self.charity_id, self.name, self.description, self.location,
                  self.start_time, self.end_time, self.required_skills, self.status, self.id))
        else:
            # 创建新活动
            cursor.execute("""
                INSERT INTO events (charity_id, name, description, location, start_time, end_time, required_skills, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (self.charity_id, self.name, self.description, self.location,
                  self.start_time, self.end_time, self.required_skills, self.status))
            self.id = cursor.lastrowid

        conn.commit()
        cursor.close()
        conn.close()
        return self.id


class Registration:
    def __init__(self, id=None, volunteer_id=None, event_id=None, status='pending',
                 registered_at=None, hours_contributed=0):
        self.id = id
        self.volunteer_id = volunteer_id
        self.event_id = event_id
        self.status = status
        self.registered_at = registered_at or datetime.now()
        self.hours_contributed = hours_contributed

    @classmethod
    def get_by_volunteer_and_event(cls, volunteer_id, event_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM registrations
            WHERE volunteer_id = %s AND event_id = %s
        """, (volunteer_id, event_id))
        registration_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if registration_data:
            return cls(**registration_data)
        return None

    @classmethod
    def get_by_volunteer_id(cls, volunteer_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT r.*, e.name as event_name, e.start_time, e.end_time, e.location
            FROM registrations r
            JOIN events e ON r.event_id = e.id
            WHERE r.volunteer_id = %s
            ORDER BY e.start_time
        """, (volunteer_id,))
        registrations_data = cursor.fetchall()
        cursor.close()
        conn.close()

        return registrations_data

    @classmethod
    def get_by_event_id(cls, event_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT r.*, v.name as volunteer_name, u.email
            FROM registrations r
            JOIN volunteers v ON r.volunteer_id = v.id
            JOIN users u ON v.user_id = u.id
            WHERE r.event_id = %s
            ORDER BY r.registered_at
        """, (event_id,))
        registrations_data = cursor.fetchall()
        cursor.close()
        conn.close()

        return registrations_data

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()

        if self.id:
            # 更新现有注册
            cursor.execute("""
                UPDATE registrations
                SET status = %s, hours_contributed = %s
                WHERE id = %s
            """, (self.status, self.hours_contributed, self.id))
        else:
            # 创建新注册
            cursor.execute("""
                INSERT INTO registrations (volunteer_id, event_id, status, hours_contributed)
                VALUES (%s, %s, %s, %s)
            """, (self.volunteer_id, self.event_id, self.status, self.hours_contributed))
            self.id = cursor.lastrowid

        conn.commit()
        cursor.close()
        conn.close()
        return self.id

    def delete(self):
        if not self.id:
            return False

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM registrations WHERE id = %s", (self.id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
