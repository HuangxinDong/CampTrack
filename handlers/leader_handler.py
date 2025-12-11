from datetime import datetime
import csv

from handlers.base_handler import BaseHandler
from cli.input_utils import get_input, cancellable
from cli.prompts import get_positive_int

from persistence.dao.camp_manager import CampManager
from persistence.dao.daily_report_manager import DailyReportManager
from persistence.dao.user_manager import UserManager

from models.camper import Camper
from handlers.statistics_handler import StatisticsHandler


class LeaderHandler(BaseHandler):
    """Handles Leader-specific operations."""

    def __init__(self, user, user_manager, message_manager, camp_manager, announcement_manager):
        super().__init__(user, user_manager, message_manager, camp_manager, announcement_manager)
        self.camp_manager = camp_manager
        self.daily_report_manager = DailyReportManager()
        self.statistics = StatisticsHandler()

        self.commands = self.parent_commands + [
            {"name": "Select Camps to Supervise", "command": self.select_camps_to_supervise},
            {"name": "Edit Camp", "command": self.edit_camp},
            {"name": "Assign Campers from CSV", "command": self.assign_campers_from_csv},
            {"name": "Create Daily Report", "command": self.create_daily_report},
            {"name": "View My Statistics", "command": self.view_statistics},
        ]

        self.main_commands = self.commands.copy()

    @cancellable
    def select_camps_to_supervise(self):
        camps = self.camp_manager.read_all()

        print("\nAvailable camps:")
        for idx, camp in enumerate(camps, 1):
            if camp.camp_leader == self.user.username:
                status = " (You are the leader)"
            elif camp.camp_leader:
                status = f" (Assigned to {camp.camp_leader})"
            else:
                status = " (Available)"

            print(f"{idx}. {camp.name} - {camp.location}{status}")

        selection = get_input("\nEnter camp numbers (comma-separated): ")
        try:
            picks = [int(x.strip()) - 1 for x in selection.split(",")]
        except:
            print("Invalid input.")
            return

        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        for index in picks:
            if not (0 <= index < len(camps)):
                print(f"Invalid selection {index + 1}")
                continue

            camp = camps[index]

            if camp.camp_leader and camp.camp_leader != self.user.username:
                print(f"Cannot select {camp.name} — assigned to {camp.camp_leader}")
                continue

            if self._has_schedule_conflict(camp, my_camps):
                print(f"Cannot select '{camp.name}' — date conflict detected.")
                continue

            camp.camp_leader = self.user.username
            self.camp_manager.update(camp)
            print(f"You are now supervising: {camp.name}")


    def _has_schedule_conflict(self, new_camp, my_camps):
        """
        Private method to check schedule conflict.
        """
        new_start = datetime.strptime(str(new_camp.start_date), "%Y-%m-%d").date()
        new_end = datetime.strptime(str(new_camp.end_date), "%Y-%m-%d").date()

        for c in my_camps:
            s = datetime.strptime(str(c.start_date), "%Y-%m-%d").date()
            e = datetime.strptime(str(c.end_date), "%Y-%m-%d").date()

            if new_start <= e and new_end >= s:
                return True

        return False


    @cancellable
    def edit_camp(self):
        camps = self.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            print("You are not supervising any camps.")
            return

        print("\nYour camps:")
        for idx, camp in enumerate(my_camps, 1):
            print(f"{idx}. {camp.name}")

        choice = get_input("Select camp to edit: ")
        try:
            camp = my_camps[int(choice) - 1]
        except:
            print("Invalid selection.")
            return

        new_amount = get_positive_int("Enter food per camper per day: ")
        camp.food_per_camper_per_day = new_amount
        self.camp_manager.update(camp)

        print(f"Updated food requirement for {camp.name}.")



    @cancellable
    def assign_campers_from_csv(self):
        camps = self.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            print("You are not supervising any camps.")
            return

        print("\nYour camps:")
        for idx, camp in enumerate(my_camps, 1):
            print(f"{idx}. {camp.name}")

        try:
            camp = my_camps[int(get_input("Choose a camp: ")) - 1]
        except:
            print("Invalid selection.")
            return

        path = get_input("Enter CSV file path: ")

        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    camper = Camper(
                        name=row.get("name"),
                        age=int(row.get("age", 0)),
                        contact=row.get("contact"),
                        medical_info=row.get("medical_info")
                    )
                    camp.campers.append(camper)

            self.camp_manager.update(camp)
            print(f"Imported campers into {camp.name}.")

        except Exception as e:
            print("Error reading CSV:", e)


    @cancellable
    def create_daily_report(self):
        camps = self.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            print("You are not supervising any camps.")
            return

        print("\nYour camps:")
        for idx, camp in enumerate(my_camps, 1):
            print(f"{idx}. {camp.name}")

        try:
            camp = my_camps[int(get_input("Choose a camp: ")) - 1]
        except:
            print("Invalid selection.")
            return

        today = datetime.today().strftime("%Y-%m-%d")
        text = get_input("Enter today's report text: ")
        
        # Ask for food usage
        food_usage_int = get_positive_int("Enter amount of food used today: ")
        
        try:
             camp.remove_food(food_usage_int, today)
             self.camp_manager.update(camp)
        except ValueError as e:
             print(f"Warning: Could not save food usage: {e}")

        report = {
            "camp_id": camp.camp_id,
            "leader_username": self.user.username,
            "date": today,
            "text": text,
        }

        self.daily_report_manager.add_report(report)
        print("Daily report saved.")


    def view_statistics(self):
        camps = self.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            print("You are not supervising any camps.")
            return

        print("\n===== Statistics =====")

        for camp in my_camps:
            print(f"\nCamp: {camp.name}")
            print(f"- Participants: {self.statistics.get_participation(camp)}")
            print(f"- Food usage: {self.statistics.get_food_usage(camp)}")
            print(f"- Incident count: {self.statistics.get_incident_count(camp.camp_id)}")
            print(f"- Earnings: £{self.statistics.get_earnings(self.user.username, camp)}")
