import sqlite3
from datetime import datetime, date

def init_db():
    conn = sqlite3.connect('employee_system.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT DEFAULT 'employee',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Employees table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT,
            position TEXT,
            phone TEXT,
            join_date DATE,
            salary REAL,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    # Attendance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT NOT NULL,
            date DATE NOT NULL,
            check_in TIME,
            check_out TIME,
            status TEXT DEFAULT 'present',
            FOREIGN KEY (emp_id) REFERENCES employees(emp_id),
            UNIQUE(emp_id, date)
        )
    ''')
    
    # Performance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT NOT NULL,
            review_date DATE NOT NULL,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            comments TEXT,
            goals TEXT,
            FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
        )
    ''')
    
    # Events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            event_date DATE NOT NULL,
            location TEXT,
            created_by TEXT
        )
    ''')
    
    # Insert admin user
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (username, password, email, role)
            VALUES (?, ?, ?, ?)
        ''', ('admin', 'admin123', 'admin@company.com', 'admin'))
    
    # Insert sample events
    cursor.execute("SELECT * FROM events LIMIT 1")
    if not cursor.fetchone():
        sample_events = [
            ('Annual Company Meeting', 'Yearly meeting with all staff', 
             datetime.now().strftime('%Y-%m-%d'), 'Conference Hall', 'admin'),
            ('Team Building Workshop', 'Fun activities for team bonding', 
             (date.today().replace(day=15) if date.today().day < 15 else 
              date.today().replace(month=date.today().month+1, day=15)).isoformat(), 
             'City Park', 'admin'),
            ('Technical Training', 'Advanced Python training session', 
             (date.today().replace(day=20) if date.today().day < 20 else 
              date.today().replace(month=date.today().month+1, day=20)).isoformat(), 
             'Training Room', 'admin')
        ]
        cursor.executemany('''
            INSERT INTO events (title, description, event_date, location, created_by)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_events)
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('employee_system.db', timeout=10)
    conn.row_factory = sqlite3.Row
    return conn