from datetime import datetime, date
from persistence.dao.camp_manager import CampManager
from persistence.dao.user_manager import UserManager
from persistence.dao.daily_report_manager import DailyReportManager


class StatisticsHandler:
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

        if num_campers == 0 or food_per_camper == 0:
            return 0

        days = self.get_camp_days(camp)
        return num_campers * food_per_camper * days

    def get_injury_count(self, camp_id):
        reports = self.daily_report_manager.read_all()

        total_injuries = 0
        for r in reports:
            if r.get("camp_id") != camp_id:
                continue

            if r.get("injury") == "y":
                total_injuries += int(r.get("injured_count", 0))

        return total_injuries
    
    def get_injury_days(self, camp_id):
        reports = self.daily_report_manager.read_all()

        return sum(
            1 for r in reports
            if r.get("camp_id") == camp_id and r.get("injury") == "y"
        )

    def get_earnings(self, leader_username, camp):
        user = self.user_manager.find_user(leader_username)
        if not user:
            return 0

        daily_rate = getattr(user, "daily_payment_rate", 100) 
        days = self.get_camp_days(camp)

        return daily_rate * days

    def get_camp_days(self, camp):
        start = camp.start_date
        end = camp.end_date

        if isinstance(start, str):
            start = datetime.strptime(start, "%Y-%m-%d").date()
        if isinstance(end, str):
            end = datetime.strptime(end, "%Y-%m-%d").date()

        delta = (end - start).days
        return delta + 1 if delta >= 0 else 0
