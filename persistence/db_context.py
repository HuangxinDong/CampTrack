import sqlite3
import logging
import os
import sys
import shutil

class DBContext:
    def __init__(self, db_path=None):
        # Resolve DB path; when frozen (PyInstaller) copy bundled DB to a writable location.
        self.db_path = db_path or self._resolve_db_path()
        self._ensure_db_dir()
        self.initialize_db()

    def _resolve_db_path(self):
        default_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "camptrack.db"))

        if getattr(sys, "frozen", False):
            bundle_dir = getattr(sys, "_MEIPASS", os.getcwd())
            bundled_db = os.path.join(bundle_dir, "persistence", "data", "camptrack.db")
            user_db = os.path.abspath(os.path.join(os.getcwd(), "persistence", "data", "camptrack.db"))

            # If bundled DB exists and user DB missing, copy so we have writable storage.
            if os.path.exists(bundled_db) and not os.path.exists(user_db):
                os.makedirs(os.path.dirname(user_db), exist_ok=True)
                shutil.copy2(bundled_db, user_db)
            return user_db

        return default_path

    def _ensure_db_dir(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                role TEXT,
                enabled INTEGER DEFAULT 1,
                daily_payment_rate REAL
            )
        ''')

        # Camps
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS camps (
                camp_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                location TEXT,
                camp_type TEXT,
                start_date TEXT,
                end_date TEXT,
                camp_leader TEXT,
                food_per_camper_per_day INTEGER,
                initial_food_stock INTEGER,
                current_food_stock INTEGER,
                FOREIGN KEY (camp_leader) REFERENCES users(username)
            )
        ''')

        # Campers
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campers (
                camper_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                contact TEXT,
                medical_info TEXT
            )
        ''')

        # Camp-Campers (Many-to-Many)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS camp_campers (
                camp_id TEXT,
                camper_id TEXT,
                PRIMARY KEY (camp_id, camper_id),
                FOREIGN KEY (camp_id) REFERENCES camps(camp_id),
                FOREIGN KEY (camper_id) REFERENCES campers(camper_id)
            )
        ''')

        # Activity Library
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_library (
                name TEXT PRIMARY KEY,
                is_indoor INTEGER DEFAULT 0
            )
        ''')

        # Scheduled Activities
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camp_id TEXT,
                name TEXT,
                date TEXT,
                session TEXT,
                is_indoor INTEGER,
                FOREIGN KEY (camp_id) REFERENCES camps(camp_id)
            )
        ''')

        # Activity Attendance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_attendance (
                scheduled_activity_id INTEGER,
                camper_id TEXT,
                PRIMARY KEY (scheduled_activity_id, camper_id),
                FOREIGN KEY (scheduled_activity_id) REFERENCES scheduled_activities(id),
                FOREIGN KEY (camper_id) REFERENCES campers(camper_id)
            )
        ''')

        # Equipment
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipment (
                resource_id TEXT PRIMARY KEY,
                camp_id TEXT,
                name TEXT,
                target_quantity INTEGER,
                current_quantity INTEGER,
                condition TEXT,
                FOREIGN KEY (camp_id) REFERENCES camps(camp_id)
            )
        ''')

        # Messages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                from_user TEXT,
                to_user TEXT,
                content TEXT,
                sent_at TEXT,
                mark_as_read INTEGER DEFAULT 0,
                FOREIGN KEY (from_user) REFERENCES users(username),
                FOREIGN KEY (to_user) REFERENCES users(username)
            )
        ''')

        # Announcements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS announcements (
                announcement_id TEXT PRIMARY KEY,
                author TEXT,
                content TEXT,
                created_at TEXT,
                FOREIGN KEY (author) REFERENCES users(username)
            )
        ''')

        # System Notifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_notifications (
                sys_notification_id TEXT PRIMARY KEY,
                to_user TEXT,
                type TEXT,
                content TEXT,
                created_at TEXT,
                FOREIGN KEY (to_user) REFERENCES users(username)
            )
        ''')

        # Audit Logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                username TEXT,
                action TEXT,
                details TEXT
            )
        ''')

        # Daily Reports
        # Assuming daily reports are linked to a camp and have content
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_reports (
                report_id TEXT PRIMARY KEY,
                camp_id TEXT,
                date TEXT,
                content TEXT,
                created_at TEXT,
                FOREIGN KEY (camp_id) REFERENCES camps(camp_id)
            )
        ''')

        conn.commit()
        conn.close()
