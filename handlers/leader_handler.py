from datetime import datetime
import csv
import uuid
import os

from handlers.base_handler import BaseHandler
from cli.input_utils import get_input, cancellable
from cli.prompts import get_positive_int
from cli.console_manager import console_manager

from persistence.dao.daily_report_manager import DailyReportManager

from models.camper import Camper
from handlers.statistics_handler import StatisticsHandler

from interface.interface_leader import LeaderInterface


class LeaderHandler(BaseHandler):

    def __init__(self, user, context):
        super().__init__(user, context)

        self.daily_report_manager = DailyReportManager()
        self.statistics = StatisticsHandler()
        self.interface = LeaderInterface()    

        self.commands = self.parent_commands + [
            {"name": "Select Camps to Supervise", "command": self.select_camps_to_supervise},
            {"name": "Edit Camp", "command": self.edit_camp},
            {"name": "Assign Campers from CSV", "command": self.assign_campers_from_csv},
            {'name': 'View Campers', 'command': self.view_campers}, 
            {"name": "Daily Reports", "command": self.daily_reports_menu},
            {"name": "View My Statistics", "command": self.view_statistics},
        ]

        self.main_commands = self.commands.copy()


    @cancellable
    def select_camps_to_supervise(self):
        camps = self.context.camp_manager.read_all()

        self.interface.show_available_camps(camps, self.user.username)

        selection = get_input("Enter camp numbers (comma-separated): ")
        try:
            picks = [int(x.strip()) - 1 for x in selection.split(",")]
        except:
            self.interface.show_message("Invalid input.")
            return

        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        for index in picks:
            if not (0 <= index < len(camps)):
                self.interface.show_message(f"Invalid selection {index + 1}")
                continue

            camp = camps[index]

            if camp.camp_leader and camp.camp_leader != self.user.username:
                self.interface.show_message(f"Cannot select {camp.name} — assigned to {camp.camp_leader}")
                continue

            if self._has_schedule_conflict(camp, my_camps):
                self.interface.show_message(f"Cannot select '{camp.name}' — date conflict detected.")
                continue

            camp.camp_leader = self.user.username
            self.camp_manager.update(camp)
            self.interface.show_message(f"You are now supervising: {camp.name}")

    def _has_schedule_conflict(self, new_camp, my_camps):
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
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            self.interface.show_message("You are not supervising any camps.")
            return

        camp = self.interface.select_camp(my_camps)
        if not camp:
            self.interface.show_message("Invalid selection.")
            return

        new_amount = get_positive_int("Enter food per camper per day: ")
        camp.food_per_camper_per_day = new_amount
        self.context.camp_manager.update(camp)

        console_manager.print_success(f"Updated food requirement for {camp.name}.")

        self.interface.show_message(f"Updated food requirement for {camp.name}.")


    @cancellable
    def assign_campers_from_csv(self):
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            self.interface.show_message("You are not supervising any camps.")
            return

        camp = self.interface.select_camp(my_camps)
        if not camp:
            self.interface.show_message("Invalid selection.")
            return

        path = self.interface.get_csv_path()

        try:
            csv_choice = int(get_input("Choose a CSV file by number: ")) - 1
            csv_file = csv_files[csv_choice]
        except (ValueError, IndexError):
            console_manager.print_error("Invalid selection.")
            return

        csv_path = os.path.join(folder_path, csv_file)

        # Import campers
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
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
            self.interface.show_message(f"Imported campers into {camp.name}.")

        except Exception as e:
            self.interface.show_message(f"Error reading CSV: {e}")


    def view_campers(self):
        camps = self.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            self.interface.show_message("You are not supervising any camps.")
            return

        camp = self.interface.select_camp(my_camps)
        if not camp:
            self.interface.show_message("Invalid selection.")
            return

        self.interface.show_campers_table(camp)
    
    def daily_reports_menu(self):
        while True:
            choice = input("""
            ===== Daily Reports =====
                1. Create New Report
                2. Review Reports
                3. Delete Report
                4. Back
                Choose an option: """)
            if choice == "1":
                self.create_daily_report()
            elif choice == "2":
                self.view_daily_reports()
            elif choice == "3":
                self.delete_daily_report()
            elif choice == "4":
                break
            else:
                self.interface.show_message("Invalid choice.")


    @cancellable
    def create_daily_report(self):
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            self.interface.show_message("You are not supervising any camps.")
            return

        camp = self.interface.select_camp(my_camps)
        if not camp:
            self.interface.show_message("Invalid selection.")
            return

        report_text, incident_flag = self.interface.get_daily_report_input()

        today = datetime.today().strftime("%Y-%m-%d")

        # Ask for food usage
        food_usage_int = get_positive_int("Enter amount of food used today: ")

        try:
            camp.remove_food(food_usage_int, today)
            self.context.camp_manager.update(camp)
        except ValueError as e:
            console_manager.print_error(f"Warning: Could not save food usage: {e}")

        report = {
            "id": str(uuid.uuid4()),
            "camp_id": camp.camp_id,
            "leader_username": self.user.username,
            "date": today,
            "text": report_text,
            "incident": incident_flag
        }

        self.daily_report_manager.add_report(report)
        self.interface.show_message("Daily report saved.")

    def view_daily_reports(self):
        camps = self.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            self.interface.show_message("You are not supervising any camps.")
            return

        camp = self.interface.select_camp(my_camps)
        if not camp:
            self.interface.show_message("Invalid selection.")
            return

        reports = [r for r in self.daily_report_manager.read_all()
                if r["camp_id"] == camp.camp_id]

        if not reports:
            self.interface.show_message("No reports yet.")
            return

        reports.sort(key=lambda r: r["date"], reverse=True)

        self.interface.show_reports_table(camp, reports)
    
    @cancellable
    def delete_daily_report(self):
        camps = self.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            self.interface.show_message("You are not supervising any camps.")
            return

        camp = self.interface.select_camp(my_camps)
        if not camp:
            self.interface.show_message("Invalid selection.")
            return

        reports = [r for r in self.daily_report_manager.read_all()
                if r["camp_id"] == camp.camp_id]

        if not reports:
            self.interface.show_message("No reports to delete.")
            return

        self.interface.show_reports_table(camp, reports)

        to_delete = self.interface.pick_report_to_delete(reports)
        if not to_delete:
            self.interface.show_message("Invalid selection.")
            return

        all_reports = self.daily_report_manager.read_all()
        all_reports = [r for r in all_reports if r["id"] != to_delete["id"]]

        self.daily_report_manager.save_all(all_reports)
        self.interface.show_message("Report deleted.")


    def view_statistics(self):
        camps = self.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            self.interface.show_message("You are not supervising any camps.")
            return

        for camp in my_camps:
            stats = {
                "participants": self.statistics.get_participation(camp),
                "food": self.statistics.get_food_usage(camp),
                "incidents": self.statistics.get_incident_count(camp.camp_id),
                "earnings": self.statistics.get_earnings(self.user.username, camp)
            }

            self.interface.show_statistics(camp, stats)

