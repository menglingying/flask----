from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session, current_app
from models import User, Volunteer, Charity, Event, Registration, get_db_connection
from utils import charity_required, save_file, format_datetime
from datetime import datetime
import os

charity = Blueprint('charity', __name__)

@charity.route('/dashboard')
@charity_required
def dashboard():
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 获取慈善机构信息
    cursor.execute("SELECT * FROM charities WHERE user_id = %s", (user_id,))
    charity_data = cursor.fetchone()

    if not charity_data:
        flash('慈善机构资料不存在', 'error')
        return redirect(url_for('main.index'))

    charity_id = charity_data['id']

    # 获取即将到来的活动
    cursor.execute("""
        SELECT e.*,
               (SELECT COUNT(*) FROM registrations r WHERE r.event_id = e.id) as registration_count
        FROM events e
        WHERE e.charity_id = %s AND e.start_time > NOW() AND e.status = 'approved'
        ORDER BY e.start_time
        LIMIT 5
    """, (charity_id,))
    upcoming_events = cursor.fetchall()

    # 获取总活动数
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM events
        WHERE charity_id = %s
    """, (charity_id,))
    total_events = cursor.fetchone()['count']

    # 获取总志愿者数
    cursor.execute("""
        SELECT COUNT(DISTINCT r.volunteer_id) as count
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        WHERE e.charity_id = %s AND r.status = 'approved'
    """, (charity_id,))
    total_volunteers = cursor.fetchone()['count']

    # 获取待审核的志愿者申请
    cursor.execute("""
        SELECT r.*, v.name as volunteer_name, e.name as event_name
        FROM registrations r
        JOIN volunteers v ON r.volunteer_id = v.id
        JOIN events e ON r.event_id = e.id
        WHERE e.charity_id = %s AND r.status = 'pending'
        ORDER BY r.registered_at DESC
        LIMIT 5
    """, (charity_id,))
    pending_applications = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('charity/dashboard.html',
                          charity=charity_data,
                          upcoming_events=upcoming_events,
                          total_events=total_events,
                          total_volunteers=total_volunteers,
                          pending_applications=pending_applications,
                          format_datetime=format_datetime)

@charity.route('/create_event', methods=['GET', 'POST'])
@charity_required
def create_event():
    if request.method == 'POST':
        user_id = session.get('user_id')

        name = request.form.get('name')
        description = request.form.get('description')
        location = request.form.get('location')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        required_skills = request.form.get('required_skills')

        # 验证必填字段
        if not all([name, description, location, start_time, end_time]):
            flash('请填写所有必填字段', 'error')
            return redirect(url_for('charity.create_event'))

        # 验证时间
        try:
            start_datetime = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
            end_datetime = datetime.strptime(end_time, '%Y-%m-%dT%H:%M')

            if start_datetime >= end_datetime:
                flash('结束时间必须晚于开始时间', 'error')
                return redirect(url_for('charity.create_event'))

            if start_datetime < datetime.now():
                flash('开始时间不能早于当前时间', 'error')
                return redirect(url_for('charity.create_event'))
        except ValueError:
            flash('日期格式无效', 'error')
            return redirect(url_for('charity.create_event'))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 获取慈善机构ID
        cursor.execute("SELECT id FROM charities WHERE user_id = %s", (user_id,))
        charity_data = cursor.fetchone()

        if not charity_data:
            flash('慈善机构资料不存在', 'error')
            return redirect(url_for('main.index'))

        charity_id = charity_data['id']

        # 创建活动
        cursor.execute("""
            INSERT INTO events (charity_id, name, description, location, start_time, end_time, required_skills, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
        """, (charity_id, name, description, location, start_time, end_time, required_skills))

        conn.commit()

        # 处理文件上传
        event_id = cursor.lastrowid
        if 'files' in request.files:
            files = request.files.getlist('files')
            for file in files:
                if file.filename:
                    filename = save_file(file)
                    if filename:
                        # 保存文件关联
                        cursor.execute("""
                            INSERT INTO event_files (event_id, filename, original_filename)
                            VALUES (%s, %s, %s)
                        """, (event_id, filename, file.filename))

        conn.commit()
        cursor.close()
        conn.close()

        flash('活动创建成功，请等待管理员审核', 'success')
        return redirect(url_for('charity.events'))

    return render_template('charity/create_event.html')

@charity.route('/events')
@charity_required
def events():
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 获取慈善机构ID
    cursor.execute("SELECT id FROM charities WHERE user_id = %s", (user_id,))
    charity_data = cursor.fetchone()

    if not charity_data:
        flash('慈善机构资料不存在', 'error')
        return redirect(url_for('main.index'))

    charity_id = charity_data['id']

    # 获取所有活动
    cursor.execute("""
        SELECT e.*,
               (SELECT COUNT(*) FROM registrations r WHERE r.event_id = e.id) as registration_count
        FROM events e
        WHERE e.charity_id = %s
        ORDER BY e.created_at DESC
    """, (charity_id,))
    events = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('charity/events.html',
                          events=events,
                          format_datetime=format_datetime)

@charity.route('/events/<int:event_id>')
@charity_required
def event_details(event_id):
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 获取慈善机构ID
    cursor.execute("SELECT id FROM charities WHERE user_id = %s", (user_id,))
    charity_data = cursor.fetchone()

    if not charity_data:
        flash('慈善机构资料不存在', 'error')
        return redirect(url_for('main.index'))

    charity_id = charity_data['id']

    # 获取活动详情
    cursor.execute("""
        SELECT * FROM events
        WHERE id = %s AND charity_id = %s
    """, (event_id, charity_id))
    event = cursor.fetchone()

    if not event:
        flash('活动不存在或无权访问', 'error')
        return redirect(url_for('charity.events'))

    # 获取注册的志愿者
    cursor.execute("""
        SELECT r.*, v.name as volunteer_name, u.email
        FROM registrations r
        JOIN volunteers v ON r.volunteer_id = v.id
        JOIN users u ON v.user_id = u.id
        WHERE r.event_id = %s
        ORDER BY r.registered_at
    """, (event_id,))
    registrations = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('charity/event_details.html',
                          event=event,
                          registrations=registrations,
                          format_datetime=format_datetime)

@charity.route('/update_event/<int:event_id>', methods=['GET', 'POST'])
@charity_required
def update_event(event_id):
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 获取慈善机构ID
    cursor.execute("SELECT id FROM charities WHERE user_id = %s", (user_id,))
    charity_data = cursor.fetchone()

    if not charity_data:
        flash('慈善机构资料不存在', 'error')
        return redirect(url_for('main.index'))

    charity_id = charity_data['id']

    # 获取活动详情
    cursor.execute("""
        SELECT * FROM events
        WHERE id = %s AND charity_id = %s
    """, (event_id, charity_id))
    event = cursor.fetchone()

    if not event:
        flash('活动不存在或无权访问', 'error')
        return redirect(url_for('charity.events'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        location = request.form.get('location')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        required_skills = request.form.get('required_skills')

        # 验证必填字段
        if not all([name, description, location, start_time, end_time]):
            flash('请填写所有必填字段', 'error')
            return redirect(url_for('charity.update_event', event_id=event_id))

        # 验证时间
        try:
            start_datetime = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
            end_datetime = datetime.strptime(end_time, '%Y-%m-%dT%H:%M')

            if start_datetime >= end_datetime:
                flash('结束时间必须晚于开始时间', 'error')
                return redirect(url_for('charity.update_event', event_id=event_id))
        except ValueError:
            flash('日期格式无效', 'error')
            return redirect(url_for('charity.update_event', event_id=event_id))

        # 更新活动
        cursor.execute("""
            UPDATE events
            SET name = %s, description = %s, location = %s, start_time = %s, end_time = %s, required_skills = %s
            WHERE id = %s AND charity_id = %s
        """, (name, description, location, start_time, end_time, required_skills, event_id, charity_id))

        conn.commit()

        # 处理文件上传
        if 'files' in request.files:
            files = request.files.getlist('files')
            for file in files:
                if file.filename:
                    filename = save_file(file)
                    if filename:
                        # 保存文件关联
                        cursor.execute("""
                            INSERT INTO event_files (event_id, filename, original_filename)
                            VALUES (%s, %s, %s)
                        """, (event_id, filename, file.filename))

        conn.commit()
        cursor.close()
        conn.close()

        flash('活动更新成功', 'success')
        return redirect(url_for('charity.event_details', event_id=event_id))

    return render_template('charity/update_event.html', event=event, format_datetime=format_datetime)

@charity.route('/delete_event/<int:event_id>', methods=['POST'])
@charity_required
def delete_event(event_id):
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 获取慈善机构ID
    cursor.execute("SELECT id FROM charities WHERE user_id = %s", (user_id,))
    charity_data = cursor.fetchone()

    if not charity_data:
        flash('慈善机构资料不存在', 'error')
        return redirect(url_for('main.index'))

    charity_id = charity_data['id']

    # 检查活动是否存在且属于该慈善机构
    cursor.execute("""
        SELECT * FROM events
        WHERE id = %s AND charity_id = %s
    """, (event_id, charity_id))
    event = cursor.fetchone()

    if not event:
        flash('活动不存在或无权访问', 'error')
        return redirect(url_for('charity.events'))

    # 删除活动
    cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
    conn.commit()

    cursor.close()
    conn.close()

    flash('活动已删除', 'success')
    return redirect(url_for('charity.events'))

@charity.route('/volunteers')
@charity_required
def volunteers():
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 获取慈善机构ID
    cursor.execute("SELECT id FROM charities WHERE user_id = %s", (user_id,))
    charity_data = cursor.fetchone()

    if not charity_data:
        flash('慈善机构资料不存在', 'error')
        return redirect(url_for('main.index'))

    charity_id = charity_data['id']

    # 获取所有申请
    cursor.execute("""
        SELECT r.*, v.name as volunteer_name, u.email, e.name as event_name
        FROM registrations r
        JOIN volunteers v ON r.volunteer_id = v.id
        JOIN users u ON v.user_id = u.id
        JOIN events e ON r.event_id = e.id
        WHERE e.charity_id = %s
        ORDER BY r.registered_at DESC
    """, (charity_id,))
    applications = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('charity/volunteers.html',
                          applications=applications,
                          format_datetime=format_datetime)

@charity.route('/approve_volunteer/<int:registration_id>', methods=['POST'])
@charity_required
def approve_volunteer(registration_id):
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 获取慈善机构ID
    cursor.execute("SELECT id FROM charities WHERE user_id = %s", (user_id,))
    charity_data = cursor.fetchone()

    if not charity_data:
        flash('慈善机构资料不存在', 'error')
        return redirect(url_for('main.index'))

    charity_id = charity_data['id']

    # 检查注册是否存在且属于该慈善机构的活动
    cursor.execute("""
        SELECT r.*
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        WHERE r.id = %s AND e.charity_id = %s
    """, (registration_id, charity_id))
    registration = cursor.fetchone()

    if not registration:
        flash('申请不存在或无权访问', 'error')
        return redirect(url_for('charity.volunteers'))

    # 更新注册状态
    cursor.execute("""
        UPDATE registrations
        SET status = 'approved'
        WHERE id = %s
    """, (registration_id,))

    conn.commit()
    cursor.close()
    conn.close()

    flash('志愿者申请已批准', 'success')
    return redirect(url_for('charity.volunteers'))

@charity.route('/reject_volunteer/<int:registration_id>', methods=['POST'])
@charity_required
def reject_volunteer(registration_id):
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 获取慈善机构ID
    cursor.execute("SELECT id FROM charities WHERE user_id = %s", (user_id,))
    charity_data = cursor.fetchone()

    if not charity_data:
        flash('慈善机构资料不存在', 'error')
        return redirect(url_for('main.index'))

    charity_id = charity_data['id']

    # 检查注册是否存在且属于该慈善机构的活动
    cursor.execute("""
        SELECT r.*
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        WHERE r.id = %s AND e.charity_id = %s
    """, (registration_id, charity_id))
    registration = cursor.fetchone()

    if not registration:
        flash('申请不存在或无权访问', 'error')
        return redirect(url_for('charity.volunteers'))

    # 更新注册状态
    cursor.execute("""
        UPDATE registrations
        SET status = 'rejected'
        WHERE id = %s
    """, (registration_id,))

    conn.commit()
    cursor.close()
    conn.close()

    flash('志愿者申请已拒绝', 'success')
    return redirect(url_for('charity.volunteers'))

@charity.route('/profile')
@charity_required
def profile():
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 获取用户和慈善机构信息
    cursor.execute("""
        SELECT u.*, c.*
        FROM users u
        JOIN charities c ON u.id = c.user_id
        WHERE u.id = %s
    """, (user_id,))
    profile_data = cursor.fetchone()

    cursor.close()
    conn.close()

    if not profile_data:
        flash('用户资料不存在', 'error')
        return redirect(url_for('main.index'))

    return render_template('charity/profile.html', profile=profile_data, format_datetime=format_datetime)

@charity.route('/update_profile', methods=['POST'])
@charity_required
def update_profile():
    user_id = session.get('user_id')

    name = request.form.get('name')
    address = request.form.get('address')
    description = request.form.get('description')
    email = request.form.get('email')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 获取用户和慈善机构信息
    cursor.execute("""
        SELECT u.*, c.id as charity_id
        FROM users u
        JOIN charities c ON u.id = c.user_id
        WHERE u.id = %s
    """, (user_id,))
    user_data = cursor.fetchone()

    if not user_data:
        flash('用户资料不存在', 'error')
        return redirect(url_for('charity.profile'))

    # 更新基本信息
    cursor.execute("""
        UPDATE charities
        SET name = %s, address = %s, description = %s
        WHERE id = %s
    """, (name, address, description, user_data['charity_id']))

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
            return redirect(url_for('charity.profile'))

        # 验证新密码
        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'error')
            return redirect(url_for('charity.profile'))

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

    flash('机构资料已更新', 'success')
    return redirect(url_for('charity.profile'))
