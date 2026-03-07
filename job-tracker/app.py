from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
from database import get_db, init_db
from datetime import datetime
import sqlite3
from scheduler import start_scheduler
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import csv
import io
from flask import make_response
app = Flask(__name__)
CORS(app)
app.secret_key = 'your-secret-key-change-this-in-production'

# Initialize database on first run
init_db()

# Start reminder scheduler
scheduler = start_scheduler()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form.get('email', '')
        password = request.form['password']
        confirm = request.form['confirm_password']
        
        if password != confirm:
            return render_template('register.html', error='Passwords do not match')
        
        conn = get_db()
        
        # Check if username exists
        existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            conn.close()
            return render_template('register.html', error='Username already exists')
        
        # Create user
        hashed_password = generate_password_hash(password)
        conn.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                     (username, hashed_password, email))
        conn.commit()
        conn.close()
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Dashboard - shows all applications"""
    conn = get_db()
    applications = conn.execute('''
        SELECT * FROM applications 
        WHERE user_id = ?
        ORDER BY date_applied DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('index.html', applications=applications)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_application():
    """Add new job application"""
    if request.method == 'POST':
        data = request.form
        
        conn = get_db()
        conn.execute('''
            INSERT INTO applications 
            (user_id, company, position, location, date_applied, status, deadline, job_url, salary_range, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            data['company'],
            data['position'],
            data.get('location', ''),
            data['date_applied'],
            'Applied',
            data.get('deadline', None),
            data.get('job_url', ''),
            data.get('salary_range', ''),
            data.get('notes', '')
        ))
        conn.commit()
        conn.close()
        
        return redirect(url_for('index'))
    
    return render_template('add.html')

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_application(id):
    """Delete an application"""
    conn = get_db()
    conn.execute('DELETE FROM applications WHERE id = ? AND user_id = ?', (id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/status/<int:id>', methods=['POST'])
@login_required
def change_status(id):
    """Change application status"""
    new_status = request.json.get('status')
    
    conn = get_db()
    
    # Get old status
    old = conn.execute('SELECT status FROM applications WHERE id = ? AND user_id = ?', 
                       (id, session['user_id'])).fetchone()
    old_status = old['status'] if old else None
    
    # Update status
    conn.execute('UPDATE applications SET status = ?, updated_at = ? WHERE id = ? AND user_id = ?',
                 (new_status, datetime.now(), id, session['user_id']))
    
    # Record in history
    conn.execute('''
        INSERT INTO status_history (application_id, old_status, new_status)
        VALUES (?, ?, ?)
    ''', (id, old_status, new_status))
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success'})

@app.route('/analytics')
@login_required
def analytics():
    """Analytics dashboard"""
    return render_template('analytics.html')

@app.route('/api/analytics/status')
@login_required
def analytics_status():
    """Get status breakdown for pie chart"""
    conn = get_db()
    results = conn.execute('''
        SELECT status, COUNT(*) as count 
        FROM applications 
        WHERE user_id = ?
        GROUP BY status
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    labels = [r['status'] for r in results]
    values = [r['count'] for r in results]
    
    return jsonify({'labels': labels, 'values': values})

@app.route('/api/analytics/timeline')
@login_required
def analytics_timeline():
    """Get applications over time for line chart"""
    conn = get_db()
    results = conn.execute('''
        SELECT date_applied, COUNT(*) as count
        FROM applications
        WHERE user_id = ?
        GROUP BY date_applied
        ORDER BY date_applied
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    dates = [r['date_applied'] for r in results]
    counts = [r['count'] for r in results]
    
    return jsonify({'dates': dates, 'counts': counts})

@app.route('/api/analytics/stats')
@login_required
def analytics_stats():
    """Get overall statistics"""
    conn = get_db()
    
    total = conn.execute('SELECT COUNT(*) as count FROM applications WHERE user_id = ?', 
                         (session['user_id'],)).fetchone()['count']
    
    responses = conn.execute('''
        SELECT COUNT(*) as count FROM applications 
        WHERE user_id = ? AND status != 'Applied' AND status != 'Ghosted'
    ''', (session['user_id'],)).fetchone()['count']
    
    response_rate = round((responses / total * 100) if total > 0 else 0, 1)
    
    conn.close()
    
    return jsonify({
        'total': total,
        'responses': responses,
        'response_rate': response_rate
    })

@app.route('/export')
@login_required
def export_csv():
    """Export applications to CSV"""
    conn = get_db()
    applications = conn.execute('''
        SELECT company, position, location, date_applied, status, deadline, salary_range, notes
        FROM applications 
        WHERE user_id = ?
        ORDER BY date_applied DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Company', 'Position', 'Location', 'Date Applied', 'Status', 'Deadline', 'Salary Range', 'Notes'])
    
    # Write data
    for app in applications:
        writer.writerow([
            app['company'],
            app['position'],
            app['location'] or '',
            app['date_applied'],
            app['status'],
            app['deadline'] or '',
            app['salary_range'] or '',
            app['notes'] or ''
        ])
    
    # Create response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=job_applications.csv'
    response.headers['Content-Type'] = 'text/csv'
    
    return response

if __name__ == '__main__':
    app.run(debug=True, port=5000)