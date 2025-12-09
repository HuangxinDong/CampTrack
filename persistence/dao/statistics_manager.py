import os
import sys
import json
from datetime import datetime

CURRENT_DIR = os.path.dirname(__file__) 
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from persistence.dao.camp_manager import CampManager
from persistence.dao.user_manager import UserManager

class StatisticsAndTrends:
    def __init__(self):
        self.camp_manager = CampManager()
        self.user_manager = UserManager()

    def get_participation(self, camp):
        """
        Return the number of campers assigned to this camp.
        """
        campers = getattr(camp, "campers", [])
        return len(campers)

    def get_food_usage(self, camp):
        """
        Estimate total food usage for this camp.
        Formula: num_campers * food_per_camper_per_day * camp_days
        If food per camper is not set, return 0.
        """
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
        if days == 0:
            return 0

        return num_campers * food_per_camper * days
    
    def get_incident_count(self, camp_id):
        """
        Count how many daily reports for this camp mention an incident.
        We simply look for keywords like 'incident' or 'injury' in the text.
        """
        path = "data.daily_reports.json"
        try:
            with open(path, "r") as f:
                reports = json.load(f)
        except FileNotFoundError:
            return 0
        except json.JSONDecodeError:
            print("[WARN] daily_reports.json is not valid JSON.")
            return 0

        count = 0
        for r in reports:
            if r.get("camp_id") != camp_id:
                continue
            text = (r.get("content") or r.get("report") or "").lower()
            if "incident" in text or "injury" in text or "accident" in text:
                count += 1
        return count


    def get_earnings(self, leader_username, camp):
        """
        earnings = leader_daily_payment_rate * camp_days
        """
        user = self.user_manager.find_user(leader_username)
        if not user:
            return 0

        daily_rate = user.get("daily_payment_rate", 0)
        if not daily_rate:
            return 0

        days = self.get_camp_days(camp)
        if days == 0:
            return 0

        return daily_rate * days
    def get_camp_days(self, camp):
        """
        Calculate how many days the camp runs (inclusive).
        """
        try:
            start = datetime.strptime(camp.start_date, "%Y-%m-%d")
            end = datetime.strptime(camp.end_date, "%Y-%m-%d")
        except Exception as e:
            print(f"[WARN] Failed to parse camp dates: {e}")
            return 0
        delta = (end - start).days
        return delta + 1 if delta >= 0 else 0

# test code
if __name__ == "__main__":
    stats = StatisticsAndTrends()
    camps = stats.camp_manager.read_all()
    if not camps:
        print("No camps found in camps.json")
    else:
        camp = camps[0]
        print("Camp name:", getattr(camp, "name", "N/A"))
        print("Participation:", stats.get_participation(camp))
        print("Food usage:", stats.get_food_usage(camp))


    



