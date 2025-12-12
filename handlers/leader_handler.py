from datetime import datetime
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

from handlers.activity_handler import ActivityHandler
from cli.leader_display import leader_display

from services.weather_service import WeatherService
from rich.table import Table
from rich.console import Console
from rich import box
import pandas as pd

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
        self.display = leader_display
        self.activity_handler = ActivityHandler(user, context)

        self.commands = self.parent_commands + [
            {"name": "Select Camps to Supervise", "command": self.select_camps},
            {"name": "Edit Camp Food Settings", "command": self.edit_camp},
            {"name": "Assign Campers from CSV", "command": self.assign_campers_ui},
            {"name": "View Campers", "command": self.view_campers},
            {"name": "Search Campers for Emergency Details", "command": self.search_camper},
            {"name": "Manage Activities", "command": self.activities_menu},
            {"name": "View Camp Schedules", "command": self.view_camp_schedules},
            {"name": "Daily Reports", "command": self.daily_reports_menu},
            {"name": "View My Statistics", "command": self.show_statistics},
            {"name": "View Equipment", "command": self.view_equipment},
            {"name": "View Camp Schedules", "command": self.view_camp_schedules},
            {"name": "View Weather Forecast", "command": self.view_weather_forecast},
        ]

        self.main_commands = self.commands.copy()


    @cancellable
    def select_camps(self):
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        self.display.display_camp_selection(camps, self.user.username)

        while True:
            choice = get_input("Enter camp number to supervise or 'b' to go back: ")

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
            self.display.display_error("You don't supervise any camps.")
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

        self.display.display_camp_food_update(camp, total_required, num_campers, days, new_food)
        wait_for_enter()


    @cancellable
    def assign_campers_ui(self):
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            self.display.display_error("You don't supervise any camps.")
            return

        camp = self._select_camp(my_camps)
        if not camp:
            return

        csv_files = self.context.camper_manager.get_available_csv_files()
        
        # UI: Get selection
        csv_file = self.display.select_csv_file(csv_files)
        if not csv_file:
            return

        try:
            # Data: Perform import (validation is handled inside)
            results = self.context.camper_manager.import_campers_from_csv(camp, csv_file, self.context)
            
            # UI: Show results
            self.display.display_import_results(results, camp.name)

        except Exception as e:
            self.display.display_error(f"Unexpected Error during import: {e}")
            wait_for_enter()


    @cancellable
    def view_campers(self):
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            self.display.display_error("You supervise no camps.")
            return

        camp = self._select_camp(my_camps)
        if not camp:
            return

        self.display.display_campers(camp)
        wait_for_enter()

    @cancellable
    def search_camper(self):
        """Search for a camper in supervised camps (Global Search & Emergency Info)."""
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]
        
        if not my_camps:
            self.display.display_error("You don't supervise any camps.")
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
                
            self.display.display_camper_search_results(found)
            
            while True:
                choice = get_input("Choice (enter a number): ")
                
                if choice.lower() == 's':
                    break
                if choice.lower() == 'b':
                    return
                    
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(found):
                        camp_name, camper = found[idx]
                        self.display.display_emergency_details(camper, camp_name)
                        wait_for_enter()
                        break
                    else:
                        console_manager.print_error("Invalid selection. Please try again.")
                else:
                    console_manager.print_error("Invalid selection. Please try again.")

    @cancellable
    def daily_reports_menu(self):
        while True:
            self.display.display_daily_reports_menu()

            choice = get_input("Choose an option or 'b' to go back: ")

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
            self.display.display_error("You supervise no camps.")
            return

        camp = self._select_camp(my_camps)
        if not camp:
            return

        # Validation: Cannot create report for future camps
        today = datetime.now().date()
        try:
            camp_start = datetime.strptime(str(camp.start_date), "%Y-%m-%d").date()
        except ValueError:
             # Fallback if date format is different or already a date object
             camp_start = camp.start_date if isinstance(camp.start_date, datetime) else datetime.now().date()

        if camp_start > today:
            console_manager.print_error(f"Cannot create a report for '{camp.name}' because it has not started yet (Starts: {camp.start_date}).")
            wait_for_enter()
            return

        text = get_input("Enter report text(please include any achievements or key activities): ")
        daily_participation = get_positive_int("How many campers participated today? ")

        summary = LeaderHandler.extract_summary(text)

        today_str = datetime.now().date().isoformat()
        todays_activities = [
            act.get('name') for act in camp.activities 
            if act.get('date') == today_str
        ]

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
            "activities": todays_activities,
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
            self.display.display_error("You supervise no camps.")
            return

        camp = self._select_camp(my_camps)
        if not camp:
            return

        reports = [
            r for r in self.daily_report_manager.read_all()
            if r["camp_id"] == camp.camp_id
        ]

        if not reports:
            console_manager.print_info("No reports available.")
            return

        reports.sort(key=lambda r: r["date"], reverse=True)

        self.display.display_daily_reports_list(reports)
        wait_for_enter()


    @cancellable
    def delete_daily_report(self):
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            self.display.display_error("You supervise no camps.")
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

        self.display.display_reports_for_deletion(reports)

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
            console_manager.print_warning("You are not supervising any camps.")
            wait_for_enter()
            return

        stats_data = []
        all_reports = self.daily_report_manager.read_all()  
        total_earnings = 0
        
        for camp in my_camps:
            total_participants = self.statistics.get_total_participants(camp)
            
            if not camp.has_camp_started():
                avg_rate_str = "N/A"
                earnings_str = "N/A"
                earnings = 0
            else:
                avg_rate = self.statistics.get_average_participation_rate(camp)  
                avg_rate_str = f"{avg_rate * 100:.1f}%" if avg_rate > 0 else "0%"
                earnings = self.statistics.get_earnings(self.user.username, camp)
                earnings_str = f"£{earnings}"

            food_usage = self.statistics.get_food_usage(camp)
            camp_reports = [r for r in all_reports if r["camp_id"] == camp.camp_id]
            incident_count = sum(int(r.get("injured_count", 0)) for r in camp_reports)
            activity_count = sum(len(r.get("activities", [])) for r in camp_reports)
            achievement_count = sum(len(r.get("achievements", [])) for r in camp_reports)
            
            total_earnings += earnings

            stats_data.append({
                "camp_name": camp.name,
                "campers": str(total_participants),
                "participation": avg_rate_str,
                "food_used": str(food_usage),
                "incidents": str(incident_count),
                "activities": str(activity_count),
                "achievements": str(achievement_count),
                "earnings": earnings_str
            })

        self.display.display_statistics(stats_data, total_earnings)
        wait_for_enter()



    def _select_camp(self, camps):
        self.display.display_camp_selection_simple(camps)

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

        try:
            return camps[int(choice) - 1]
        except:
            console_manager.print_error("Invalid selection.")
            return None
        
    @cancellable
    def view_equipment(self):
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            console_manager.print_error("You are not supervising any camps.")
            return
        
        for camp in my_camps:
            console_manager.print_header(f"Equipment Checklist: {camp.name}")

        if not camp.equipment:
            print(" No equipment listed")
            continue

        print(f" {'Item':<20} | {'Qty':<10} | {'Status':<10}")
        print(" " + "-"*45)

        for eq in camp.equipment:
            qty_str = f"{eq.current_quantity}/{eq.target_quantity}"
            if eq.current_quantity < eq.target_quantity:
                qty_str = f"[bold red]{qty_str}[/bold red]"

            print(f" {eq.name:<20} | {qty_str:<25} | {eq.condition:<10}")
            print(" "+ "-"*45)


    
    @cancellable
    def activities_menu(self):
        self.activity_handler.activities_menu()

    @cancellable
    def view_camp_schedules(self):
        self.activity_handler.view_weekly_schedule()
    
    @cancellable
    def view_weather_forecast(self):
        camps = self.context.camp_manager.read_all()

        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            self.display.display_error("You don't supervise any camps")
            return
        
        camp = self._select_camp(my_camps)
        if not camp:
            return
        
        console = Console()
        with console.status("[bold green]Fetching live weather data, please hold on...[/]"):
            ws = WeatherService()
            df_forecast, error = ws.get_weekly_forecast(camp.location)

        if error:
            console_manager.print_error("No Weather Data Is Available Currently. Inconvenience is deeply regretted.")
            wait_for_enter()
            return
        
        if df_forecast is None:
            console_manager.print_error("No weather data returned.")
            wait_for_enter()
            return

        table = Table(title=f"7-Day Forecast for {camp.location}")
        table.add_column("date")
        table.add_column("Condition")

        for index, row in df_forecast.iterrows():
            status = row['status']
            color = "green" if status == "Good" else ("yellow" if status == "Rainy" else "red")
            table.add_row(str(row['date']), f"[{color}]{status}[/]")

        console_manager.console.print(table)

        self._display_weather_conflicts(camp, df_forecast)
        wait_for_enter()

    def _display_weather_conflicts(self, camp, df_forecast):
        forecast_map = pd.Series(df_forecast.status.values, index=df_forecast.date).to_dict()

        conflicts = []

        for activity in camp.activities:
            if isinstance(activity, dict):
                act_date = str(activity.get('date'))
                act_name = activity.get('name')
            else:
                act_date = str(activity.date)
                act_name = activity.name
                
            weather = forecast_map.get(act_date)

            if weather in ["Rainy", "Stormy"]:
                conflicts.append((act_date, act_name, weather))

        if conflicts:
            console_manager.console.print("\n[bold red] WEATHER ALERT FOR SCHEDULED ACTIVITIES[/]")

            alert_table = Table(box=box.SIMPLE)
            alert_table.add_column("Date")
            alert_table.add_column("Activity")
            alert_table.add_column("Forecast")

            for date, name, weather in conflicts:
                alert_table.add_row(date, name, f"[red]{weather}[/]")

            console_manager.console.print(alert_table)
        else:
            console_manager.console.print("\n[bold green]No bad weather conflicts for scheduled activities.[/]")

            


        
    

