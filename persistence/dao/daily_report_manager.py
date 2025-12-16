import json
import logging
from datetime import datetime
from persistence.db_context import DBContext


class DailyReportManager:
    """SQLite-backed daily reports with JSON payload stored in content column."""

    def __init__(self, db_context=None):
        self.db = db_context or DBContext()

    def _serialize(self, report_dict):
        return json.dumps(report_dict, ensure_ascii=False)

    def _deserialize(self, content):
        try:
            return json.loads(content)
        except Exception:
            return {"content": content}

    def read_all(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT report_id, camp_id, date, content, created_at FROM daily_reports ORDER BY date DESC"
            )
            rows = cursor.fetchall()
            reports = []
            for row in rows:
                payload = self._deserialize(row[3])
                payload.update(
                    {
                        "report_id": row[0],
                        "camp_id": row[1],
                        "date": row[2],
                        "created_at": row[4],
                    }
                )
                reports.append(payload)
            return reports
        except Exception as exc:
            logging.error(f"Error reading daily reports: {exc}")
            return []
        finally:
            conn.close()

    def save_all(self, reports):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM daily_reports")
            for report in reports:
                cursor.execute(
                    "INSERT INTO daily_reports (report_id, camp_id, date, content, created_at) VALUES (?, ?, ?, ?, ?)",
                    (
                        report.get("report_id") or report.get("id"),
                        report.get("camp_id"),
                        report.get("date"),
                        self._serialize(report),
                        report.get("created_at") or datetime.now().isoformat(),
                    ),
                )
            conn.commit()
        except Exception as exc:
            logging.error(f"Error saving daily reports: {exc}")
            raise
        finally:
            conn.close()

    def add_report(self, report_dict):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO daily_reports (report_id, camp_id, date, content, created_at) VALUES (?, ?, ?, ?, ?)",
                (
                    report_dict.get("report_id") or report_dict.get("id"),
                    report_dict.get("camp_id"),
                    report_dict.get("date"),
                    self._serialize(report_dict),
                    report_dict.get("created_at") or datetime.now().isoformat(),
                ),
            )
            conn.commit()
        except Exception as exc:
            logging.error(f"Error adding daily report: {exc}")
            raise
        finally:
            conn.close()



    



