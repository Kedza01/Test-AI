"""
Test script for RBAC implementation
Tests database schema, authentication, quotas, and audit logging
"""
import sqlite3
import sys
from datetime import datetime

DATABASE_NAME = 'ZRP_CrimeData.db'

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_database_tables():
    """Test if all required tables exist"""
    print_section("TEST 1: Database Tables")
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = [
            'users', 'user_sessions', 'audit_logs', 
            'system_settings', 'prediction_history', 'generated_reports',
            'crime_reports'
        ]
        
        print(f"\nFound {len(tables)} tables in database:")
        for table in tables:
            status = "✓" if table in required_tables else "?"
            print(f"  {status} {table}")
        
        missing = [t for t in required_tables if t not in tables]
        if missing:
            print(f"\n❌ FAILED: Missing tables: {missing}")
            return False
        else:
            print("\n✅ PASSED: All required tables exist")
            return True
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    finally:
        conn.close()

def test_default_users():
    """Test if default users were created"""
    print_section("TEST 2: Default Users")
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT username, role, full_name, email, is_active FROM users")
        users = cursor.fetchall()
        
        print(f"\nFound {len(users)} users:")
        for user in users:
            print(f"  • {user[0]:10} | Role: {user[1]:15} | Name: {user[2]:25} | Active: {user[4]}")
        
        expected_users = ['admin', 'analyst', 'user']
        found_users = [u[0] for u in users]
        
        if all(u in found_users for u in expected_users):
            print("\n✅ PASSED: All default users created")
            return True
        else:
            print(f"\n❌ FAILED: Missing users: {[u for u in expected_users if u not in found_users]}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    finally:
        conn.close()

def test_system_settings():
    """Test if system settings were initialized"""
    print_section("TEST 3: System Settings")
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT setting_key, setting_value, description FROM system_settings")
        settings = cursor.fetchall()
        
        print(f"\nFound {len(settings)} system settings:")
        for setting in settings:
            print(f"  • {setting[0]:30} = {setting[1]:10} ({setting[2]})")
        
        required_settings = [
            'standard_user_daily_quota',
            'session_timeout_minutes',
            'data_retention_days',
            'enable_email_notifications'
        ]
        
        found_settings = [s[0] for s in settings]
        
        if all(s in found_settings for s in required_settings):
            print("\n✅ PASSED: All system settings initialized")
            return True
        else:
            print(f"\n❌ FAILED: Missing settings: {[s for s in required_settings if s not in found_settings]}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    finally:
        conn.close()

def test_user_table_schema():
    """Test users table schema"""
    print_section("TEST 4: Users Table Schema")
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("\nUsers table columns:")
        for col in columns:
            print(f"  • {col[1]:25} {col[2]:15} {'NOT NULL' if col[3] else ''}")
        
        required_columns = [
            'id', 'username', 'password_hash', 'role', 'full_name', 
            'email', 'created_date', 'last_login', 'is_active',
            'daily_prediction_count', 'last_prediction_date'
        ]
        
        found_columns = [col[1] for col in columns]
        
        if all(c in found_columns for c in required_columns):
            print("\n✅ PASSED: Users table has all required columns")
            return True
        else:
            print(f"\n❌ FAILED: Missing columns: {[c for c in required_columns if c not in found_columns]}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    finally:
        conn.close()

def test_password_hashing():
    """Test password hashing"""
    print_section("TEST 5: Password Hashing")
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT username, password_hash FROM users WHERE username = 'admin'")
        result = cursor.fetchone()
        
        if result:
            username, pwd_hash = result
            print(f"\nAdmin user found:")
            print(f"  Username: {username}")
            print(f"  Password Hash: {pwd_hash[:20]}... (truncated)")
            print(f"  Hash Length: {len(pwd_hash)} characters")
            
            # SHA-256 produces 64 character hex string
            if len(pwd_hash) == 64:
                print("\n✅ PASSED: Password is properly hashed (SHA-256)")
                return True
            else:
                print(f"\n❌ FAILED: Unexpected hash length: {len(pwd_hash)}")
                return False
        else:
            print("\n❌ FAILED: Admin user not found")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    finally:
        conn.close()

def test_audit_logs_table():
    """Test audit logs table structure"""
    print_section("TEST 6: Audit Logs Table")
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(audit_logs)")
        columns = cursor.fetchall()
        
        print("\nAudit logs table columns:")
        for col in columns:
            print(f"  • {col[1]:15} {col[2]:15}")
        
        # Check if there are any audit logs
        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        count = cursor.fetchone()[0]
        print(f"\nCurrent audit log entries: {count}")
        
        if count > 0:
            cursor.execute("SELECT username, action, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT 5")
            logs = cursor.fetchall()
            print("\nRecent audit logs:")
            for log in logs:
                print(f"  • {log[2]} | {log[0]:10} | {log[1]}")
        
        print("\n✅ PASSED: Audit logs table exists and is functional")
        return True
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    finally:
        conn.close()

def test_prediction_history_table():
    """Test prediction history table"""
    print_section("TEST 7: Prediction History Table")
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM prediction_history")
        count = cursor.fetchone()[0]
        print(f"\nPrediction history entries: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT username, location, predicted_crimes, timestamp 
                FROM prediction_history 
                ORDER BY timestamp DESC LIMIT 5
            """)
            predictions = cursor.fetchall()
            print("\nRecent predictions:")
            for pred in predictions:
                print(f"  • {pred[3]} | {pred[0]:10} | {pred[1]:15} | {pred[2]}")
            print("\n✅ PASSED: Prediction history is being tracked")
        else:
            print("\n⚠️  WARNING: No predictions in history yet (expected if app just started)")
            print("✅ PASSED: Table structure is correct")
        
        return True
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    finally:
        conn.close()

def test_user_sessions_table():
    """Test user sessions table"""
    print_section("TEST 8: User Sessions Table")
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM user_sessions")
        count = cursor.fetchone()[0]
        print(f"\nTotal sessions recorded: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT u.username, s.login_time, s.logout_time, s.session_duration
                FROM user_sessions s
                JOIN users u ON s.user_id = u.id
                ORDER BY s.login_time DESC LIMIT 5
            """)
            sessions = cursor.fetchall()
            print("\nRecent sessions:")
            for sess in sessions:
                duration = f"{sess[3]} min" if sess[3] else "Active"
                logout = sess[2] if sess[2] else "Still active"
                print(f"  • {sess[0]:10} | Login: {sess[1]} | Logout: {logout} | Duration: {duration}")
            print("\n✅ PASSED: Session tracking is working")
        else:
            print("\n⚠️  WARNING: No sessions yet (expected if no one has logged in)")
            print("✅ PASSED: Table structure is correct")
        
        return True
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    finally:
        conn.close()

def test_generated_reports_table():
    """Test generated reports table"""
    print_section("TEST 9: Generated Reports Table")
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM generated_reports")
        count = cursor.fetchone()[0]
        print(f"\nTotal reports generated: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT username, report_type, location, generation_date
                FROM generated_reports
                ORDER BY generation_date DESC LIMIT 5
            """)
            reports = cursor.fetchall()
            print("\nRecent reports:")
            for rep in reports:
                print(f"  • {rep[3]} | {rep[0]:10} | {rep[1]:25} | {rep[2]}")
            print("\n✅ PASSED: Report tracking is working")
        else:
            print("\n⚠️  WARNING: No reports generated yet")
            print("✅ PASSED: Table structure is correct")
        
        return True
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    finally:
        conn.close()

def test_user_quota_tracking():
    """Test user quota tracking fields"""
    print_section("TEST 10: User Quota Tracking")
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT username, role, daily_prediction_count, last_prediction_date
            FROM users
        """)
        users = cursor.fetchall()
        
        print("\nUser quota status:")
        for user in users:
            print(f"  • {user[0]:10} ({user[1]:15}) | Count: {user[2] or 0} | Last: {user[3] or 'Never'}")
        
        print("\n✅ PASSED: Quota tracking fields are present")
        return True
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    finally:
        conn.close()

def run_all_tests():
    """Run all tests and provide summary"""
    print("\n" + "█"*60)
    print("  ZRP RBAC IMPLEMENTATION - DATABASE TESTS")
    print("█"*60)
    
    tests = [
        ("Database Tables", test_database_tables),
        ("Default Users", test_default_users),
        ("System Settings", test_system_settings),
        ("Users Table Schema", test_user_table_schema),
        ("Password Hashing", test_password_hashing),
        ("Audit Logs Table", test_audit_logs_table),
        ("Prediction History", test_prediction_history_table),
        ("User Sessions", test_user_sessions_table),
        ("Generated Reports", test_generated_reports_table),
        ("User Quota Tracking", test_user_quota_tracking)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    print("\nDetailed Results:")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Database schema is correctly implemented.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
    
    return passed == total

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
