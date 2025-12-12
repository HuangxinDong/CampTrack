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
from models.camp import Camp
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
            {"name": "Search Campers for Emergency Details", "command": self.search_camper},
            {"name": "Manage Activities", "command": self.activities_menu},
            {"name": "Daily Reports", "command": self.daily_reports_menu},
            {"name": "View My Statistics", "command": self.show_statistics}
        ]

        self.main_commands = self.commands.copy()


    @cancellable
    def select_camps(self):
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        console.print(Panel("Select a Camp to Supervise", style="cyan"))
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Camp Name")
        table.add_column("Location")
        table.add_column("Dates")
        table.add_column("Current Leader")
        table.add_column("Status")

        for i, camp in enumerate(camps, 1):
            leader = camp.camp_leader
            if not leader:
                leader_display = "[dim]None[/dim]"
                status = "[green]Available[/green]"
            elif leader == self.user.username:
                leader_display = "[bold green]You[/bold green]"
                status = "[blue]Already Supervising[/blue]"
            else:
                leader_display = f"[red]{leader}[/red]"
                status = "[red]Taken[/red]"
            
            dates = f"{camp.start_date} to {camp.end_date}"
            table.add_row(str(i), camp.name, camp.location, dates, leader_display, status)

        console.print(table)

        while True:
            choice = get_input("Enter camp number to supervise: ")

            try:
                index = int(choice) - 1
                if not (0 <= index < len(camps)):
                    raise ValueError
                camp = camps[index]
            except:
                console_manager.print_error("Invalid selection. Please try again.")
                continue

            if camp.camp_leader:
                if camp.camp_leader == self.user.username:
                    console_manager.print_info(f"You are already supervising {camp.name}. Please select another.")
                else:
                    console_manager.print_error(f"Camp already supervised by {camp.camp_leader}. Please select another.")
                continue

            if self._conflict_with_existing(camp, my_camps):
                console_manager.print_error("Date conflict detected with your existing camps. Please select another.")
                continue

            camp.camp_leader = self.user.username
            self.context.camp_manager.update(camp)

            console_manager.print_success(f"You are now supervising {camp.name}.")
            self.context.audit_log_manager.log_event(self.user.username, "Supervise Camp", f"Started supervising {camp.name}")
            wait_for_enter()
            break

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

        all_camps = self.context.camp_manager.read_all()
        conflicting_camps = []
        for other_camp in all_camps:
            if other_camp.camp_id == camp.camp_id:
                continue
            if Camp.dates_overlap(camp.start_date, camp.end_date, other_camp.start_date, other_camp.end_date):
                conflicting_camps.append(other_camp)

        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                imported_count = 0
                skipped_count = 0
                
                for row in reader:
                    name = row.get("name")
                    if not name:
                        continue

                    # Check if already in current camp
                    if any(c.name.lower() == name.lower() for c in camp.campers):
                        console_manager.print_warning(f"Skipping '{name}': Already registered in this camp.")
                        skipped_count += 1
                        continue
                        
                    # Check conflict
                    conflict_found = False
                    for other_camp in conflicting_camps:
                        if any(c.name.lower() == name.lower() for c in other_camp.campers):
                            console_manager.print_warning(f"Skipping '{name}': Already registered in overlapping camp '{other_camp.name}'.")
                            conflict_found = True
                            break
                    
                    if conflict_found:
                        skipped_count += 1
                        continue

                    age_raw = row.get("age")
                    age = int(age_raw) if age_raw and age_raw.isdigit() else 0

                    camp.campers.append(
                        Camper(
                            name=name,
                            age=age,
                            contact=row.get("contact") or "",
                            medical_info=row.get("medical_info") or ""
                        )
                    )
                    imported_count += 1

            self.context.camp_manager.update(camp)
            console_manager.print_success(f"Imported {imported_count} campers into {camp.name}. (Skipped {skipped_count} conflicts)")
            wait_for_enter()

        except Exception as e:
            console_manager.print_error(f"Error reading CSV: {e}")
            wait_for_enter()


    @cancellable
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
    def search_camper(self):
        """Search for a camper in supervised camps (Global Search & Emergency Info)."""
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]
        
        if not my_camps:
            console_manager.print_error("You don't supervise any camps.")
            return

        while True:
            query = get_input("Enter camper name (or part of name) to search: ").lower()
            
            found = []
            for camp in my_camps:
                for camper in camp.campers:
                    if query in camper.name.lower():
                        found.append((camp.name, camper))
            
            if not found:
                console_manager.print_error(f"No campers found matching '{query}'. Please try again.")
                continue
                
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("#", style="dim", width=4)
            table.add_column("Camp")
            table.add_column("Name")
            table.add_column("Contact")
            
            for i, (camp_name, camper) in enumerate(found, 1):
                table.add_row(str(i), camp_name, camper.name, camper.contact)
                
            console.print(table)
            
            console.print("[dim]Enter number to view Emergency/Medical Info, 's' to search again, or 'b' to back[/dim]")
            choice = get_input("Choice (enter a number): ")
            
            if choice.lower() == 's':
                continue
            if choice.lower() == 'b':
                break
                
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(found):
                    camp_name, camper = found[idx]
                    console.print(Panel(f"""
[bold]Emergency Details[/bold]
[green]Name:[/green] {camper.name}
[green]Camp:[/green] {camp_name}
[green]Age:[/green] {camper.age}
[green]Contact:[/green] {camper.contact}
[yellow]Medical Info:[/yellow] {camper.medical_info or 'None'}
""", style="red"))
                    wait_for_enter()
                    continue
            
            console_manager.print_error("Invalid selection.")

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
            "activities": summary["activities"],
            "achievements": summary["achievements"],
        }

        self.daily_report_manager.add_report(report)
        console_manager.print_success("Report saved.")
        wait_for_enter()


    @cancellable
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


    @cancellable
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


    @cancellable
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

    @cancellable
    def activities_menu(self):
        while True:
            console.print(Panel("""
[bold]Activity Management[/bold]
1. Add Activities to Camp
2. View Camp Activities
3. Add New Activity to Library
4. Search Activity Library
""", style="blue"))

            choice = get_input("Choose an option: ")

            if choice == "1":
                self.add_activities_to_camp()
            elif choice == "2":
                self.view_camp_activities()
            elif choice == "3":
                self.add_activity_to_library()
            elif choice == "4":
                self.search_activity()
            elif choice.lower() == "b":
                break
            else:
                console_manager.print_error("Invalid choice.")

    @cancellable
    def search_activity(self):
        """Search for an activity in the library."""
        activity_library = self._load_activity_library()
        
        if not activity_library:
            console_manager.print_error("Activity library is empty.")
            return
            
        query = get_input("Enter activity name (or part of name): ").lower()
        
        matches = [a for a in activity_library if query in a.lower()]
        
        if not matches:
            console_manager.print_info(f"No activities found matching '{query}'.")
            wait_for_enter()
            return
            
        console.print(Panel(f"Found {len(matches)} activities:", style="blue"))
        for a in matches:
            console.print(f"• {a}")
            
        wait_for_enter()

    @cancellable
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

    @cancellable
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

    @cancellable
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
        wait_for_enter()

