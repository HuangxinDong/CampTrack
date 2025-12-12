from datetime import datetime
import csv
import os
import uuid
import json

from handlers.base_handler import BaseHandler
from cli.prompts import get_index_from_options, get_positive_int
from cli.input_utils import get_input, cancellable, wait_for_enter
from cli.prompts import get_positive_int
from cli.console_manager import console_manager

from models.activity import Activity, Session
from persistence.dao.daily_report_manager import DailyReportManager
from models.camper import Camper
from handlers.statistics_handler import StatisticsHandler

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

ACTIVITIES_FILE = os.path.join("persistence", "data", "activities.json")

class LeaderHandler(BaseHandler):

    @staticmethod
    def extract_summary(text):
        text_low = text.lower()

        activity_keywords = ["hike", "swim", "archery", "canoe", "craft", "walk", "game", "climb"]
        achievement_keywords = ["completed", "award", "achievement", "improved", "great job"]
        activities = [k for k in activity_keywords if k in text_low]
        achievements = [k for k in achievement_keywords if k in text_low]

        return {
            "activities": activities,
            "achievements": achievements,
        }
    def __init__(self, user, context):
        super().__init__(user, context)

        self.daily_report_manager = DailyReportManager()
        self.statistics = StatisticsHandler()

        self.commands = self.parent_commands + [
            {"name": "Select Camps to Supervise", "command": self.select_camps},
            {"name": "Edit Camp Food Settings", "command": self.edit_camp},
            {"name": "Assign Campers from CSV", "command": self.import_campers_from_csv},
            {"name": "View Campers", "command": self.view_campers},
            {"name": "Manage Activities", "command": self.activities_menu},
            {"name": "Daily Reports", "command": self.daily_reports_menu},
            {"name": "View My Statistics", "command": self.show_statistics},
            {"name": "Emergency Contact Lookup", "command": self.emergency_lookup},
        ]

        self.main_commands = self.commands.copy()


    def select_camps(self):
        camps = self.context.camp_manager.read_all()
        available = [c for c in camps]
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        console.print(Panel("Available Camps", style="cyan"))
        for i, camp in enumerate(available, 1):
            console.print(f"{i}. {camp.name} ({camp.location})")

        choice = get_input("Enter camp number to supervise: ")

        try:
            index = int(choice) - 1
            camp = available[index]
        except:
            console_manager.print_error("Invalid selection.")
            return

        if camp.camp_leader and camp.camp_leader != self.user.username:
            console_manager.print_error(f"Camp already supervised by {camp.camp_leader}.")
            return

        if self._conflict_with_existing(camp, my_camps):
            console_manager.print_error("Date conflict detected with your existing camps.")
            return

        camp.camp_leader = self.user.username
        self.context.camp_manager.update(camp)

        console_manager.print_success(f"You are now supervising {camp.name}.")
        self.context.audit_log_manager.log_event(self.user.username, "Supervise Camp", f"Started supervising {camp.name}")
        wait_for_enter()

    def _conflict_with_existing(self, new, existing):
        ns = datetime.strptime(str(new.start_date), "%Y-%m-%d").date()
        ne = datetime.strptime(str(new.end_date), "%Y-%m-%d").date()
        for c in existing:
            s = datetime.strptime(str(c.start_date), "%Y-%m-%d").date()
            e = datetime.strptime(str(c.end_date), "%Y-%m-%d").date()
            if ns <= e and ne >= s:
                return True
        return False


    @cancellable
    def edit_camp(self):
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            console_manager.print_error("You don't supervise any camps.")
            return

        camp = self._select_camp(my_camps)
        if not camp:
            return

        new_food = get_positive_int("Enter food per camper per day: ")
        camp.food_per_camper_per_day = new_food
        self.context.camp_manager.update(camp)
        self.context.audit_log_manager.log_event(self.user.username, "Edit Camp", f"Updated food settings for {camp.name}")

        console_manager.print_success(f"Updated food requirement for {camp.name}.")

        total_required = camp.total_food_required()
        num_campers = len(camp.campers)
        days = (camp.end_date - camp.start_date).days + 1

        console.print(
            f"\n[bold]Total Food Required for {camp.name}:[/bold] {total_required} units\n"
            f"  ({num_campers} campers x {days} days x {new_food} food)"
        )
        wait_for_enter()


    @cancellable
    def import_campers_from_csv(self):
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            console_manager.print_error("You don't supervise any camps.")
            return

        camp = self._select_camp(my_camps)
        if not camp:
            return

        folder_path = os.path.join("persistence", "data", "campers")
        csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]

        if not csv_files:
            console_manager.print_error("No CSV files found.")
            return

        console.print(Panel("Available Camper CSV Files", style="cyan"))
        for i, f in enumerate(csv_files, 1):
            console.print(f"{i}. {f}")

        choice = get_input("Choose CSV file number: ")

        try:
            csv_file = csv_files[int(choice) - 1]
        except:
            console_manager.print_error("Invalid selection.")
            return

        csv_path = os.path.join(folder_path, csv_file)

        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    camp.campers.append(
                        Camper(
                            name=row.get("name"),
                            age=row.get("age"),
                            contact=row.get("contact"),
                            medical_info=row.get("medical_info")
                        )
                    )

            self.context.camp_manager.update(camp)
            console_manager.print_success(f"Imported campers into {camp.name}.")
            wait_for_enter()

        except Exception as e:
            console_manager.print_error(f"Error reading CSV: {e}")
            wait_for_enter()


    def view_campers(self):
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            console_manager.print_error("You supervise no camps.")
            return

        camp = self._select_camp(my_camps)
        if not camp:
            return

        table_lines = [f"[bold]{camp.name} Campers[/bold]"]
        table_lines.append("─" * 40)

        if not camp.campers:
            table_lines.append("No campers yet.")
        else:
            for c in camp.campers:
                table_lines.append(f"{c.name} (Age {c.age}) — {c.contact}")

        console.print(Panel("\n".join(table_lines), style="cyan"))
        wait_for_enter()

    @cancellable
    def daily_reports_menu(self):
        while True:
            console.print(Panel("""
[bold]Daily Reports[/bold]
1. Create New Report
2. View Reports
3. Delete Report
""", style="blue"))

            choice = get_input("Choose an option: ")

            if choice == "1":
                self.create_daily_report()
            elif choice == "2":
                self.view_daily_reports()
            elif choice == "3":
                self.delete_daily_report()
            elif choice == "b":
                break
            else:
                console_manager.print_error("Invalid choice.")
    

    @cancellable
    def create_daily_report(self):

        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            console_manager.print_error("You supervise no camps.")
            return

        camp = self._select_camp(my_camps)
        if not camp:
            return

        text = get_input("Enter report text(please include any achievements or key activities): ")
        daily_participation = get_positive_int("How many campers participated today? ")

        summary = LeaderHandler.extract_summary(text)

        injury_flag = get_input("Any injuries today? (y/n): ")

        injured_count = 0
        details = ""

        if injury_flag == "y":
            injured_count = get_positive_int("How many injured? ")
            details = get_input("Describe the incident: ")
            food_used = get_positive_int("Enter food used today: ")

            try:
                camp.remove_food(food_used, datetime.now().date().isoformat())
                self.context.camp_manager.update(camp)
            except Exception as e:
                console_manager.print_error(f"Could not save food usage: {e}")

        report = {
            "id": str(uuid.uuid4()),
            "camp_id": camp.camp_id,
            "leader_username": self.user.username,
            "date": datetime.now().date().isoformat(),
            "text": text,
            "daily_participation": daily_participation,
            "injury": injury_flag,
            "injured_count": injured_count,
            "incident_details": details,
            "incidents": [],
            "activities": summary["activities"],
            "achievements": summary["achievements"],
        }

        self.daily_report_manager.add_report(report)
        console_manager.print_success("Report saved.")
        wait_for_enter()


    def view_daily_reports(self):
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            console_manager.print_error("You supervise no camps.")
            return

        camp = self._select_camp(my_camps)
        if not camp:
            return

        reports = [
            r for r in self.daily_report_manager.read_all()
            if r["camp_id"] == camp.camp_id
        ]

        if not reports:
            console_manager.print_error("No reports available.")
            return

        reports.sort(key=lambda r: r["date"], reverse=True)

        from rich.table import Table

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Date", width=12)
        table.add_column("Summary", width=40)
        table.add_column("Activities")
        table.add_column("Incidents")
        table.add_column("Achievements")

        for r in reports:
            table.add_row(
                r["date"],
                r["text"][:40] + "",
                ", ".join(r.get("activities", [])),
                ", ".join(r.get("incidents", [])),
                ", ".join(r.get("achievements", [])),
            )

        console.print(table)
        wait_for_enter()


    def delete_daily_report(self):
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            console_manager.print_error("You supervise no camps.")
            return

        camp = self._select_camp(my_camps)
        if not camp:
            return

        reports = [
            r for r in self.daily_report_manager.read_all()
            if r["camp_id"] == camp.camp_id
        ]

        if not reports:
            console_manager.print_error("No reports to delete.")
            return

        console.print(Panel("Reports:", style="blue"))
        for i, r in enumerate(reports, 1):
            console.print(f"{i}. {r['date']} — {r['text'][:40]}")

        choice = get_input("Choose report number to delete: ")

        try:
            r = reports[int(choice) - 1]
        except:
            console_manager.print_error("Invalid selection.")
            return

        all_reports = self.daily_report_manager.read_all()
        all_reports = [x for x in all_reports if x["id"] != r["id"]]
        self.daily_report_manager.save_all(all_reports)

        console_manager.print_success("Report deleted.")
        wait_for_enter()


    def show_statistics(self):
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            console.print("You are not supervising any camps.", style="yellow")
            wait_for_enter()
            return

        console.print(Panel("Statistics for Your Camps", style="cyan"))

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Camp")
        table.add_column("Campers", justify="center")
        table.add_column("Avg Participation Rate", justify="center")
        table.add_column("Food Used", justify="center")
        table.add_column("Incidents", justify="center")
        table.add_column("Activities", justify="center")
        table.add_column("Achievements", justify="center")
        table.add_column("Earnings", justify="center")

        total_earnings = 0
        all_reports = self.daily_report_manager.read_all()  

        for camp in my_camps:
            total_participants = self.statistics.get_total_participants(camp)
            avg_rate = self.statistics.get_average_participation_rate(camp)  
            avg_rate_str = f"{avg_rate * 100:.1f}%" if avg_rate > 0 else "0%"
            food_usage = self.statistics.get_food_usage(camp)
            camp_reports = [r for r in all_reports if r["camp_id"] == camp.camp_id]
            incident_count = sum(int(r.get("injured_count", 0)) for r in camp_reports)
            activity_count = sum(len(r.get("activities", [])) for r in camp_reports)
            achievement_count = sum(len(r.get("achievements", [])) for r in camp_reports)
            earnings = self.statistics.get_earnings(self.user.username, camp)
            total_earnings += earnings

            table.add_row(
                camp.name,
                str(total_participants),
                avg_rate_str,
                str(food_usage),
                str(incident_count),
                str(activity_count),
                str(achievement_count),
                f"£{earnings}",
            )

        console.print(table)


        console.print(
            Panel(
                f"[bold green]Total Earnings Across All Camps: £{total_earnings}[/bold green]",
                style="green"
            )
        )
        wait_for_enter()



    def _select_camp(self, camps):
        console.print(Panel("Select Camp", style="cyan"))
        for i, c in enumerate(camps, 1):
            console.print(f"{i}. {c.name} ({c.location})")

        while True:
            choice = get_input("Choose camp number: ")
            try:
                index = int(choice) - 1
                if 0 <= index < len(camps):
                    return camps[index]
                else:
                    console_manager.print_error("Invalid selection. Please choose a number from the list.")
            except ValueError:
                console_manager.print_error("Invalid input. Please enter a number.")

    # ACTIVITES

    def _load_activity_library(self):
        if os.path.exists(ACTIVITIES_FILE):
            with open(ACTIVITIES_FILE, "r") as f:
                return json.load(f)
        return []

    def _save_activity_library(self, activities):
        with open(ACTIVITIES_FILE, "w") as f:
            json.dump(activities, f, indent=4)

    def activities_menu(self):
        while True:
            console.print(Panel("""
[bold]Manage Activities[/bold]
1. Add Activities to Camp
2. View Camp Activities
3. Add New Activity 
b. Back
""", style="blue"))

            choice = get_input("Choose an option: ")

            if choice == "1":
                self.add_activities_to_camp()
            elif choice == "2":
                self.view_camp_activities()
            elif choice == "3":
                self.add_activity_to_library()
            elif choice.lower() == "b":
                break
            else:
                console_manager.print_error("Invalid choice.")

    def add_activities_to_camp(self):
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            console_manager.print_error("You don't supervise any camps.")
            return

        camp = self._select_camp(my_camps)
        if not camp:
            return

        if not camp.campers:
            console_manager.print_error("This camp has no campers yet. Add campers first.")
            return

        activity_library = self._load_activity_library()

        if not activity_library:
            console_manager.print_error("No activities in library. Add some first.")
            return
        

        activity_index = get_index_from_options("Available Activities", activity_library)

        activity_name = activity_library[activity_index]

        # Choose date from dates in camp

        camp_dates = camp.get_date_range()

        date_index = get_index_from_options("Available Dates", camp_dates)

        selected_date = camp_dates[date_index]

        session_names = [s.name for s in Session]
        session_index = get_index_from_options("Sessions", session_names)

        # If activity already exists on that day and at that session, let the user know and return

        if added:
            self.context.camp_manager.update(camp)
            camper_names = ", ".join([c.name for c in camp.campers])
            console_manager.print_success(
                f"Added {', '.join(added)} to {camp.name}. "
                f"All {len(camp.campers)} campers ({camper_names}) assigned."
            )
            wait_for_enter()

    def view_camp_activities(self):
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            console_manager.print_error("You don't supervise any camps.")
            return

        camp = self._select_camp(my_camps)
        if not camp:
            return

        if not camp.activities:
            console_manager.print_error("No activities assigned to this camp yet.")
            return

        lines = [f"[bold]{camp.name} Activities[/bold]", "─" * 40]

        for activity in camp.activities:
            camper_count = len(activity.get("camper_ids", []))
            lines.append(f"• {activity['name']} ({camper_count} campers)")

        console.print(Panel("\n".join(lines), style="blue"))
        wait_for_enter()

    def add_activity_to_library(self):
        activity_library = self._load_activity_library()

        console.print(Panel("Current Activity Library", style="blue"))
        if activity_library:
            for i, a in enumerate(activity_library, 1):
                console.print(f"{i}. {a}")
        else:
            console.print("[dim]No activities yet.[/dim]")

        new_activity = get_input("Enter new activity name: ").strip()

        if not new_activity:
            console_manager.print_error("Activity name cannot be empty.")
            return

        if new_activity in activity_library:
            console_manager.print_error("Activity already exists.")
            return

        activity_library.append(new_activity)
        self._save_activity_library(activity_library)
        console_manager.print_success(f"Added '{new_activity}' to activity library.")
        wait_for_enter

    def emergency_lookup(self):
        console.print(Panel("Emergency Contact Lookup", style="red"))

        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            console_manager.print_error("You supervise no camps.")
            return

        camp = self._select_camp(my_camps)
        if not camp:
            return

        if not camp.campers:
            console_manager.print_error("No campers in this camp.")
            return

        name = get_input("Enter camper name: ")

        camper = self.find_camper_by_name(name, camp.campers)

        if camper:
            console.print(f"[green]Name:[/green] {camper.name}")
            console.print(f"[green]Contact:[/green] {camper.contact}")
            if camper.medical_info:
                console.print(f"[yellow]Medical Info:[/yellow] {camper.medical_info}")
        else:
            console_manager.print_error("Camper not found. Please check the name.")


    def find_camper_by_name(self, name, campers):
        for camper in campers:
            if camper.name and camper.name.lower() == name.lower():
                return camper
        return None

