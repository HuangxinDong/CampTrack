import json
import logging
import os
import sys
from datetime import datetime

# Ensure project root is on sys.path when running as a script
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from persistence.db_context import DBContext


def _camp_exists(conn, camp_id):
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM camps WHERE camp_id = ?", (camp_id,))
    return cursor.fetchone() is not None

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

DATA_DIR = os.path.join("persistence", "data")


def _load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        logging.warning("Missing %s, skipping", path)
        return None
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as exc:
            logging.error("Invalid JSON in %s: %s", path, exc)
            return None


def seed_users(conn):
    rows = _load_json("users.json")
    if not rows:
        return
    cursor = conn.cursor()
    inserted = 0
    for u in rows:
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO users (username, password, role, enabled, daily_payment_rate)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    u.get("username"),
                    u.get("password", ""),
                    u.get("role"),
                    1 if u.get("enabled", True) else 0,
                    u.get("daily_payment_rate"),
                ),
            )
            inserted += 1
        except Exception as exc:
            logging.error("Failed to insert user %s: %s", u.get("username"), exc)
    conn.commit()
    logging.info("Seeded users: %d", inserted)


def seed_activity_library(conn):
    data = _load_json("activities.json")
    if data is None:
        return
    cursor = conn.cursor()
    cursor.execute("DELETE FROM activity_library")
    inserted = 0
    if isinstance(data, list):
        iterable = [(name, False) for name in data]
    elif isinstance(data, dict):
        iterable = [(name, meta.get("is_indoor", False)) for name, meta in data.items()]
    else:
        logging.warning("activities.json format unexpected, skipping")
        return
    for name, is_indoor in iterable:
        try:
            cursor.execute(
                "INSERT OR REPLACE INTO activity_library (name, is_indoor) VALUES (?, ?)",
                (name, 1 if is_indoor else 0),
            )
            inserted += 1
        except Exception as exc:
            logging.error("Failed to insert activity %s: %s", name, exc)
    conn.commit()
    logging.info("Seeded activities: %d", inserted)


def seed_camps(conn):
    camps = _load_json("camps.json")
    if not camps:
        return

    cursor = conn.cursor()
    inserted = 0
    for camp in camps:
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO camps (camp_id, name, location, camp_type, start_date, end_date, camp_leader,
                                             food_per_camper_per_day, initial_food_stock, current_food_stock)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    camp.get("camp_id"),
                    camp.get("name"),
                    camp.get("location"),
                    camp.get("camp_type"),
                    camp.get("start_date"),
                    camp.get("end_date"),
                    camp.get("camp_leader"),
                    camp.get("food_per_camper_per_day", 1),
                    camp.get("initial_food_stock", 0),
                    camp.get("current_food_stock", camp.get("initial_food_stock", 0)),
                ),
            )

            # Campers
            campers = camp.get("campers", [])
            name_to_id = {}
            for camper in campers:
                cursor.execute(
                    "INSERT OR REPLACE INTO campers (camper_id, name, age, contact, medical_info) VALUES (?, ?, ?, ?, ?)",
                    (
                        camper.get("camper_id"),
                        camper.get("name"),
                        camper.get("age"),
                        camper.get("contact"),
                        camper.get("medical_info"),
                    ),
                )
                name_to_id[camper.get("name")] = camper.get("camper_id")
                cursor.execute(
                    "INSERT OR REPLACE INTO camp_campers (camp_id, camper_id) VALUES (?, ?)",
                    (camp.get("camp_id"), camper.get("camper_id")),
                )

            # Equipment
            for eq in camp.get("equipment", []):
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO equipment (resource_id, camp_id, name, target_quantity, current_quantity, condition)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        eq.get("resource_id"),
                        camp.get("camp_id"),
                        eq.get("name"),
                        eq.get("target_quantity"),
                        eq.get("current_quantity"),
                        eq.get("condition"),
                    ),
                )

            # Activities (scheduled)
            for act in camp.get("activities", []):
                cursor.execute(
                    "INSERT INTO scheduled_activities (camp_id, name, date, session, is_indoor) VALUES (?, ?, ?, ?, ?)",
                    (
                        camp.get("camp_id"),
                        act.get("name"),
                        act.get("date"),
                        act.get("session", "Morning"),
                        1 if act.get("is_indoor") else 0,
                    ),
                )
                act_id = cursor.lastrowid
                for camper_key in act.get("camper_ids", []):
                    camper_id = name_to_id.get(camper_key, camper_key)
                    cursor.execute(
                        "INSERT OR IGNORE INTO activity_attendance (scheduled_activity_id, camper_id) VALUES (?, ?)",
                        (act_id, camper_id),
                    )

            inserted += 1
        except Exception as exc:
            logging.error("Failed to insert camp %s: %s", camp.get("name"), exc)

    conn.commit()
    logging.info("Seeded camps: %d", inserted)


def seed_announcements(conn):
    rows = _load_json("announcements.json")
    if not rows:
        return
    cursor = conn.cursor()
    inserted = 0
    for a in rows:
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO announcements (announcement_id, author, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    a.get("announcement_id"),
                    a.get("author"),
                    a.get("content"),
                    a.get("created_at"),
                ),
            )
            inserted += 1
        except Exception as exc:
            logging.error("Failed to insert announcement %s: %s", a.get("announcement_id"), exc)
    conn.commit()
    logging.info("Seeded announcements: %d", inserted)


def seed_messages(conn):
    rows = _load_json("messages.json")
    if not rows:
        return
    cursor = conn.cursor()
    inserted = 0
    for m in rows:
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO messages (message_id, from_user, to_user, content, sent_at, mark_as_read)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    m.get("message_id"),
                    m.get("from_user"),
                    m.get("to_user"),
                    m.get("content"),
                    m.get("sent_at"),
                    1 if m.get("mark_as_read", False) else 0,
                ),
            )
            inserted += 1
        except Exception as exc:
            logging.error("Failed to insert message %s: %s", m.get("message_id"), exc)
    conn.commit()
    logging.info("Seeded messages: %d", inserted)


def seed_system_notifications(conn):
    rows = _load_json("system_notifications.json")
    if not rows:
        return
    cursor = conn.cursor()
    inserted = 0
    for n in rows:
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO system_notifications (sys_notification_id, to_user, type, content, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    n.get("sys_notification_id"),
                    n.get("to_user"),
                    n.get("type"),
                    n.get("content"),
                    n.get("created_at"),
                ),
            )
            inserted += 1
        except Exception as exc:
            logging.error("Failed to insert system notification %s: %s", n.get("sys_notification_id"), exc)
    conn.commit()
    logging.info("Seeded system notifications: %d", inserted)


def seed_audit_logs(conn):
    rows = _load_json("audit_logs.json")
    if not rows:
        return
    cursor = conn.cursor()
    inserted = 0
    for log in rows:
        try:
            cursor.execute(
                """
                INSERT INTO audit_logs (timestamp, username, action, details)
                VALUES (?, ?, ?, ?)
                """,
                (
                    log.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    log.get("username"),
                    log.get("action"),
                    log.get("details", ""),
                ),
            )
            inserted += 1
        except Exception as exc:
            logging.error("Failed to insert audit log: %s", exc)
    conn.commit()
    logging.info("Seeded audit logs: %d", inserted)


def seed_daily_reports(conn):
    rows = _load_json("daily_reports.json")
    if not rows:
        return
    cursor = conn.cursor()
    inserted = 0
    for r in rows:
        camp_id = r.get("camp_id")
        if camp_id and not _camp_exists(conn, camp_id):
            logging.warning("Skip daily report %s: camp %s missing", r.get("report_id"), camp_id)
            continue
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO daily_reports (report_id, camp_id, date, content, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    r.get("report_id"),
                    camp_id,
                    r.get("date"),
                    r.get("content"),
                    r.get("created_at"),
                ),
            )
            inserted += 1
        except Exception as exc:
            logging.error("Failed to insert daily report %s: %s", r.get("report_id"), exc)
    conn.commit()
    logging.info("Seeded daily reports: %d", inserted)


def main():
    db = DBContext()
    conn = db.get_connection()
    try:
        seed_camps(conn)
        seed_users(conn)
        seed_activity_library(conn)
        seed_announcements(conn)
        seed_messages(conn)
        seed_system_notifications(conn)
        seed_audit_logs(conn)
        seed_daily_reports(conn)
        logging.info("Seeding complete.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
