from apscheduler.schedulers.background import BackgroundScheduler
from database import get_db
from datetime import datetime, date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def check_reminders():
    """Check for reminders due today and send emails"""
    print(f"[REMINDER] Checking reminders at {datetime.now()}")
    
    conn = get_db()
    
    # Get applications with deadlines today that haven't been reminded
    today = date.today().isoformat()
    
    results = conn.execute('''
        SELECT a.id, a.company, a.position, a.deadline
        FROM applications a
        LEFT JOIN reminders r ON a.id = r.application_id AND r.reminder_date = ?
        WHERE a.deadline = ? AND (r.sent IS NULL OR r.sent = 0)
    ''', (today, today)).fetchall()
    
    if not results:
        print("[REMINDER] No reminders to send today")
        conn.close()
        return
    
    # Send email for each reminder
    for app in results:
        send_reminder_email(app['company'], app['position'], app['deadline'])
        
        # Mark as sent
        conn.execute('''
            INSERT OR REPLACE INTO reminders (application_id, reminder_date, sent)
            VALUES (?, ?, 1)
        ''', (app['id'], today))
    
    conn.commit()
    conn.close()
    print(f"[REMINDER] Sent {len(results)} reminders")

def send_reminder_email(company, position, deadline):
    """Send email reminder"""
    try:
        sender = os.getenv('EMAIL_USER')
        password = os.getenv('EMAIL_PASS')
        recipient = os.getenv('RECIPIENT_EMAIL')
        
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = f'Job Application Reminder - {company}'
        
        body = f"""
Hello,

This is a reminder about your job application:

Company: {company}
Position: {position}
Deadline: {deadline}

Don't forget to follow up!

Best regards,
Job Tracker
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        
        print(f"[EMAIL] Sent reminder for {company}")
        
    except Exception as e:
        print(f"[EMAIL] Failed to send: {e}")

def start_scheduler():
    """Start the background scheduler"""
    scheduler = BackgroundScheduler()
    
    # Check for reminders every day at 9 AM
    scheduler.add_job(check_reminders, 'cron', hour=9, minute=0)
    
    # For testing: also check every 5 minutes
    # scheduler.add_job(check_reminders, 'interval', minutes=5)
    
    scheduler.start()
    print("[SCHEDULER] Reminder scheduler started")
    
    return scheduler