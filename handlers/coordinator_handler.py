# handlers/coordinator_handler.py
from datetime import datetime, date
from cli.console_manager import console_manager
from models.camp import Camp
from handlers.base_handler import BaseHandler
from cli.input_utils import get_input, cancellable
from cli.prompts import get_positive_int
from cli.coordinator_display import coordinator_display
import cli.visualisations as visualisations

class CoordinatorHandler(BaseHandler):
    """Handles Coordinator-specific actions."""

    def __init__(self, user, context):
        super().__init__(user, context)

        self.commands = self.parent_commands + [
            {"name": "Create Camp", "command": self.create_camp},
            {"name": "Edit Camp", "command": self.edit_camp_resources},
            {
                "name": "Set Daily Payment Limit",
                "command": self.set_daily_payment_limit,
            },
            {"name": "See Visualizations", "command": self.visualization_menu},
        ]

        self.main_commands = self.commands.copy()

    @cancellable
    def create_camp(self):
        camps = self.context.camp_manager.read_all()
        while True:
            name = get_input("Enter camp name: ")
            if any(camp.name == name for camp in camps):
                console_manager.print_error("Camp name already exists. Please enter a different name.")
            else:
                break
        location = get_input("Enter camp location: ")
        camp_type = get_input("Enter camp type: ")

        while True:
            start_date_str = get_input("Enter camp start date (yyyy-mm-dd): ")
            end_date_str = get_input("Enter camp end date (yyyy-mm-dd): ")
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                
                if start_date < datetime.now().date():
                    print("Error: Start date cannot be in the past.")
                    continue

                if end_date < start_date:
                    print("Error: End date must be after start date.")
                    continue
                break
            except ValueError:
                print("Error: Invalid date format. Please use yyyy-mm-dd.")

        food = get_positive_int("Enter camp food stock: ")

        camp = Camp(
            camp_id=None,
            name=name,
            location=location,
            camp_type=camp_type,
            start_date=start_date,
            end_date=end_date,
            current_food_stock=food,
        )
        self.context.camp_manager.add(camp)
        # Use new display class for success message
        coordinator_display.display_camp_creation_success(camp)

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
        if not camps:
            print("No camps available.")
            return

        print("Camps:")
        # Use new display class for camp list
        coordinator_display.display_camp_list(camps)


        while True:
            invalid_selection_error_message = 'Please select a number from the list'
            selection = get_input("\nEnter camp number to topup food:")
            if not selection.isdigit():
                print(invalid_selection_error_message)
                continue
            selected_number = int(selection)
            if not (1 <= selected_number <= len(camps)):
                print(invalid_selection_error_message)
                continue
            break



        selected_camp = camps[selected_number -1]
        if not selected_camp:
            print("Camp not found")
            return
        additional_food = get_positive_int("Enter the amount of food to add: ")
        try:
            selected_camp.add_food(additional_food)
            self.context.camp_manager.update(selected_camp)
            
            from cli.console_manager import console_manager
            console_manager.print_success(f"Food stock for camp '{selected_camp.name}' has been topped up by {additional_food}.")
            get_input("(Press Enter to continue)")
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
        scout_leader_name = get_input("Enter the name of the scout leader: ")

        scout_leader = self.context.user_manager.find_user(scout_leader_name)
        if scout_leader is None:
            print("Cannot find user")
            return
        if scout_leader["role"] != "Leader":
            print("User is not a leader")
            return

        old_rate = scout_leader.get("daily_restock_limit", 0) # Assumed key, checking user model would be safer, but relying on context logic often used. 
        # Actually daily_payment_rate for Leader... checking user_manager usage.
        # user_manager.update_daily_payment_rate updates 'daily_payment_rate'
        old_rate = scout_leader.get("daily_payment_rate", "N/A")

        daily_payment_rate = get_positive_int("Enter the new daily payment rate: ")
        self.context.user_manager.update_daily_payment_rate(scout_leader["username"], daily_payment_rate)
        
        coordinator_display.display_payment_update_success(scout_leader_name, old_rate, daily_payment_rate)

    def restore_main_commands(self):
        self.commands = self.main_commands

    def visualization_menu(self):
        self.commands = [
             {'name': 'Show Food Stock Chart', 'command': lambda:
             visualisations.plot_food_stock(self.context.camp_manager)},
             {'name': 'Show Campers per Camp Chart', 'command': lambda:
               visualisations.plot_campers_per_camp(self.context.camp_manager)}, 
             {'name': 'Show Location Distribution', 'command': lambda:
              visualisations.plot_camp_location_distribution(self.context.camp_manager)},]
            
