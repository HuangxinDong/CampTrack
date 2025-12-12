from typing import List, Dict, Any, Tuple, Optional
import uuid
from datetime import datetime
from persistence.dao.daily_report_manager import DailyReportManager
from persistence.dao.camp_manager import CampManager
from persistence.dao.user_manager import UserManager
from models.camp import Camp

class ReportService:
    def __init__(self, daily_report_manager: DailyReportManager, camp_manager: CampManager, user_manager: UserManager):
        self.daily_report_manager = daily_report_manager
        self.camp_manager = camp_manager
        self.user_manager = user_manager

    def extract_summary(self, text: str) -> Dict[str, List[str]]:
        text_low = text.lower()
        activity_keywords = ["hike", "swim", "archery", "canoe", "craft", "walk", "game", "climb"]
        achievement_keywords = ["completed", "award", "achievement", "improved", "great job"]
        activities = [k for k in activity_keywords if k in text_low]
        achievements = [k for k in achievement_keywords if k in text_low]
        return {
            "activities": activities,
            "achievements": achievements,
        }

    def create_report(self, camp_name: str, leader_username: str, text: str, daily_participation: int, injury_flag: bool, injured_count: int, details: str) -> Tuple[bool, str]:
        camp = self.camp_manager.find_camp(camp_name)
        if not camp:
            return False, f"Camp '{camp_name}' not found."

        summary = self.extract_summary(text)
        
        # Get today's scheduled activities for this camp
        today_str = datetime.now().date().isoformat()
        todays_activities = []
        for act in camp.activities:
            act_date = act.get("date")
            if act_date == today_str:
                todays_activities.append(act.get("name"))

        report = {
            "id": str(uuid.uuid4()),
            "camp_id": camp.camp_id,
            "leader_username": leader_username,
            "date": today_str,
            "text": text,
            "daily_participation": daily_participation,
            "injury": injury_flag,
            "injured_count": injured_count,
            "incident_details": details,
            "activities": todays_activities,
            "achievements": summary["achievements"],
        }

        self.daily_report_manager.add_report(report)
        return True, "Report saved."

    def get_reports_for_camp(self, camp_id: str) -> List[Dict[str, Any]]:
        reports = [
            r for r in self.daily_report_manager.read_all()
            if r["camp_id"] == camp_id
        ]
        reports.sort(key=lambda r: r["date"], reverse=True)
        return reports

    def delete_report(self, report_id: str) -> Tuple[bool, str]:
        all_reports = self.daily_report_manager.read_all()
        new_reports = [x for x in all_reports if x["id"] != report_id]
        
        if len(all_reports) == len(new_reports):
            return False, "Report not found."
            
        self.daily_report_manager.save_all(new_reports)
        return True, "Report deleted."

    # Statistics Logic
    def get_camp_statistics(self, camp: Camp, leader_username: str) -> Dict[str, Any]:
        total_participants = len(camp.campers)
        
        if not camp.has_camp_started():
            avg_rate = 0
            earnings = 0
        else:
            avg_rate = self._get_average_participation_rate(camp)
            earnings = self._get_earnings(leader_username, camp)

        food_usage = self._get_food_usage(camp)
        
        all_reports = self.daily_report_manager.read_all()
        camp_reports = [r for r in all_reports if r["camp_id"] == camp.camp_id]
        
        incident_count = sum(int(r.get("injured_count", 0)) for r in camp_reports)
        activity_count = sum(len(r.get("activities", [])) for r in camp_reports)
        achievement_count = sum(len(r.get("achievements", [])) for r in camp_reports)

        return {
            "camp_name": camp.name,
            "campers": total_participants,
            "participation_rate": avg_rate,
            "food_used": food_usage,
            "incidents": incident_count,
            "activities": activity_count,
            "achievements": achievement_count,
            "earnings": earnings
        }

    def _get_average_participation_rate(self, camp: Camp) -> float:
        total = len(camp.campers)
        if total == 0: return 0

        reports = self.daily_report_manager.read_all()
        daily_list = [r.get("daily_participation", 0) for r in reports if r.get("camp_id") == camp.camp_id]
        
        if not daily_list: return 0

        avg_daily = sum(daily_list) / len(daily_list)
        return round(avg_daily / total, 2)

    def _get_earnings(self, leader_username: str, camp: Camp) -> float:
        user = self.user_manager.find_user(leader_username)
        if not user: return 0

        daily_rate = user.get("daily_payment_rate", 0.0)
        days = self._get_camp_days(camp)
        return daily_rate * days

    def _get_food_usage(self, camp: Camp) -> int:
        num_campers = len(camp.campers)
        food_per_camper = camp.food_per_camper_per_day
        if num_campers == 0 or food_per_camper == 0: return 0
        days = self._get_camp_days(camp)
        return num_campers * food_per_camper * days

    def _get_camp_days(self, camp: Camp) -> int:
        start = camp.start_date
        end = camp.end_date
        if isinstance(start, str): start = datetime.strptime(start, "%Y-%m-%d").date()
        if isinstance(end, str): end = datetime.strptime(end, "%Y-%m-%d").date()
        delta = (end - start).days
        return delta + 1 if delta >= 0 else 0