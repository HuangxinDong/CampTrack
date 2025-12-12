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
from models.resource import Equipment
from cli.console_manager import console_manager
from services.weather_service import WeatherService
from rich.table import Table
from rich.console import Console

class CoordinatorHandler(BaseHandler):
    """Handles Coordinator-specific actions."""

    def __init__(self, user, context):
        super().__init__(user, context)

        self.display = coordinator_display

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
        camps = self.context.camp_manager.read_all()
        
        # 1. Name Validation
        while True:
            name = get_input("Enter camp name: ")
            if not name.strip():
                console_manager.print_error("Camp name cannot be empty.")
                continue
            if any(camp.name == name for camp in camps):
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
                if end_date < start_date:
                    console_manager.print_error(f"End date must be on or after start date ({start_date}).")
                    continue
                break
            except ValueError:
                console_manager.print_error("Invalid date format. Please use yyyy-mm-dd.")

        food = get_positive_int("Enter camp food stock: ")

        camp = Camp(
            camp_id=str(uuid.uuid4()),
            name=name,
            location=location,
            camp_type=camp_type,
            start_date=start_date,
            end_date=end_date,
            initial_food_stock=food,
        )
        self.context.camp_manager.add(camp)
        # Use new display class for success message
        coordinator_display.display_camp_creation_success(camp)
        self.context.audit_log_manager.log_event(self.user.username, "Create Camp", f"Created camp {camp.name}")
        
        if get_input("Do you want to assign a leader now? (y/n): ").lower() == 'y':
            self._assign_leader_to_camp(camp)
        
        wait_for_enter()

    def edit_camp_resources(self):
        """Switch to camp editing submenu."""
        self.commands = [
            {"name": "Top Up Food Stock", "command": self.top_up_food_stock},
            {"name": "Edit Camp Location", "command": self.edit_camp_location},
            {"name": "Edit Camp Dates", "command": self.edit_camp_dates},
            {"name": "Assign/Change Camp Leader", "command": self.assign_camp_leader},
        ]

    @cancellable
    def assign_camp_leader(self):
        """Assign or change the leader for a camp."""
        camps = self.context.camp_manager.read_all()
        if not camps:
            console_manager.print_error("No camps available.")
            return

        coordinator_display.display_camp_list(camps)
        
        while True:
            selection = get_input("\nEnter camp number to assign leader: ")
            if selection.isdigit() and 1 <= int(selection) <= len(camps):
                break
            console_manager.print_error("Invalid selection.")

        selected_camp = camps[int(selection) - 1]
        self._assign_leader_to_camp(selected_camp)
        wait_for_enter()

    def _assign_leader_to_camp(self, camp):
        """Helper to assign a leader to a camp with validation."""
        while True:
            username = self.get_username_with_search("Enter leader username", role_filter="Leader")
            user = self.context.user_manager.find_user(username)
            
            if not user:
                console_manager.print_error(f"User '{username}' not found.")
                continue
                
            if user.get('role') != 'Leader':
                console_manager.print_error(f"User '{username}' is not a Leader (Role: {user.get('role')}).")
                continue
                
            # Conflict Check
            # We need to check if this user is leading other camps that overlap with THIS camp
            # Temporarily set leader to check conflicts (or pass username explicitly if I refactor _get_conflicting_camps)
            
            # Let's manually check here to be safe and explicit
            all_camps = self.context.camp_manager.read_all()
            conflicts = []
            for other in all_camps:
                if other.camp_id == camp.camp_id:
                    continue
                if other.camp_leader == username:
                    if Camp.dates_overlap(camp.start_date, camp.end_date, other.start_date, other.end_date):
                        conflicts.append(other.name)
            
            if conflicts:
                console_manager.print_error(f"Conflict detected! {username} is already leading: {', '.join(conflicts)} during this period.")
                if get_input("Assign anyway? (y/n): ").lower() != 'y':
                    continue
            
            break
            
        camp.camp_leader = username
        self.context.camp_manager.update(camp)
        console_manager.print_success(f"Leader '{username}' assigned to camp '{camp.name}'.")
        self.context.audit_log_manager.log_event(self.user.username, "Assign Leader", f"Assigned {username} to {camp.name}")

    @cancellable
    def top_up_food_stock(self):
        camps = self.context.camp_manager.read_all()
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
        try:
            selected_camp.add_food(additional_food)
            self.context.camp_manager.update(selected_camp)

            from cli.console_manager import console_manager

            console_manager.print_success(
                f"Food stock for camp '{selected_camp.name}' has been topped up by {additional_food}."
            )
            self.context.audit_log_manager.log_event(self.user.username, "Top Up Food", f"Added {additional_food} to {selected_camp.name}")
            wait_for_enter()
        except ValueError as e:
            from cli.console_manager import console_manager

            console_manager.print_error(f"Error: {e}")

        self.commands = self.main_commands

    @cancellable
    def edit_camp_location(self):
        """Allow coordinator to edit a camp's location."""
        camps = self.context.camp_manager.read_all()
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
        if not new_location.strip():
            console_manager.print_error("Location cannot be empty.")
            return

        # Update and save
        selected_camp.location = new_location.strip()
        self.context.camp_manager.update(selected_camp)

        console_manager.print_success(f"Location for '{selected_camp.name}' updated to '{new_location}'.")
        self.context.audit_log_manager.log_event(self.user.username, "Edit Camp Location", f"Changed {selected_camp.name} location to {new_location}")
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

        # Check for leader conflicts
        if selected_camp.camp_leader:
            conflicting_camps = self._get_conflicting_camps(selected_camp, new_start, new_end)

            if conflicting_camps:
                # Display conflict warning
                conflict_names = ", ".join(c.name for c in conflicting_camps)
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
                    selected_camp.camp_leader = None
                    console_manager.print_success(
                        f"Leader unassigned from '{selected_camp.name}'."
                    )
                else:
                    console_manager.print_error("Date change cancelled.")
                    self.commands = self.main_commands
                    return

        # Apply date changes
        selected_camp.start_date = new_start
        selected_camp.end_date = new_end
        self.context.camp_manager.update(selected_camp)

        console_manager.print_success(
            f"Dates for '{selected_camp.name}' updated to {new_start} - {new_end}."
        )
        self.commands = self.main_commands

    def _get_conflicting_camps(self, camp: Camp, new_start: date, new_end: date) -> list:
        """
        Find camps that would conflict with new dates for this camp's leader.

        Args:
            camp: The camp being edited
            new_start: Proposed new start date
            new_end: Proposed new end date

        Returns:
            list[Camp]: Camps with overlapping dates (excluding the camp being edited)
        """
        if not camp.camp_leader:
            return []

        leader_camps = self.context.camp_manager.get_camps_by_leader(camp.camp_leader)
        conflicts = []

        for other_camp in leader_camps:
            # Skip the camp being edited
            if other_camp.camp_id == camp.camp_id:
                continue

            # Use model's static method for overlap check
            if Camp.dates_overlap(new_start, new_end, other_camp.start_date, other_camp.end_date):
                conflicts.append(other_camp)

        return conflicts

    @cancellable
    def set_daily_payment_limit(self):
        while True:
            scout_leader_name = self.get_username_with_search("Enter the name of the scout leader", role_filter="Leader")
            scout_leader = self.context.user_manager.find_user(scout_leader_name)
            
            if not scout_leader:
                console_manager.print_error(f"User '{scout_leader_name}' not found. Please try again.")
                continue

            if scout_leader["role"] != "Leader":
                console_manager.print_error(f"User '{scout_leader_name}' is not a Leader.")
                continue
            
            break

        old_rate = scout_leader.get(
            "daily_restock_limit", 0
        )  # Assumed key, checking user model would be safer, but relying on context logic often used.
        # Actually daily_payment_rate for Leader... checking user_manager usage.
        # user_manager.update_daily_payment_rate updates 'daily_payment_rate'
        old_rate = scout_leader.get("daily_payment_rate", "N/A")

        daily_payment_rate = get_positive_int("Enter the new daily payment rate: ")
        self.context.user_manager.update_daily_payment_rate(scout_leader["username"], daily_payment_rate)

        coordinator_display.display_payment_update_success(scout_leader_name, old_rate, daily_payment_rate)
        self.context.audit_log_manager.log_event(self.user.username, "Set Payment Limit", f"Set {scout_leader_name} rate to {daily_payment_rate}")

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


        print(f"\nTotal Camps: {len(df)}")

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

            new_eq = Equipment(
                resource_id=str(uuid.uuid4()),
                name = name,
                camp_id=camp.camp_id,
                target_quantity=target,
                current_quantity=current,
                condition=condition

            )

            camp.equipment.append(new_eq)
            self.context.camp_manager.update(camp)
            console_manager.print_success(f"Added {name} to {camp.name}.")
            

