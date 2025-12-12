# handlers/coordinator_handler.py
from datetime import datetime, date
import uuid
from cli.console_manager import console_manager
from models.camp import Camp
from handlers.base_handler import BaseHandler
from cli.input_utils import get_input, cancellable, wait_for_enter
from cli.prompts import get_positive_int
from cli.coordinator_display import coordinator_display
import cli.visualisations as visualisations
from cli.console_manager import console_manager
import uuid
from services.weather_service import WeatherService
from rich.table import Table
from rich.console import Console
from services.camp_service import CampService
from services.user_service import UserService

class CoordinatorHandler(BaseHandler):
    """Handles Coordinator-specific actions."""

    def __init__(self, user, context):
        super().__init__(user, context)

        self.display = coordinator_display
        self.camp_service = CampService(self.context.camp_manager)
        self.user_service = UserService(self.context.user_manager, self.context.camp_manager)

        self.commands = self.parent_commands + [
            {"name": "Create Camp", "command": self.create_camp},
            {"name": "Edit Camp", "command": self.edit_camp_resources},
            {
                "name": "Set Daily Payment Limit",
                "command": self.set_daily_payment_limit,
            },
            {"name": "See Visualizations", "command": self.visualization_menu},
            {"name": "View Dashboard", "command": self.view_dashboard},
            {"name": "Manage Equipment", "command": self.manage_equipment},
            {"name": "View Weather Forecast", "command": self.view_weather_forecast},
        ]

        self.main_commands = self.commands.copy()

    def get_notifications(self):
        notifications = []

        unread_alert = self.get_unread_message_alert()
        if unread_alert:
            notifications.append(unread_alert)

        food_shortage_messages = self.get_camps_with_food_shortages()
        notifications.extend(food_shortage_messages)

        return notifications

    def get_camps_with_food_shortages(self):
        camps = self.context.camp_manager.read_all()

        shortage_messages = [
            f"{camp.name} has a food shortage"
            for camp in camps
            if camp.is_food_shortage()
        ]

        return shortage_messages

    @cancellable
    def create_camp(self):
        # 1. Name Validation
        while True:
            name = get_input("Enter camp name: ")
            if not name.strip():
                console_manager.print_error("Camp name cannot be empty.")
                continue
            
            if not self.camp_service.is_name_unique(name):
                console_manager.print_error("Camp name already exists. Please enter a different name.")
            else:
                break
        
        # 2. Location Validation
        while True:
            location = get_input("Enter camp location: ")
            if location.strip():
                break
            console_manager.print_error("Location cannot be empty.")

        # 3. Type Validation
        while True:
            camp_type = get_input("Enter camp type: ")
            if camp_type.strip():
                break
            console_manager.print_error("Camp type cannot be empty.")

        # 4. Start Date Validation
        while True:
            start_date_str = get_input("Enter camp start date (yyyy-mm-dd): ")
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                if start_date < datetime.now().date():
                    console_manager.print_error("Start date cannot be in the past.")
                    continue
                break
            except ValueError:
                console_manager.print_error("Invalid date format. Please use yyyy-mm-dd.")

        # 5. End Date Validation
        while True:
            end_date_str = get_input("Enter camp end date (yyyy-mm-dd): ")
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                # Use service to validate date logic
                self.camp_service.validate_dates(start_date, end_date)
                break
            except ValueError as e:
                console_manager.print_error(str(e))

        food = get_positive_int("Enter camp food stock: ")

        try:
            camp = self.camp_service.create_camp(
                name=name,
                location=location,
                camp_type=camp_type,
                start_date=start_date,
                end_date=end_date,
                initial_food_stock=food
            )
            # Use new display class for success message
            coordinator_display.display_camp_creation_success(camp)
            self.context.audit_log_manager.log_event(self.user.username, "Create Camp", f"Created camp {camp.name}")
            
            if get_input("Do you want to assign a leader now? (y/n): ").lower() == 'y':
                self._assign_leader_to_camp(camp)
                
        except ValueError as e:
            console_manager.print_error(f"Failed to create camp: {e}")
        
        wait_for_enter()

    def _assign_leader_to_camp(self, camp):
        """Helper to assign a leader to a camp."""
        # Get all leaders
        users = self.user_service.get_all_users()
        leaders = [u for u in users if u['role'] == 'Leader']
        
        if not leaders:
            console_manager.print_error("No leaders found in the system.")
            return

        # Filter available leaders
        available_leaders = []
        for leader in leaders:
            conflicts = self.camp_service.get_conflicting_camps(leader['username'], camp.start_date, camp.end_date, camp.camp_id)
            if not conflicts:
                available_leaders.append(leader)
        
        if not available_leaders:
            console_manager.print_error("No available leaders for these dates.")
            return

        console_manager.print_menu("Available Leaders", [l['username'] for l in available_leaders])
        
        while True:
            choice = get_input("Select leader number: ")
            if not choice.isdigit(): continue
            idx = int(choice) - 1
            if 0 <= idx < len(available_leaders):
                selected_leader = available_leaders[idx]
                break
        
        # Assign
        success, message = self.camp_service.assign_leader(camp.name, selected_leader['username'])
        if success:
            console_manager.print_success(message)
            self.context.audit_log_manager.log_event(self.user.username, "Assign Leader", f"Assigned {selected_leader['username']} to {camp.name}")
        else:
            console_manager.print_error(message)

    def edit_camp_resources(self):
        """Switch to camp editing submenu."""
        self.commands = [
            {"name": "Top Up Food Stock", "command": self.top_up_food_stock},
            {"name": "Edit Camp Location", "command": self.edit_camp_location},
            {"name": "Edit Camp Dates", "command": self.edit_camp_dates},
        ]


    @cancellable
    def top_up_food_stock(self):
        camps = self.context.camp_manager.read_all()
        camps.sort(key=lambda c: c.start_date)
        if not camps:
            print("No camps available.")
            return

        print("Camps:")
        # Use new display class for camp list
        coordinator_display.display_camp_list(camps)

        while True:
            invalid_selection_error_message = "Please select a number from the list"
            selection = get_input("\nEnter camp number to topup food:")
            if not selection.isdigit():
                print(invalid_selection_error_message)
                continue
            selected_number = int(selection)
            if not (1 <= selected_number <= len(camps)):
                print(invalid_selection_error_message)
                continue
            break

        selected_camp = camps[selected_number - 1]
        if not selected_camp:
            print("Camp not found")
            return
        additional_food = get_positive_int("Enter the amount of food to add: ")
        
        success, message = self.camp_service.top_up_food(selected_camp.name, additional_food)
        if success:
            console_manager.print_success(message)
            self.context.audit_log_manager.log_event(self.user.username, "Top Up Food", f"Added {additional_food} to {selected_camp.name}")
            wait_for_enter()
        else:
            console_manager.print_error(f"Error: {message}")

        self.commands = self.main_commands

    @cancellable
    def edit_camp_location(self):
        """Allow coordinator to edit a camp's location."""
        camps = self.context.camp_manager.read_all()
        camps.sort(key=lambda c: c.start_date)
        if not camps:
            console_manager.print_error("No camps available.")
            return

        # Display camps for selection
        coordinator_display.display_camp_list(camps)

        # Select camp
        while True:
            selection = get_input("\nEnter camp number to edit location: ")
            if not selection.isdigit():
                console_manager.print_error("Please select a number from the list.")
                continue
            selected_idx = int(selection)
            if not (1 <= selected_idx <= len(camps)):
                console_manager.print_error("Please select a number from the list.")
                continue
            break

        selected_camp = camps[selected_idx - 1]

        # Show current location
        console_manager.console.print(f"Current location: [bold]{selected_camp.location}[/bold]")

        # Get new location
        new_location = get_input("Enter new location: ")
        
        success, message = self.camp_service.update_location(selected_camp.name, new_location)
        if success:
            console_manager.print_success(message)
            self.context.audit_log_manager.log_event(self.user.username, "Edit Camp Location", f"Changed {selected_camp.name} location to {new_location}")
        else:
            console_manager.print_error(message)
            
        self.commands = self.main_commands

    @cancellable
    def edit_camp_dates(self):
        """
        Allow coordinator to edit a camp's dates with conflict detection.

        Business Rules:
        - Cannot edit if camp started/finished
        - New dates cannot be in the past
        - If leader assigned and dates conflict: offer choice to unassign or cancel
        """
        from cli.prompts import get_valid_date_range

        camps = self.context.camp_manager.read_all()
        camps.sort(key=lambda c: c.start_date)

        if not camps:
            console_manager.print_error("No camps available.")
            return

        # Display camps for selection
        coordinator_display.display_camp_list(camps)

        # Select camp
        while True:
            selection = get_input("\nEnter camp number to edit dates: ")
            if not selection.isdigit():
                console_manager.print_error("Please select a number from the list.")
                continue
            selected_idx = int(selection)
            if not (1 <= selected_idx <= len(camps)):
                console_manager.print_error("Please select a number from the list.")
                continue
            break

        selected_camp = camps[selected_idx - 1]

        # Check if dates can be edited (business rule in model)
        can_edit, reason = selected_camp.can_edit_dates()
        if not can_edit:
            console_manager.print_error(reason)
            self.commands = self.main_commands
            return

        # Show current dates
        console_manager.console.print(
            f"Current dates: [bold]{selected_camp.start_date}[/bold] to [bold]{selected_camp.end_date}[/bold]"
        )

        # Get new dates (validated by prompts function)
        new_start, new_end = get_valid_date_range(
            start_prompt="Enter new start date (yyyy-mm-dd): ",
            end_prompt="Enter new end date (yyyy-mm-dd): "
        )

        success, message, conflicts = self.camp_service.update_dates(selected_camp.name, new_start, new_end)
        
        if not success:
            if conflicts:
                conflict_names = ", ".join(c.name for c in conflicts)
                console_manager.print_error(
                    f"Schedule conflict detected! Leader '{selected_camp.camp_leader}' "
                    f"is also assigned to: {conflict_names}"
                )

                # Offer choice
                console_manager.console.print("\nOptions:")
                console_manager.console.print("  1. Unassign leader from this camp and proceed")
                console_manager.console.print("  2. Cancel date change")

                choice = get_input("Enter choice (1 or 2): ")

                if choice == "1":
                    success, message, _ = self.camp_service.update_dates(selected_camp.name, new_start, new_end, force_unassign_leader=True)
                    if success:
                        console_manager.print_success(message)
                        console_manager.print_success(f"Leader unassigned from '{selected_camp.name}'.")
                    else:
                        console_manager.print_error(message)
                else:
                    console_manager.print_error("Date change cancelled.")
            else:
                console_manager.print_error(message)
        else:
            console_manager.print_success(message)

        self.commands = self.main_commands



    @cancellable
    def set_daily_payment_limit(self):
        while True:
            scout_leader_name = self.get_username_with_search("Enter the name of the scout leader", role_filter="Leader")
            scout_leader = self.user_service.get_user(scout_leader_name)
            
            if not scout_leader:
                console_manager.print_error(f"User '{scout_leader_name}' not found. Please try again.")
                continue

            if scout_leader["role"] != "Leader":
                console_manager.print_error(f"User '{scout_leader_name}' is not a Leader.")
                continue
            
            break

        old_rate = scout_leader.get("daily_payment_rate", "N/A")

        daily_payment_rate = get_positive_int("Enter the new daily payment rate: ")
        
        success, message = self.user_service.update_daily_payment_rate(scout_leader["username"], daily_payment_rate)
        
        if success:
            coordinator_display.display_payment_update_success(scout_leader_name, old_rate, daily_payment_rate)
            self.context.audit_log_manager.log_event(self.user.username, "Set Payment Limit", f"Set {scout_leader_name} rate to {daily_payment_rate}")
        else:
            console_manager.print_error(message)

    def restore_main_commands(self):
        self.commands = self.main_commands

    def visualization_menu(self):
        self.commands = [
            {
                "name": "Show Food Stock Chart",
                "command": lambda: visualisations.plot_food_stock(self.context.camp_manager),
            },
            {
                "name": "Show Campers per Camp Chart",
                "command": lambda: visualisations.plot_campers_per_camp(self.context.camp_manager),
            },
            {
                "name": "Show Location Distribution",
                "command": lambda: visualisations.plot_camp_location_distribution(self.context.camp_manager),
            },
        ]

    
    @cancellable
    def view_dashboard(self):
        # Phase 9C: Fetch Pandas-powered Overview
        overview_data = self.context.camp_manager.get_camp_overview_stats()
        
        # Phase 9B: Fetch Global Engagement Metrics
        metrics = self.context.camp_manager.get_global_activity_engagement()
        
        self.display.display_full_dashboard(overview_data, engagement_metrics=metrics)
        wait_for_enter()

    @cancellable
    def view_weather_forecast(self):
        camps = self.context.camp_manager.read_all()

        if not camps:
            console_manager.print_error("No camps available.")
            return
        
        self.display.display_camp_list(camps)

        while True:
            choice = get_input("Select camp number: ")
            if not choice.isdigit(): continue
            idx = int(choice) - 1
            if 0 <= idx < len(camps):
                camp = camps[idx]
                break

        console = Console()
        with console.status("[bold green]Fetching live weather data, Please wait...[/]"):
            ws = WeatherService()
            df_forecast, error = ws.get_weekly_forecast(camp.location)

        if error:
            console_manager.print_error(f"Weather Unavailable: {error}")
            wait_for_enter()
            return
        
        if df_forecast is None or df_forecast.empty:
            console_manager.print_error("No weather data returned. Inconvenience is deeply regretted.")
            wait_for_enter()
            return
        
        table = Table(title=f"7-Day Forecast for {camp.location}")
        table.add_column("Date")
        table.add_column("Condition")


        for index, row in df_forecast.iterrows():
            status = row['status']
            color = "green" if status == "Good" else ("yellow" if status == "Rainy" else "red")
            table.add_row(str(row['date']), f"[{color}]{status}[/]")


        console_manager.console.print(table)

        wait_for_enter()

    @cancellable
    def manage_equipment(self):
        camps = self.context.camp_manager.read_all()

        if not camps:
            console_manager.print_error("No camps available.")
            return
        
        console_manager.print_menu("\nSelect a Camp to manage equipment:", [f"{i+1}. {c.name}" for i, c in enumerate(camps)])

        try:
            choice = int(get_input("Enter number: ")) - 1
            camp = camps[choice]
        except (ValueError, IndexError):
            console_manager.print_error("Invalid selection")
            return
        

        if camp.equipment:
            console_manager.print_header(f"Equipment for {camp.name}")
            for eq in camp.equipment:
                status = "Okay" if eq.condition == "Good" else f"[red]{eq.condition}[/red]"
                console_manager.print_message(f"-{eq.name}: {eq.current_quantity}/{eq.target_quantity} (Cond: {status})")
        else:
            console_manager.print_info(f"No equipment assigned to {camp.name} yet.")

            if get_input("Add new equipment? (y/n): ").lower() != 'y':
                return
            
            name = get_input("Equipment Name: ")
            target = get_positive_int("Target Quantity (Total needed): ")
            current = get_positive_int("Current Quantity (Available now): ")
            condition = get_input("Condition (Good, Fair, Poor): ")

            success, message = self.camp_service.add_equipment(camp.name, name, target, current, condition)
            
            if success:
                console_manager.print_success(message)
            else:
                console_manager.print_error(message)
            wait_for_enter()
            

