from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session
from models import User, Volunteer, Charity, Event, Registration, get_db_connection
from utils import admin_required, format_datetime
from datetime import datetime

admin = Blueprint('admin', __name__)

@admin.route('/dashboard')
@admin_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 获取统计数据
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE user_type = 'volunteer'")
    volunteer_count = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM users WHERE user_type = 'charity'")
    charity_count = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM events")
    event_count = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM registrations")
    registration_count = cursor.fetchone()['count']

    # 获取最新活动
    cursor.execute("""
        SELECT e.*, c.name as charity_name
        FROM events e
        JOIN charities c ON e.charity_id = c.id
        ORDER BY e.created_at DESC
        LIMIT 5
    """)
    latest_events = cursor.fetchall()

    # 获取待审批的慈善机构
    cursor.execute("""
        SELECT u.*, c.name as charity_name
        FROM users u
        JOIN charities c ON u.id = c.user_id
        WHERE u.user_type = 'charity' AND u.status = 'pending'
        ORDER BY u.created_at DESC
    """)
    pending_charities = cursor.fetchall()

    # 获取待审批的活动
    cursor.execute("""
        SELECT e.*, c.name as charity_name
        FROM events e
        JOIN charities c ON e.charity_id = c.id
        WHERE e.status = 'pending'
        ORDER BY e.created_at DESC
    """)
    pending_events = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin/dashboard.html',
                          volunteer_count=volunteer_count,
                          charity_count=charity_count,
                          event_count=event_count,
                          registration_count=registration_count,
                          latest_events=latest_events,
                          pending_charities=pending_charities,
                          pending_events=pending_events,
                          format_datetime=format_datetime)

@admin.route('/users')
@admin_required
def user_management():
    user_type = request.args.get('type', 'all')
    status = request.args.get('status', 'all')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM users WHERE 1=1"
    params = []

    if user_type != 'all':
        query += " AND user_type = %s"
        params.append(user_type)

    if status != 'all':
        query += " AND status = %s"
        params.append(status)

    query += " ORDER BY created_at DESC"

    cursor.execute(query, params)
    users = cursor.fetchall()

    # 获取额外信息
    for user in users:
        if user['user_type'] == 'volunteer':
            cursor.execute("SELECT * FROM volunteers WHERE user_id = %s", (user['id'],))
            volunteer_data = cursor.fetchone()
            if volunteer_data:
                user['profile_name'] = volunteer_data['name']
        elif user['user_type'] == 'charity':
            cursor.execute("SELECT * FROM charities WHERE user_id = %s", (user['id'],))
            charity_data = cursor.fetchone()
            if charity_data:
                user['profile_name'] = charity_data['name']

    cursor.close()
    conn.close()

    return render_template('admin/user_management.html',
                          users=users,
                          current_type=user_type,
                          current_status=status,
                          format_datetime=format_datetime)

@admin.route('/users/update_status', methods=['POST'])
@admin_required
def update_user_status():
    user_id = request.form.get('user_id')
    new_status = request.form.get('status')

    if not user_id or not new_status:
        flash('缺少必要参数', 'error')
        return redirect(url_for('admin.user_management'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = %s WHERE id = %s", (new_status, user_id))
    conn.commit()
    cursor.close()
    conn.close()

    flash('用户状态已更新', 'success')
    return redirect(url_for('admin.user_management'))

@admin.route('/events')
@admin_required
def event_approval():
    status = request.args.get('status', 'pending')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT e.*, c.name as charity_name
        FROM events e
        JOIN charities c ON e.charity_id = c.id
    """

    params = []
    if status != 'all':
        query += " WHERE e.status = %s"
        params.append(status)

    query += " ORDER BY e.created_at DESC"

    cursor.execute(query, params)
    events = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin/event_approval.html',
                          events=events,
                          current_status=status,
                          format_datetime=format_datetime,
                          now=datetime.now())

@admin.route('/events/update_status', methods=['POST'])
@admin_required
def update_event_status():
    event_id = request.form.get('event_id')
    new_status = request.form.get('status')

    if not event_id or not new_status:
        flash('缺少必要参数', 'error')
        return redirect(url_for('admin.event_approval'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE events SET status = %s WHERE id = %s", (new_status, event_id))
    conn.commit()
    cursor.close()
    conn.close()

    flash('活动状态已更新', 'success')
    return redirect(url_for('admin.event_approval'))

@admin.route('/statistics')
@admin_required
def statistics():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 获取用户增长统计
    cursor.execute("""
        SELECT DATE_FORMAT(created_at, '%Y-%m') as month,
               COUNT(*) as count,
               user_type
        FROM users
        GROUP BY month, user_type
        ORDER BY month
    """)
    user_growth = cursor.fetchall()

    # 获取活动统计
    cursor.execute("""
        SELECT DATE_FORMAT(created_at, '%Y-%m') as month,
               COUNT(*) as count,
               status
        FROM events
        GROUP BY month, status
        ORDER BY month
    """)
    event_stats = cursor.fetchall()

    # 获取注册统计
    cursor.execute("""
        SELECT DATE_FORMAT(registered_at, '%Y-%m') as month,
               COUNT(*) as count
        FROM registrations
        GROUP BY month
        ORDER BY month
    """)
    registration_stats = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin/statistics.html',
                          user_growth=user_growth,
                          event_stats=event_stats,
                          registration_stats=registration_stats,
                          format_datetime=format_datetime)
