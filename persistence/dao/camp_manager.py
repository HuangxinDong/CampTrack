from datetime import datetime
import logging
import numpy as np
import pandas as pd
from models.activity import Activity, Session
from models.camp import Camp
from models.camper import Camper
from models.resource import Equipment
from persistence.db_context import DBContext


class CampManager:
    """SQLite-backed camp persistence."""

    def __init__(self, db_context=None):
        self.db = db_context or DBContext()

    def read_all(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM camps")
            camp_rows = cursor.fetchall()
            camps = [self._build_camp_from_row(cursor, row) for row in camp_rows]
            return camps
        except Exception as exc:
            logging.error(f"Error reading camps: {exc}")
            return []
        finally:
            conn.close()

    def find_camp(self, name: str):
        """Find a camp by name (case-sensitive)."""
        camps = self.read_all()
        for camp in camps:
            if camp.name == name:
                return camp
        return None

    def _build_camp_from_row(self, cursor, row):
        camp_id = row[0]

        cursor.execute(
            """
            SELECT c.camper_id, c.name, c.age, c.contact, c.medical_info
            FROM campers c
            JOIN camp_campers cc ON c.camper_id = cc.camper_id
            WHERE cc.camp_id = ?
            """,
            (camp_id,)
        )
        camper_rows = cursor.fetchall()
        campers = [Camper(name=r[1], age=r[2], contact=r[3], medical_info=r[4]) for r in camper_rows]
        for idx, camper in enumerate(campers):
            camper.camper_id = camper_rows[idx][0]

        cursor.execute(
            "SELECT id, name, date, session, is_indoor FROM scheduled_activities WHERE camp_id = ?",
            (camp_id,)
        )
        activity_rows = cursor.fetchall()
        activities = []
        for act_row in activity_rows:
            act_id = act_row[0]
            cursor.execute(
                "SELECT camper_id FROM activity_attendance WHERE scheduled_activity_id = ?",
                (act_id,)
            )
            attendees = [a[0] for a in cursor.fetchall()]

            session_enum = Session.Morning
            try:
                session_enum = Session[act_row[3]]
            except Exception:
                pass

            activity = Activity(
                name=act_row[1],
                date=act_row[2],
                session=session_enum,
                is_indoor=bool(act_row[4])
            )
            activity.campers = attendees
            activities.append(activity)

        cursor.execute(
            "SELECT resource_id, name, target_quantity, current_quantity, condition FROM equipment WHERE camp_id = ?",
            (camp_id,)
        )
        equipment_rows = cursor.fetchall()
        equipment = [
            Equipment(
                resource_id=eq[0],
                name=eq[1],
                camp_id=camp_id,
                target_quantity=eq[2],
                current_quantity=eq[3],
                condition=eq[4],
            )
            for eq in equipment_rows
        ]

        start_date = datetime.strptime(row[4], "%Y-%m-%d").date() if row[4] else None
        end_date = datetime.strptime(row[5], "%Y-%m-%d").date() if row[5] else None

        camp = Camp(
            camp_id=camp_id,
            name=row[1],
            location=row[2],
            camp_type=row[3],
            start_date=start_date,
            end_date=end_date,
            camp_leader=row[6],
            campers=campers,
            food_per_camper_per_day=row[7],
            initial_food_stock=row[8],
            current_food_stock=row[9],
            equipment=equipment,
            activities=activities,
        )
        return camp

    def add(self, camp: Camp):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO camps (camp_id, name, location, camp_type, start_date, end_date, camp_leader, food_per_camper_per_day, initial_food_stock, current_food_stock)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    camp.camp_id,
                    camp.name,
                    camp.location,
                    camp.camp_type,
                    str(camp.start_date),
                    str(camp.end_date),
                    camp.camp_leader,
                    camp.food_per_camper_per_day,
                    camp.initial_food_stock,
                    camp.current_food_stock,
                ),
            )

            for camper in camp.campers:
                cursor.execute(
                    "SELECT camper_id FROM campers WHERE camper_id = ?",
                    (camper.camper_id,),
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO campers (camper_id, name, age, contact, medical_info) VALUES (?, ?, ?, ?, ?)",
                        (
                            camper.camper_id,
                            camper.name,
                            camper.age,
                            camper.contact,
                            camper.medical_info,
                        ),
                    )
                cursor.execute(
                    "INSERT INTO camp_campers (camp_id, camper_id) VALUES (?, ?)",
                    (camp.camp_id, camper.camper_id),
                )

            for act in camp.activities:
                cursor.execute(
                    "INSERT INTO scheduled_activities (camp_id, name, date, session, is_indoor) VALUES (?, ?, ?, ?, ?)",
                    (camp.camp_id, act.name, str(act.date), act.session.name, 1 if act.is_indoor else 0),
                )
                act_id = cursor.lastrowid
                for cid in act.campers:
                    cursor.execute(
                        "INSERT INTO activity_attendance (scheduled_activity_id, camper_id) VALUES (?, ?)",
                        (act_id, cid),
                    )

            for eq in camp.equipment:
                cursor.execute(
                    """
                    INSERT INTO equipment (resource_id, camp_id, name, target_quantity, current_quantity, condition)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        eq.resource_id,
                        camp.camp_id,
                        eq.name,
                        eq.target_quantity,
                        eq.current_quantity,
                        eq.condition,
                    ),
                )

            conn.commit()
        except Exception as exc:
            logging.error(f"Error adding camp: {exc}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def update(self, updated_camp: Camp):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE camps
                SET name=?, location=?, camp_type=?, start_date=?, end_date=?, camp_leader=?, food_per_camper_per_day=?, initial_food_stock=?, current_food_stock=?
                WHERE camp_id=?
                """,
                (
                    updated_camp.name,
                    updated_camp.location,
                    updated_camp.camp_type,
                    str(updated_camp.start_date),
                    str(updated_camp.end_date),
                    updated_camp.camp_leader,
                    updated_camp.food_per_camper_per_day,
                    updated_camp.initial_food_stock,
                    updated_camp.current_food_stock,
                    updated_camp.camp_id,
                ),
            )

            cursor.execute("DELETE FROM camp_campers WHERE camp_id = ?", (updated_camp.camp_id,))
            for camper in updated_camp.campers:
                cursor.execute(
                    "SELECT camper_id FROM campers WHERE camper_id = ?",
                    (camper.camper_id,),
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO campers (camper_id, name, age, contact, medical_info) VALUES (?, ?, ?, ?, ?)",
                        (
                            camper.camper_id,
                            camper.name,
                            camper.age,
                            camper.contact,
                            camper.medical_info,
                        ),
                    )
                cursor.execute(
                    "INSERT INTO camp_campers (camp_id, camper_id) VALUES (?, ?)",
                    (updated_camp.camp_id, camper.camper_id),
                )

            cursor.execute("SELECT id FROM scheduled_activities WHERE camp_id = ?", (updated_camp.camp_id,))
            old_act_ids = [row[0] for row in cursor.fetchall()]
            for act_id in old_act_ids:
                cursor.execute("DELETE FROM activity_attendance WHERE scheduled_activity_id = ?", (act_id,))
            cursor.execute("DELETE FROM scheduled_activities WHERE camp_id = ?", (updated_camp.camp_id,))

            for act in updated_camp.activities:
                cursor.execute(
                    "INSERT INTO scheduled_activities (camp_id, name, date, session, is_indoor) VALUES (?, ?, ?, ?, ?)",
                    (updated_camp.camp_id, act.name, str(act.date), act.session.name, 1 if act.is_indoor else 0),
                )
                new_act_id = cursor.lastrowid
                for cid in act.campers:
                    cursor.execute(
                        "INSERT INTO activity_attendance (scheduled_activity_id, camper_id) VALUES (?, ?)",
                        (new_act_id, cid),
                    )

            cursor.execute("DELETE FROM equipment WHERE camp_id = ?", (updated_camp.camp_id,))
            for eq in updated_camp.equipment:
                cursor.execute(
                    """
                    INSERT INTO equipment (resource_id, camp_id, name, target_quantity, current_quantity, condition)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        eq.resource_id,
                        updated_camp.camp_id,
                        eq.name,
                        eq.target_quantity,
                        eq.current_quantity,
                        eq.condition,
                    ),
                )

            conn.commit()
        except Exception as exc:
            logging.error(f"Error updating camp: {exc}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_camp_by_id(self, camp_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM camps WHERE camp_id = ?", (camp_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._build_camp_from_row(cursor, row)
        except Exception as exc:
            logging.error(f"Error getting camp by id: {exc}")
            return None
        finally:
            conn.close()

    def get_camps_by_leader(self, leader_username: str) -> list:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM camps WHERE camp_leader = ?", (leader_username,))
            rows = cursor.fetchall()
            return [self._build_camp_from_row(cursor, row) for row in rows]
        except Exception as exc:
            logging.error(f"Error getting camps by leader: {exc}")
            return []
        finally:
            conn.close()

    def get_global_activity_engagement(self) -> dict:
        camps = self.read_all()
        global_unique_campers = set()
        activity_data = []

        for camp in camps:
            for camper in getattr(camp, "campers", []):
                global_unique_campers.add(camper.name)

            for act in getattr(camp, "activities", []):
                act_name = act.get("name") if isinstance(act, dict) else getattr(act, "name", "Unknown")
                camper_ids = act.get("camper_ids", []) if isinstance(act, dict) else getattr(act, "campers", [])
                for cid in camper_ids:
                    activity_data.append({"activity": act_name, "camper": cid})

        total_unique = len(global_unique_campers)
        if total_unique == 0 or not activity_data:
            return {}

        try:
            df = pd.DataFrame(activity_data)
            engagement_series = df.groupby("activity")["camper"].nunique()
            metrics = (engagement_series / total_unique).round(2).to_dict()
            return metrics
        except ImportError:
            logging.error("Pandas not installed.")
            return {}
        except Exception as exc:
            logging.error(f"Error in engagement calculation: {exc}")
            return {}

    def get_camp_overview_stats(self) -> dict:
        camps = self.read_all()
        if not camps:
            return {"aggregates": {}, "details": []}

        data = []
        for camp in camps:
            leader = camp.camp_leader if camp.camp_leader else None
            stock = getattr(camp, "current_food_stock", 0)
            camper_count = len(getattr(camp, "campers", []))

            data.append(
                {
                    "name": camp.name,
                    "leader": leader,
                    "campers_count": camper_count,
                    "food_stock": stock,
                    "schedule_status": camp.get_schedule_status(),
                    "is_shortage": camp.is_food_shortage(),
                }
            )

        try:
            df = pd.DataFrame(data)
            aggregates = {
                "total_campers": int(df["campers_count"].sum()),
                "total_food": int(df["food_stock"].sum()),
                "assigned_leaders": int(df["leader"].notna().sum()),
                "total_camps": len(df),
                "shortage_camps": int(df["is_shortage"].sum()),
            }

            conditions = [pd.isna(df["leader"]) | (df["leader"] == ""), df["is_shortage"]]
            choices = ["Need Leader", "Low Food"]
            df["status"] = np.select(conditions, choices, default="Good")
            df["leader"] = df["leader"].fillna("[Unassigned]")

            return {"aggregates": aggregates, "details": df.to_dict("records")}
        except ImportError:
            logging.error("Pandas/Numpy not installed.")
            return {}
        except Exception as exc:
            logging.error(f"Error in overview calculation: {exc}")
            return {}


