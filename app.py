from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from database import init_db, get_db
from functools import wraps
from datetime import datetime, date
import sqlite3

app = Flask(__name__)
app.secret_key = 'your-secret-key-2024'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
CORS(app, supports_credentials=True)

# Initialize database
init_db()

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

# Login
@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    db = get_db()
    try:
        user = db.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, password)
        ).fetchone()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return jsonify({
                'success': True, 
                'role': user['role'],
                'username': user['username']
            })
        
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    finally:
        db.close()

# Sign Up
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    role = data.get('role', 'employee')
    
    db = get_db()
    try:
        db.execute(
            'INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)',
            (username, password, email, role)
        )
        db.commit()
        return jsonify({'success': True, 'message': 'User created successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Username or email already exists'}), 400
    finally:
        db.close()

# Employee Management
@app.route('/api/employees', methods=['POST', 'OPTIONS'])
@login_required
def add_employee():
    if request.method == 'OPTIONS':
        return '', 200
    
    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.json
    db = get_db()
    
    try:
        db.execute('''
            INSERT INTO employees (emp_id, name, email, department, position, phone, join_date, salary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['emp_id'], data['name'], data['email'], data['department'], 
              data['position'], data['phone'], data['join_date'], data['salary']))
        db.commit()
        return jsonify({'success': True, 'message': 'Employee added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

@app.route('/api/employees', methods=['GET', 'OPTIONS'])
@login_required
def get_employees():
    if request.method == 'OPTIONS':
        return '', 200
    
    db = get_db()
    try:
        employees = db.execute('SELECT * FROM employees ORDER BY id').fetchall()
        return jsonify([dict(emp) for emp in employees])
    finally:
        db.close()

@app.route('/api/employees/<emp_id>', methods=['PUT', 'OPTIONS'])
@login_required
def update_employee(emp_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.json
    db = get_db()
    
    try:
        db.execute('''
            UPDATE employees 
            SET name=?, email=?, department=?, position=?, phone=?, join_date=?, salary=?
            WHERE emp_id=?
        ''', (data['name'], data['email'], data['department'], data['position'],
              data['phone'], data['join_date'], data['salary'], emp_id))
        db.commit()
        return jsonify({'success': True, 'message': 'Employee updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

@app.route('/api/employees/<emp_id>', methods=['DELETE', 'OPTIONS'])
@login_required
def delete_employee(emp_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    db = get_db()
    try:
        db.execute('DELETE FROM employees WHERE emp_id=?', (emp_id,))
        db.commit()
        return jsonify({'success': True, 'message': 'Employee deleted successfully'})
    finally:
        db.close()

# ATTENDANCE MODULE
@app.route('/api/attendance', methods=['POST', 'OPTIONS'])
@login_required
def mark_attendance():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.json
    emp_id = data.get('emp_id')
    db = get_db()
    
    try:
        today = date.today().isoformat()
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # Check if already checked in today
        existing = db.execute(
            'SELECT * FROM attendance WHERE emp_id = ? AND date = ?',
            (emp_id, today)
        ).fetchone()
        
        if existing:
            if existing['check_out'] is None:
                # Update check-out time
                db.execute(
                    'UPDATE attendance SET check_out = ? WHERE emp_id = ? AND date = ?',
                    (current_time, emp_id, today)
                )
                db.commit()
                message = 'Check-out marked successfully!'
            else:
                message = 'Already checked out for today!'
        else:
            # Mark check-in
            db.execute(
                '''INSERT INTO attendance (emp_id, date, check_in, status) 
                   VALUES (?, ?, ?, ?)''',
                (emp_id, today, current_time, 'present')
            )
            db.commit()
            message = 'Check-in marked successfully!'
        
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

@app.route('/api/attendance/<emp_id>', methods=['GET', 'OPTIONS'])
@login_required
def get_attendance(emp_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    db = get_db()
    try:
        attendance = db.execute(
            '''SELECT * FROM attendance 
               WHERE emp_id = ? 
               ORDER BY date DESC 
               LIMIT 30''',
            (emp_id,)
        ).fetchall()
        return jsonify([dict(att) for att in attendance])
    finally:
        db.close()

# PERFORMANCE MODULE
@app.route('/api/performance', methods=['POST', 'OPTIONS'])
@login_required
def add_performance():
    if request.method == 'OPTIONS':
        return '', 200
    
    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.json
    db = get_db()
    
    try:
        db.execute('''
            INSERT INTO performance (emp_id, review_date, rating, comments, goals)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['emp_id'], data['review_date'], data['rating'], 
              data['comments'], data['goals']))
        db.commit()
        return jsonify({'success': True, 'message': 'Performance review added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

@app.route('/api/performance/<emp_id>', methods=['GET', 'OPTIONS'])
@login_required
def get_performance(emp_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    db = get_db()
    try:
        performance = db.execute(
            'SELECT * FROM performance WHERE emp_id = ? ORDER BY review_date DESC',
            (emp_id,)
        ).fetchall()
        return jsonify([dict(perf) for perf in performance])
    finally:
        db.close()

# SALARY MODULE
@app.route('/api/salary/<emp_id>', methods=['GET', 'OPTIONS'])
@login_required
def get_salary(emp_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    db = get_db()
    try:
        employee = db.execute(
            'SELECT name, emp_id, salary FROM employees WHERE emp_id = ?',
            (emp_id,)
        ).fetchone()
        
        if employee:
            return jsonify(dict(employee))
        return jsonify({'error': 'Employee not found'}), 404
    finally:
        db.close()

# EVENTS MODULE
@app.route('/api/events', methods=['GET', 'OPTIONS'])
@login_required
def get_events():
    if request.method == 'OPTIONS':
        return '', 200
    
    db = get_db()
    try:
        events = db.execute(
            '''SELECT * FROM events 
               WHERE event_date >= date('now') 
               ORDER BY event_date'''
        ).fetchall()
        return jsonify([dict(event) for event in events])
    finally:
        db.close()

@app.route('/api/events', methods=['POST', 'OPTIONS'])
@login_required
def add_event():
    if request.method == 'OPTIONS':
        return '', 200
    
    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.json
    db = get_db()
    
    try:
        db.execute('''
            INSERT INTO events (title, description, event_date, location, created_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['title'], data['description'], data['event_date'], 
              data['location'], session['username']))
        db.commit()
        return jsonify({'success': True, 'message': 'Event added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()

# Logout
@app.route('/api/logout', methods=['POST', 'OPTIONS'])
def logout():
    if request.method == 'OPTIONS':
        return '', 200
    
    session.clear()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='127.0.0.1')