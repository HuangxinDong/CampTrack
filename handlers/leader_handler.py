# handlers/leader_handler.py
from datetime import datetime
from handlers.base_handler import BaseHandler
from cli.input_utils import get_input, cancellable
from cli.prompts import get_positive_int


class LeaderHandler(BaseHandler):
    """Handles Leader-specific actions."""

    def __init__(self, user, user_manager, message_manager, camp_manager, announcement_manager):
        super().__init__(user, user_manager, message_manager, camp_manager, announcement_manager)
        self.camp_manager = camp_manager

        self.commands = self.parent_commands + [
            {
                "name": "Select Camps to Supervise",
                "command": self.select_camps_to_supervise,
            },
            {"name": "Edit Camp", "command": self.edit_camp},
        ]

        self.main_commands = self.commands.copy()


    @staticmethod
    def dates_conflict(start1, end1, start2, end2):
        return (start1 <= end2) and (end1 >= start2)

    @cancellable
    def select_camps_to_supervise(self):
        camps = self.camp_manager.read_all()

        if not camps:
            print("No camps available.")
            return

        print("\nAvailable camps:")
        for i, camp in enumerate(camps, 1):
            if camp.camp_leader == self.user.username:
                status = " (You are the leader)"
            elif camp.camp_leader:
                status = f" (Assigned to: {camp.camp_leader})"
            else:
                status = " (Available)"
            print(f"{i}. {camp.name} - {camp.location}{status}")

        print("\nEnter camp numbers to supervise, please seperate with commas:")
        print("Note: You can only select camps that are available or already yours.")
        selection = get_input("Your selection: ")

        try:
            selected_indices = [int(x.strip()) - 1 for x in selection.split(",")]
            my_camps = [c for c in camps if c.camp_leader == self.user.username]
            for index in selected_indices:
                if not (0 <= index < len(camps)):
                    print(f"Invalid selection: {index + 1}")
                    continue

                camp = camps[index]

                if camp.camp_leader and camp.camp_leader != self.user.username:
                    print(
                        f"Cannot select '{camp.name}' - already assigned to {camp.camp_leader}"
                    )
                    continue
                # check if the time is conflict
                new_start = datetime.strptime(str(camp.start_date), "%Y-%m-%d")
                new_end = datetime.strptime(str(camp.end_date), "%Y-%m-%d")

                conflict = False
                for c in my_camps:
                    s = datetime.strptime(c.start_date, "%Y-%m-%d")
                    e = datetime.strptime(c.end_date, "%Y-%m-%d")
                    if (new_start <= e) and (new_end >= s):
                        print(
                            f"Cannot select '{camp.name}' - schedule conflicts with '{c.name}'."
                        )
                        conflict = True
                        break
                if conflict:
                    continue

                if camp.camp_leader == self.user.username:
                    print(f"You are already supervising '{camp.name}'")
                    continue
                camp.assign_leader(self.user.username)
                self.camp_manager.update(camp)
                print(f"You are now supervising: {camp.name}")

        except ValueError:
            print("Invalid input. Please enter numbers separated by commas.")

    def edit_camp(self):
        camps = self.camp_manager.read_all()
        my_camps = [camp for camp in camps if camp.camp_leader == self.user.username]

        if not my_camps:
            print(
                "You are not supervising any camps. Use 'Select Camps to Supervise' first."
            )
            return

        print("\nYour camps:")
        for i, camp in enumerate(my_camps, 1):
            print(f"{i}. {camp.name} - {camp.location}")

        self.commands = [
            {
                "name": "Assign food per camper per day",
                "command": self.assign_food_per_camper_per_day,
            },
        ]

    @cancellable
    def assign_food_per_camper_per_day(self):
        camp_name = get_input("Enter the camp name to top up food stock for: ")
        camps = self.camp_manager.read_all()
        selected_camp = next((camp for camp in camps if camp.name == camp_name), None)

        if not selected_camp:
            print("Camp not found")
            return

        if selected_camp.camp_leader != self.user.username:
            print(
                "You cannot edit a camp if you are not a leader. Ask coordinator to add you."
            )
            return
        food_per_camper_per_day = get_positive_int("Enter food per camper per day: ")
        selected_camp.food_per_camper_per_day = food_per_camper_per_day
        self.camp_manager.update(selected_camp)

        print(f"Food requirement updated for camp '{selected_camp.name}'.")

        self.commands = self.main_commands
