from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from models import User, Volunteer, Charity, Event, Registration, get_db_connection
from utils import format_datetime
from werkzeug.security import check_password_hash

main = Blueprint('main', __name__)

# 首页路由
@main.route('/')
def index():
    # 获取已批准的活动
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.*, c.name as charity_name 
        FROM events e
        JOIN charities c ON e.charity_id = c.id
        WHERE e.status = 'approved' AND e.start_time > NOW()
        ORDER BY e.start_time
        LIMIT 6
    """)
    upcoming_events = cursor.fetchall()
    
    # 获取特色慈善机构
    cursor.execute("""
        SELECT c.*, COUNT(e.id) as event_count
        FROM charities c
        LEFT JOIN events e ON c.id = e.charity_id AND e.status = 'approved'
        JOIN users u ON c.user_id = u.id
        WHERE u.status = 'approved'
        GROUP BY c.id
        ORDER BY event_count DESC
        LIMIT 3
    """)
    featured_charities = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('index.html', 
                          upcoming_events=upcoming_events,
                          featured_charities=featured_charities,
                          format_datetime=format_datetime)

# 登录路由
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.get_by_username(username)
        
        if user and check_password_hash(user.password_hash, password):
            if user.status != 'approved':
                flash('您的账户尚未被批准或已被暂停', 'error')
                return redirect(url_for('main.login'))
                
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_type'] = user.user_type
            
            if user.user_type == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.user_type == 'volunteer':
                return redirect(url_for('volunteer.dashboard'))
            elif user.user_type == 'charity':
                return redirect(url_for('charity.dashboard'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

# 管理员登录路由
@main.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.get_by_username(username)
        
        if user and user.user_type == 'admin' and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_type'] = user.user_type
            return redirect(url_for('admin.dashboard'))
        else:
            flash('管理员用户名或密码错误', 'error')
    
    return render_template('admin/login.html')

# 志愿者注册路由
@main.route('/register/volunteer', methods=['GET', 'POST'])
def register_volunteer():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        name = request.form.get('name')
        gender = request.form.get('gender')
        
        # 验证密码
        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return redirect(url_for('main.register_volunteer'))
        
        # 检查用户名和邮箱是否已存在
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        existing_user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if existing_user:
            flash('用户名或邮箱已被使用', 'error')
            return redirect(url_for('main.register_volunteer'))
        
        # 创建用户
        user = User(username=username, email=email, user_type='volunteer', status='approved')
        user.set_password(password)
        user_id = user.save()
        
        # 创建志愿者资料
        volunteer = Volunteer(user_id=user_id, name=name, gender=gender)
        volunteer.save()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register_volunteer.html')

# 慈善机构注册路由
@main.route('/register/charity', methods=['GET', 'POST'])
def register_charity():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        name = request.form.get('name')
        address = request.form.get('address')
        description = request.form.get('description')
        
        # 验证密码
        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return redirect(url_for('main.register_charity'))
        
        # 检查用户名和邮箱是否已存在
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        existing_user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if existing_user:
            flash('用户名或邮箱已被使用', 'error')
            return redirect(url_for('main.register_charity'))
        
        # 创建用户
        user = User(username=username, email=email, user_type='charity', status='pending')
        user.set_password(password)
        user_id = user.save()
        
        # 创建慈善机构资料
        charity = Charity(user_id=user_id, name=name, address=address, description=description)
        charity.save()
        
        flash('注册成功，请等待管理员审核', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register_charity.html')

# 登出路由
@main.route('/logout')
def logout():
    session.clear()
    flash('您已成功登出', 'success')
    return redirect(url_for('main.index'))

# 活动详情路由
@main.route('/event/<int:event_id>')
def event_details(event_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.*, c.name as charity_name 
        FROM events e
        JOIN charities c ON e.charity_id = c.id
        WHERE e.id = %s AND e.status = 'approved'
    """, (event_id,))
    event = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not event:
        flash('活动不存在或未获批准', 'error')
        return redirect(url_for('main.index'))
    
    # 检查用户是否已注册该活动
    is_registered = False
    if 'user_id' in session and session['user_type'] == 'volunteer':
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT r.* FROM registrations r
            JOIN volunteers v ON r.volunteer_id = v.id
            WHERE v.user_id = %s AND r.event_id = %s
        """, (session['user_id'], event_id))
        registration = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if registration:
            is_registered = True
    
    return render_template('event_details.html', 
                          event=event, 
                          is_registered=is_registered,
                          format_datetime=format_datetime)

# 错误处理
@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@main.app_errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
