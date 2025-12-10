import os
import sys
from datetime import datetime, date

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from persistence.dao.camp_manager import CampManager
from persistence.dao.user_manager import UserManager
from persistence.dao.daily_report_manager import DailyReportManager


class StatisticsAndTrends:
    def __init__(self):
        self.camp_manager = CampManager()
        self.user_manager = UserManager()
        self.daily_report_manager = DailyReportManager()

    def get_participation(self, camp):
        return len(getattr(camp, "campers", []))

    def get_food_usage(self, camp):
        campers = getattr(camp, "campers", [])
        num_campers = len(campers)

        food_per_camper = getattr(
            camp,
            "food_per_camper_per_day",
            getattr(camp, "food_per_camper", 0)
        )

        if not num_campers or not food_per_camper:
            return 0

        days = self.get_camp_days(camp)
        return num_campers * food_per_camper * days if days > 0 else 0

    def get_incident_count(self, camp_id):
        reports = self.daily_report_manager.read_all()

        count = 0
        for r in reports:
            if r.get("camp_id") != camp_id:
                continue
            text = (r.get("content") or r.get("report") or "").lower()
            if any(word in text for word in ["incident", "injury", "accident"]):
                count += 1
        return count

    def get_earnings(self, leader_username, camp):
        user = self.user_manager.find_user(leader_username)
        if not user:
            return 0

        daily_rate = user.get("daily_payment_rate", 0)
        if not daily_rate:
            return 0

        days = self.get_camp_days(camp)
        return daily_rate * days if days > 0 else 0

    def get_camp_days(self, camp):
        start = camp.start_date
        end = camp.end_date
        try:
            if isinstance(start, date):
                start_dt = datetime.combine(start, datetime.min.time())
            else:
                start_dt = datetime.strptime(start, "%Y-%m-%d")

            if isinstance(end, date):
                end_dt = datetime.combine(end, datetime.min.time())
            else:
                end_dt = datetime.strptime(end, "%Y-%m-%d")

        except Exception as e:
            print(f"[WARN] Failed to parse camp dates: {e}")
            return 0

        delta = (end - start).days
        return delta + 1 if delta >= 0 else 0