from handlers.base_handler import BaseHandler
from cli.input_utils import get_input, cancellable, wait_for_enter
from cli.prompts import get_index_from_options
from services.activity_service import ActivityService
from cli.leader_display import leader_display
from models.activity import Activity, Session

class ActivityHandler(BaseHandler):
    def __init__(self, user, context):
        super().__init__(user, context)
        self.activity_service = ActivityService(self.context.activity_manager, self.context.camp_manager)
        self.display = leader_display

    @cancellable
    def activities_menu(self):
        while True:
            self.display.display_activities_menu()

            choice = get_input("Choose an option or 'b' to go back: ")

            if choice == "1":
                self.add_activities_to_camp()
            elif choice == "2":
                self.view_camp_activities()
            elif choice == "3":
                self.add_activity_to_library()
            elif choice == "4":
                self.search_activity()
            elif choice == "5":
                self.manage_activity_roster()
            elif choice == "6":
                self.remove_activity()
            elif choice.lower() == "b":
                break
            else:
                self.display.display_error("Invalid choice.")

    @cancellable
    def view_weekly_schedule(self):
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]
        
        if not my_camps:
            self.display.display_error("You don't supervise any camps.")
            return

        camp = self._select_camp_delegated()
        if not camp: return

        self.display.display_weekly_schedule(camp)
        wait_for_enter()

    @cancellable
    def remove_activity(self):
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]
        
        if not my_camps:
            self.display.display_error("You don't supervise any camps.")
            return

        camp = self._select_camp_delegated()
        if not camp: return

        if not camp.activities:
            self.display.display_error("No activities scheduled.")
            return

        # Simple selection list
        options = []
        for act in camp.activities:
             name = act.get('name')
             date = act.get('date')
             sess = act.get('session')
             options.append(f"{name} ({date} - {sess})")
        
        idx = get_index_from_options("Select Activity to Remove", options)
        if idx is None: return
        activity_to_remove = camp.activities[idx]

        self.display.confirm_activity_removal(activity_to_remove)
        confirm = get_input("Type 'yes' to confirm: ")
        
        if confirm.lower() == "yes":
            success, message = self.activity_service.remove_activity(camp.name, idx)
            if success:
                self.display.display_success(message)
            else:
                self.display.display_error(message)
        else:
            self.display.display_info("Actions cancelled.")
        wait_for_enter()

    @cancellable
    def search_activity(self):
        """Search for an activity in the library."""
        query = get_input("Enter activity name (or part of name): ").lower()
        
        matches = self.activity_service.search_library(query)
        
        if not matches:
            self.display.display_info(f"No activities found matching '{query}'.")
            wait_for_enter()
            return
            
        self.display.display_search_activity_results(matches)
            
        wait_for_enter()

    @cancellable
    def add_activities_to_camp(self):
        camps = self.context.camp_manager.read_all()
        # Filter for camps supervised by current user
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            self.display.display_error("You don't supervise any camps.")
            return

        camp = self._select_camp_delegated()
        if not camp: return

        if not camp.campers:
            self.display.display_error("Camp has no campers. Add campers before scheduling activities.")
            return

        activity_library = self.activity_service.get_library()
        if not activity_library:
            self.display.display_error("Activity Library is empty. Add new activity types to the library first (Option 3).")
            return
        
        # 1. Select Date
        camp_dates = camp.get_date_range()
        date_index = get_index_from_options("Select Date", camp_dates)
        if date_index is None: return
        selected_date = camp_dates[date_index]

        # 2. Select Session
        session_names = [s.name for s in Session]
        session_index = get_index_from_options("Select Session", session_names)
        if session_index is None: return
        session_name = session_names[session_index]

        # 3. Select Activity from Library
        activity_names = list(activity_library.keys())
        activity_index = get_index_from_options("Select Activity Type", activity_names)
        if activity_index is None: return
        activity_name = activity_names[activity_index]

        # Try to schedule
        success, message, conflict_activity = self.activity_service.schedule_activity(camp.name, activity_name, selected_date, session_name)

        if not success:
            if conflict_activity:
                self.display.display_conflict_resolution(conflict_activity, activity_name)
                options = ["Replace Existing Activity", "Cancel"]
                choice = get_index_from_options("Choose Action", options)
                
                if choice == 0: # Replace
                    success, message, _ = self.activity_service.schedule_activity(camp.name, activity_name, selected_date, session_name, force_replace=True)
                    if success:
                        self.display.display_success(message)
                    else:
                        self.display.display_error(message)
                else: # Cancel
                    self.display.display_info("Scheduling cancelled.")
            else:
                self.display.display_error(message)
        else:
            self.display.display_success(message)


    @cancellable
    def manage_activity_roster(self):
        camp = self._select_camp_delegated()
        if not camp: return

        if not camp.activities:
            self.display.display_error("No activities scheduled for this camp.")
            return

        # Helper to display simple list of activities for selection
        # Create a temporary list of (index, activity_dict) to map selection back
        activity_options = []
        for act in camp.activities:
             name = act.get('name')
             date = act.get('date')
             sess = act.get('session')
             activity_options.append(f"{name} ({date} - {sess})")

        act_idx = get_index_from_options("Select Activity to Manage", activity_options)
        if act_idx is None: return
        selected_activity = camp.activities[act_idx]
        
        while True:
            # Display current roster status
            current_ids = selected_activity.get('camper_ids', [])
            roster_names = []
            for cid in current_ids:
                roster_names.append(cid)

            self.display.display_info(f"\nActivity: {selected_activity['name']} ({selected_activity['date']} - {selected_activity['session']})")
            self.display.display_info(f"Current Roster ({len(current_ids)}): {', '.join(roster_names) if roster_names else 'Empty'}")
            
            menu = ["Add Camper", "Remove Camper", "Add All Campers", "Back"]
            choice_idx = get_index_from_options("Roster Actions", menu)

            if choice_idx == 0: # Add
                self.add_camper_to_activity(selected_activity, camp, act_idx)
            elif choice_idx == 1: # Remove
                self.remove_camper_from_activity(selected_activity, camp, act_idx)
            elif choice_idx == 2: # Add All
                self.add_all_campers_to_activity(selected_activity, camp, act_idx)
            else:
                break

    def add_all_campers_to_activity(self, activity_data, camp, activity_index):
        success, message = self.activity_service.add_all_campers_to_activity(camp.name, activity_index)
        if success:
            self.display.display_success(message)
        else:
            self.display.display_info(message)
            wait_for_enter()

    def add_camper_to_activity(self, activity_data, camp, activity_index):
        current_ids = activity_data.get('camper_ids', [])
        
        available_campers = [c for c in camp.campers if c.name not in current_ids]
        
        if not available_campers:
            self.display.display_error("No available campers to add (all are already assigned).")
            return

        options = [c.name for c in available_campers]
        idx = get_index_from_options("Select Camper to Add", options)
        if idx is None: return
        camper_to_add = available_campers[idx]

        success, message = self.activity_service.add_camper_to_activity(camp.name, activity_index, camper_to_add.name)
        if success:
            self.display.display_success(message)
        else:
            self.display.display_error(message)

    def remove_camper_from_activity(self, activity_data, camp, activity_index):
        current_ids = activity_data.get('camper_ids', [])
        if not current_ids:
            self.display.display_error("Roster is empty.")
            return

        idx = get_index_from_options("Select Camper to Remove", current_ids)
        if idx is None: return
        removed_name = current_ids[idx]
        
        success, message = self.activity_service.remove_camper_from_activity(camp.name, activity_index, removed_name)
        if success:
            self.display.display_success(message)
        else:
            self.display.display_error(message)


    @cancellable
    def view_camp_activities(self):
        camps = self.context.camp_manager.read_all()
        my_camps = [c for c in camps if c.camp_leader == self.user.username]

        if not my_camps:
            self.display.display_error("You don't supervise any camps.")
            return

        # Simple selection again
        self.display.display_camp_selection_simple(my_camps)
        choice = get_input("Choose camp number: ")
        try:
            index = int(choice) - 1
            if not (0 <= index < len(my_camps)):
                 return
            camp = my_camps[index]
        except:
             return

        if not camp.activities:
            self.display.display_error("No activities assigned to this camp yet.")
            return

        self.display.display_camp_activities(camp)
        wait_for_enter()

    @cancellable
    def add_activity_to_library(self):
        activity_library = self.activity_service.get_library()

        self.display.display_activity_library(activity_library)

        new_activity = get_input("Enter new activity name: ").strip()

        if not new_activity:
            self.display.display_error("Activity name cannot be empty.")
            return

        is_indoor = get_input("Is this an indoor activity? (y/n): ").lower() == 'y'

        success, message = self.activity_service.add_to_library(new_activity, is_indoor)

        if not success:
             self.display.display_error(message)
             return

        self.display.display_success(message)
        wait_for_enter()

    def _select_camp_delegated(self):
        """
        Helper to select a camp for the current leader.
        """
        my_camps = self.context.camp_manager.get_camps_by_leader(self.user.username)
        
        if not my_camps:
            self.display.display_error("You do not supervise any camps.")
            return None

        self.display.display_camp_selection_simple(my_camps)
        
        while True:
            choice = get_input("Choose camp number: ")
            if not choice.isdigit():
                 self.display.display_error("Invalid input. Enter a number.")
                 continue

            index = int(choice) - 1
            if 0 <= index < len(my_camps):
                return my_camps[index]
            
            self.display.display_error("Invalid selection. Try again.")
