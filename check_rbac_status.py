"""
Quick script to check RBAC status and recent activity
Run this after testing the application to see the results
"""
import sqlite3
from datetime import datetime

DATABASE_NAME = 'ZRP_CrimeData.db'

def check_status():
    print("\n" + "="*70)
    print("  ZRP RBAC SYSTEM - CURRENT STATUS")
    print("="*70)
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # 1. User Status
        print("\n📊 USER STATUS:")
        cursor.execute("""
            SELECT username, role, daily_prediction_count, last_prediction_date, last_login
            FROM users
            ORDER BY role, username
        """)
        users = cursor.fetchall()
        for user in users:
            print(f"  • {user[0]:10} ({user[1]:15}) | Predictions: {user[2] or 0:2} | Last: {user[3] or 'Never':10} | Login: {user[4] or 'Never'}")
        
        # 2. Recent Audit Logs
        print("\n📝 RECENT AUDIT LOGS (Last 10):")
        cursor.execute("""
            SELECT timestamp, username, action, details
            FROM audit_logs
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        logs = cursor.fetchall()
        if logs:
            for log in logs:
                print(f"  • {log[0]} | {log[1]:10} | {log[2]:20} | {log[3] or ''}")
        else:
            print("  (No audit logs yet)")
        
        # 3. Active Sessions
        print("\n🔐 ACTIVE SESSIONS:")
        cursor.execute("""
            SELECT u.username, s.login_time, s.id
            FROM user_sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.logout_time IS NULL
            ORDER BY s.login_time DESC
        """)
        active = cursor.fetchall()
        if active:
            for sess in active:
                print(f"  • {sess[0]:10} | Logged in at: {sess[1]} | Session ID: {sess[2]}")
        else:
            print("  (No active sessions)")
        
        # 4. Recent Sessions
        print("\n📅 RECENT SESSIONS (Last 5):")
        cursor.execute("""
            SELECT u.username, s.login_time, s.logout_time, s.session_duration
            FROM user_sessions s
            JOIN users u ON s.user_id = u.id
            ORDER BY s.login_time DESC
            LIMIT 5
        """)
        sessions = cursor.fetchall()
        if sessions:
            for sess in sessions:
                duration = f"{sess[3]} min" if sess[3] else "Active"
                logout = sess[2] if sess[2] else "Still active"
                print(f"  • {sess[0]:10} | In: {sess[1]} | Out: {logout} | Duration: {duration}")
        else:
            print("  (No sessions yet)")
        
        # 5. Prediction History
        print("\n🎯 PREDICTION HISTORY (Last 5):")
        cursor.execute("""
            SELECT username, location, predicted_crimes, timestamp
            FROM prediction_history
            ORDER BY timestamp DESC
            LIMIT 5
        """)
        predictions = cursor.fetchall()
        if predictions:
            for pred in predictions:
                crimes = pred[2][:50] + "..." if len(pred[2]) > 50 else pred[2]
                print(f"  • {pred[3]} | {pred[0]:10} | {pred[1]:15} | {crimes}")
        else:
            print("  (No predictions yet)")
        
        # 6. Generated Reports
        print("\n📄 GENERATED REPORTS (Last 5):")
        cursor.execute("""
            SELECT username, report_type, location, generation_date
            FROM generated_reports
            ORDER BY generation_date DESC
            LIMIT 5
        """)
        reports = cursor.fetchall()
        if reports:
            for rep in reports:
                print(f"  • {rep[3]} | {rep[0]:10} | {rep[1]:30} | {rep[2]}")
        else:
            print("  (No reports generated yet)")
        
        # 7. System Settings
        print("\n⚙️  SYSTEM SETTINGS:")
        cursor.execute("SELECT setting_key, setting_value FROM system_settings")
        settings = cursor.fetchall()
        for setting in settings:
            print(f"  • {setting[0]:30} = {setting[1]}")
        
        print("\n" + "="*70)
        print("  Status check complete!")
        print("="*70 + "\n")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == '__main__':
    check_status()
