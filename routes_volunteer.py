from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session
from models import User, Volunteer, Charity, Event, Registration, get_db_connection
from utils import volunteer_required, format_datetime
from datetime import datetime

volunteer = Blueprint('volunteer', __name__)

@volunteer.route('/dashboard')
@volunteer_required
def dashboard():
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 获取志愿者信息
    cursor.execute("SELECT * FROM volunteers WHERE user_id = %s", (user_id,))
    volunteer_data = cursor.fetchone()

    if not volunteer_data:
        flash('志愿者资料不存在', 'error')
        return redirect(url_for('main.index'))

    volunteer_id = volunteer_data['id']

    # 获取即将参加的活动
    cursor.execute("""
        SELECT e.*, r.status as registration_status, c.name as charity_name
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        JOIN charities c ON e.charity_id = c.id
        WHERE r.volunteer_id = %s AND e.start_time > NOW()
        ORDER BY e.start_time
        LIMIT 5
    """, (volunteer_id,))
    upcoming_events = cursor.fetchall()

    # 获取总活动数
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM registrations
        WHERE volunteer_id = %s
    """, (volunteer_id,))
    total_events = cursor.fetchone()['count']

    # 获取总志愿时间
    cursor.execute("""
        SELECT SUM(hours_contributed) as total_hours
        FROM registrations
        WHERE volunteer_id = %s AND status = 'completed'
    """, (volunteer_id,))
    result = cursor.fetchone()
    total_hours = result['total_hours'] if result['total_hours'] else 0

    cursor.close()
    conn.close()

    return render_template('volunteer/dashboard.html',
                          volunteer=volunteer_data,
                          upcoming_events=upcoming_events,
                          total_events=total_events,
                          total_hours=total_hours,
                          format_datetime=format_datetime)

@volunteer.route('/events')
@volunteer_required
def events():
    # 获取筛选参数
    location = request.args.get('location', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 构建查询
    query = """
        SELECT e.*, c.name as charity_name
        FROM events e
        JOIN charities c ON e.charity_id = c.id
        WHERE e.status = 'approved' AND e.start_time > NOW()
    """
    params = []

    if location:
        query += " AND e.location LIKE %s"
        params.append(f"%{location}%")

    if start_date:
        query += " AND e.start_time >= %s"
        params.append(start_date)

    if end_date:
        query += " AND e.start_time <= %s"
        params.append(end_date)

    query += " ORDER BY e.start_time"

    cursor.execute(query, params)
    events = cursor.fetchall()

    # 获取所有可用的位置（用于筛选）
    cursor.execute("""
        SELECT DISTINCT location
        FROM events
        WHERE status = 'approved' AND start_time > NOW()
    """)
    locations = [row['location'] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return render_template('volunteer/events.html',
                          events=events,
                          locations=locations,
                          current_location=location,
                          current_start_date=start_date,
                          current_end_date=end_date,
                          format_datetime=format_datetime)

@volunteer.route('/events/<int:event_id>')
@volunteer_required
def event_details(event_id):
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 获取活动详情
    cursor.execute("""
        SELECT e.*, c.name as charity_name, c.description as charity_description
        FROM events e
        JOIN charities c ON e.charity_id = c.id
        WHERE e.id = %s AND e.status = 'approved'
    """, (event_id,))
    event = cursor.fetchone()

    if not event:
        flash('活动不存在或未获批准', 'error')
        return redirect(url_for('volunteer.events'))

    # 检查用户是否已注册该活动
    cursor.execute("""
        SELECT r.*
        FROM registrations r
        JOIN volunteers v ON r.volunteer_id = v.id
        WHERE v.user_id = %s AND r.event_id = %s
    """, (user_id, event_id))
    registration = cursor.fetchone()

    is_registered = False
    registration_status = None
    if registration:
        is_registered = True
        registration_status = registration['status']

    cursor.close()
    conn.close()

    return render_template('volunteer/event_details.html',
                          event=event,
                          is_registered=is_registered,
                          registration_status=registration_status,
                          format_datetime=format_datetime)

@volunteer.route('/register_event/<int:event_id>', methods=['POST'])
@volunteer_required
def register_event(event_id):
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 获取志愿者ID
    cursor.execute("SELECT id FROM volunteers WHERE user_id = %s", (user_id,))
    volunteer_data = cursor.fetchone()

    if not volunteer_data:
        flash('志愿者资料不存在', 'error')
        return redirect(url_for('volunteer.events'))

    volunteer_id = volunteer_data['id']

    # 检查活动是否存在且已批准
    cursor.execute("""
        SELECT * FROM events
        WHERE id = %s AND status = 'approved' AND start_time > NOW()
    """, (event_id,))
    event = cursor.fetchone()

    if not event:
        flash('活动不存在、未获批准或已过期', 'error')
        return redirect(url_for('volunteer.events'))

    # 检查是否已注册
    cursor.execute("""
        SELECT * FROM registrations
        WHERE volunteer_id = %s AND event_id = %s
    """, (volunteer_id, event_id))
    existing_registration = cursor.fetchone()

    if existing_registration:
        flash('您已经注册了该活动', 'info')
        return redirect(url_for('volunteer.event_details', event_id=event_id))

    # 创建注册
    cursor.execute("""
        INSERT INTO registrations (volunteer_id, event_id, status)
        VALUES (%s, %s, 'pending')
    """, (volunteer_id, event_id))

    conn.commit()
    cursor.close()
    conn.close()

    flash('活动注册成功，请等待审核', 'success')
    return redirect(url_for('volunteer.event_details', event_id=event_id))

@volunteer.route('/cancel_registration/<int:event_id>', methods=['POST'])
@volunteer_required
def cancel_registration(event_id):
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 获取志愿者ID
    cursor.execute("SELECT id FROM volunteers WHERE user_id = %s", (user_id,))
    volunteer_data = cursor.fetchone()

    if not volunteer_data:
        flash('志愿者资料不存在', 'error')
        return redirect(url_for('volunteer.my_events'))

    volunteer_id = volunteer_data['id']

    # 检查注册是否存在
    cursor.execute("""
        SELECT r.*, e.start_time
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        WHERE r.volunteer_id = %s AND r.event_id = %s
    """, (volunteer_id, event_id))
    registration = cursor.fetchone()

    if not registration:
        flash('未找到该活动的注册记录', 'error')
        return redirect(url_for('volunteer.my_events'))

    # 检查活动是否已开始
    if registration['start_time'] < datetime.now():
        flash('活动已开始，无法取消注册', 'error')
        return redirect(url_for('volunteer.my_events'))

    # 删除注册
    cursor.execute("""
        DELETE FROM registrations
        WHERE volunteer_id = %s AND event_id = %s
    """, (volunteer_id, event_id))

    conn.commit()
    cursor.close()
    conn.close()

    flash('活动注册已取消', 'success')
    return redirect(url_for('volunteer.my_events'))

@volunteer.route('/my_events')
@volunteer_required
def my_events():
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 获取志愿者ID
    cursor.execute("SELECT id FROM volunteers WHERE user_id = %s", (user_id,))
    volunteer_data = cursor.fetchone()

    if not volunteer_data:
        flash('志愿者资料不存在', 'error')
        return redirect(url_for('main.index'))

    volunteer_id = volunteer_data['id']

    # 获取即将到来的活动
    cursor.execute("""
        SELECT e.*, r.status as registration_status, c.name as charity_name, r.id as registration_id
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        JOIN charities c ON e.charity_id = c.id
        WHERE r.volunteer_id = %s AND e.start_time > NOW()
        ORDER BY e.start_time
    """, (volunteer_id,))
    upcoming_events = cursor.fetchall()

    # 获取已完成的活动
    cursor.execute("""
        SELECT e.*, r.status as registration_status, c.name as charity_name,
               r.hours_contributed, r.id as registration_id
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        JOIN charities c ON e.charity_id = c.id
        WHERE r.volunteer_id = %s AND e.end_time < NOW()
        ORDER BY e.start_time DESC
    """, (volunteer_id,))
    past_events = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('volunteer/my_events.html',
                          upcoming_events=upcoming_events,
                          past_events=past_events,
                          format_datetime=format_datetime)

@volunteer.route('/profile')
@volunteer_required
def profile():
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 获取用户和志愿者信息
    cursor.execute("""
        SELECT u.*, v.*
        FROM users u
        JOIN volunteers v ON u.id = v.user_id
        WHERE u.id = %s
    """, (user_id,))
    profile_data = cursor.fetchone()

    cursor.close()
    conn.close()

    if not profile_data:
        flash('用户资料不存在', 'error')
        return redirect(url_for('main.index'))

    return render_template('volunteer/profile.html', profile=profile_data, format_datetime=format_datetime)

@volunteer.route('/update_profile', methods=['POST'])
@volunteer_required
def update_profile():
    user_id = session.get('user_id')

    name = request.form.get('name')
    gender = request.form.get('gender')
    email = request.form.get('email')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 获取用户和志愿者信息
    cursor.execute("""
        SELECT u.*, v.id as volunteer_id
        FROM users u
        JOIN volunteers v ON u.id = v.user_id
        WHERE u.id = %s
    """, (user_id,))
    user_data = cursor.fetchone()

    if not user_data:
        flash('用户资料不存在', 'error')
        return redirect(url_for('volunteer.profile'))

    # 更新基本信息
    cursor.execute("""
        UPDATE volunteers
        SET name = %s, gender = %s
        WHERE id = %s
    """, (name, gender, user_data['volunteer_id']))

    cursor.execute("""
        UPDATE users
        SET email = %s
        WHERE id = %s
    """, (email, user_id))

    # 如果提供了密码，则更新密码
    if current_password and new_password and confirm_password:
        # 验证当前密码
        user = User.get_by_id(user_id)
        if not user.check_password(current_password):
            flash('当前密码不正确', 'error')
            return redirect(url_for('volunteer.profile'))

        # 验证新密码
        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'error')
            return redirect(url_for('volunteer.profile'))

        # 更新密码
        user.set_password(new_password)
        cursor.execute("""
            UPDATE users
            SET password = %s
            WHERE id = %s
        """, (user.password_hash, user_id))

    conn.commit()
    cursor.close()
    conn.close()

    flash('个人资料已更新', 'success')
    return redirect(url_for('volunteer.profile'))
