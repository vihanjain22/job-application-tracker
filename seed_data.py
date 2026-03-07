from database import get_db
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

def seed_database():
    """Add realistic dummy data for demo purposes"""
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Create demo user
    hashed_password = generate_password_hash('demo123')
    cursor.execute('INSERT OR IGNORE INTO users (username, password, email) VALUES (?, ?, ?)',
                   ('demo', hashed_password, 'demo@example.com'))
    conn.commit()
    
    # Get user ID
    user = cursor.execute('SELECT id FROM users WHERE username = ?', ('demo',)).fetchone()
    user_id = user['id']
    
    # Sample applications data
    companies = [
        ('Google', 'Software Engineer', 'Mountain View, CA', '$120k - $180k'),
        ('Microsoft', 'Cloud Solutions Architect', 'Seattle, WA', '$130k - $190k'),
        ('Amazon', 'Backend Developer', 'Seattle, WA', '$110k - $160k'),
        ('Meta', 'Frontend Engineer', 'Menlo Park, CA', '$125k - $185k'),
        ('Apple', 'iOS Developer', 'Cupertino, CA', '$115k - $170k'),
        ('Netflix', 'Data Engineer', 'Los Gatos, CA', '$140k - $200k'),
        ('Salesforce', 'Full Stack Developer', 'San Francisco, CA', '$110k - $165k'),
        ('Adobe', 'Software Engineer', 'San Jose, CA', '$105k - $155k'),
        ('Uber', 'Backend Engineer', 'San Francisco, CA', '$120k - $175k'),
        ('Airbnb', 'Product Engineer', 'San Francisco, CA', '$125k - $180k'),
        ('Tesla', 'Embedded Systems Engineer', 'Palo Alto, CA', '$110k - $160k'),
        ('LinkedIn', 'Software Engineer', 'Sunnyvale, CA', '$115k - $170k'),
        ('Twitter', 'Full Stack Engineer', 'San Francisco, CA', '$110k - $165k'),
        ('Stripe', 'Backend Developer', 'San Francisco, CA', '$130k - $190k'),
        ('Dropbox', 'Software Engineer', 'San Francisco, CA', '$120k - $175k')
    ]
    
    statuses = ['Applied', 'Interviewing', 'Offer', 'Rejected', 'Ghosted']
    
    # Add applications over past 2 months
    base_date = datetime.now() - timedelta(days=60)
    
    for i, (company, position, location, salary) in enumerate(companies):
        # Spread applications over time
        days_offset = i * 4
        date_applied = (base_date + timedelta(days=days_offset)).date().isoformat()
        
        # Set deadline 1-2 weeks after application
        deadline_offset = random.randint(7, 14)
        deadline = (base_date + timedelta(days=days_offset + deadline_offset)).date().isoformat()
        
        # Assign realistic statuses based on time
        if i < 3:
            status = 'Offer'
        elif i < 6:
            status = 'Interviewing'
        elif i < 10:
            status = 'Applied'
        else:
            status = random.choice(['Rejected', 'Ghosted'])
        
        notes = f"Applied through company website. Referral from {random.choice(['John', 'Sarah', 'Mike', 'Lisa', 'Alex'])}."
        
        cursor.execute('''
            INSERT INTO applications 
            (user_id, company, position, location, date_applied, status, deadline, salary_range, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, company, position, location, date_applied, status, deadline, salary, notes))
    
    conn.commit()
    conn.close()
    
    print("✅ Database seeded with 15 sample applications")
    print("Demo credentials:")
    print("  Username: demo")
    print("  Password: demo123")

if __name__ == '__main__':
    seed_database()