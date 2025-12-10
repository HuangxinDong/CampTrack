import csv
import uuid

from datetime import datetime, date
from persistence.dao.camp_manager import CampManager
from models.users.class_map import register
from models.users.users import User
from program.helpers import get_positive_int
from models.camper import Camper
from persistence.dao.daily_report_manager import DailyReportManager



def ensure_date(d):
    """Convert to datetime.date if it's a string."""
    if isinstance(d, date):
        return d
    return datetime.strptime(str(d), "%Y-%m-%d").date()


@register("Leader")
class Leader(User):
    def __init__(self, username, password, role, enabled, daily_payment_rate):
        self.daily_report_manager = DailyReportManager()
        super().__init__(username, password, role, enabled)
        self.daily_payment_rate = daily_payment_rate
        self.parent_commands = [
            {'name': 'Select Camps to Supervise', 'command': self.select_camps_to_supervise},
            {'name': 'Edit Camp', 'command': self.edit_camp},
            {'name': 'Assign Campers from CSV', 'command': self.assign_campers_menu},
            {'name': 'Create Daily Report', 'command': self.create_daily_report},
            {'name': 'View My Statistics', 'command': self.view_statistics},
        ]
        self.commands = self.parent_commands
        self.camp_manager = CampManager()

    @staticmethod
    def dates_conflict(start1, end1, start2, end2):
        return (start1 <= end2) and (end1 >= start2)

    def select_camps_to_supervise(self):
        camps = self.camp_manager.read_all()

        if not camps:
            print("No camps available.")
            return

        print("\nAvailable camps:")
        for i, camp in enumerate(camps, 1):
            if camp.camp_leader == self.username:
                status = " (You are the leader)"
            elif camp.camp_leader:
                status = f" (Assigned to: {camp.camp_leader})"
            else:
                status = " (Available)"
            print(f"{i}. {camp.name} - {camp.location}{status}")

        print("\nEnter camp numbers to supervise, separated with commas:")
        print("Note: You can only select camps that are available or already yours.")
        selection = input("Your selection: ")

        try:
            selected_indices = [int(x.strip()) - 1 for x in selection.split(",")]
            my_camps = [c for c in camps if c.camp_leader == self.username]

            for index in selected_indices:
                if not (0 <= index < len(camps)):
                    print(f"Invalid selection: {index + 1}")
                    continue

                camp = camps[index]

                if camp.camp_leader and camp.camp_leader != self.username:
                    print(f"Cannot select '{camp.name}' - already assigned to {camp.camp_leader}")
                    continue

                # Schedule conflict
                new_start = ensure_date(camp.start_date)
                new_end = ensure_date(camp.end_date)

                conflict = False
                for c in my_camps:
                    s = ensure_date(c.start_date)
                    e = ensure_date(c.end_date)

                    if (new_start <= e) and (new_end >= s):
                        print(f"Cannot select '{camp.name}' - schedule conflicts with '{c.name}'.")
                        conflict = True
                        break

                if conflict:
                    continue

                if camp.camp_leader == self.username:
                    print(f"You are already supervising '{camp.name}'")
                    continue

                camp.assign_leader(self.username)
                self.camp_manager.update(camp)
                print(f"You are now supervising: {camp.name}")

        except ValueError:
            print("Invalid input. Please enter valid numbers separated by commas.")

    def edit_camp(self):
        camps = self.camp_manager.read_all()
        my_camps = [camp for camp in camps if camp.camp_leader == self.username]

        if not my_camps:
            print("You are not supervising any camps. Use 'Select Camps to Supervise' first.")
            return

        print("\nYour camps:")
        for i, camp in enumerate(my_camps, 1):
            print(f"{i}. {camp.name} - {camp.location}")

        self.commands = [
            {'name': 'Assign food per camper per day', 'command': self.assign_food_per_camper_per_day},
        ]

    def create_daily_report(self):
        camps = self.camp_manager.read_all()
        my_camps = [camp for camp in camps if camp.camp_leader == self.username]

        if not my_camps:
            print("You are not supervising any camps.")
            return

        print("\nYour Camps:")
        for i, camp in enumerate(my_camps, 1):
            print(f"{i}. {camp.name} ({camp.start_date} → {camp.end_date})")

        try:
            choice = int(input("Select a camp to record today's report: "))
            selected_camp = my_camps[choice - 1]
        except:
            print("Invalid choice.")
            return

        date_str = input("Enter the date (YYYY-MM-DD), or press Enter for today: ")
        if date_str.strip() == "":
            report_date = datetime.today().strftime("%Y-%m-%d")
        else:
            report_date = date_str.strip()

        print("\nEnter today's activity outcomes or incidents (end with an empty line):")
        lines = []
        while True:
            line = input()
            if line.strip() == "":
                break
            lines.append(line)
        text_block = "\n".join(lines)

        report = {
            "report_id": str(uuid.uuid4()),
            "camp_id": selected_camp.camp_id,
            "leader_username": self.username,
            "date": report_date,
        "text": text_block
        }

        self.daily_report_manager.add_report(report)

        print("\nDaily report successfully recorded!")


    def assign_food_per_camper_per_day(self):
        camps = self.camp_manager.read_all()
        my_camps = [camp for camp in camps if camp.camp_leader == self.username]

        if not my_camps:
            print("You are not supervising any camps.")
            return

        print("\nYour camps:")
        for i, camp in enumerate(my_camps, 1):
            print(f"{i}. {camp.name} - {camp.location}")

        try:
            choice = int(input("Select a camp to assign food per camper per day: "))
            selected_camp = my_camps[choice - 1]
        except:
            print("Invalid choice.")
            return

        food_per_camper_per_day = get_positive_int("Enter food per camper per day: ")
        selected_camp.food_per_camper_per_day = food_per_camper_per_day
        self.camp_manager.update(selected_camp)

        print(f"Food requirement updated for camp '{selected_camp.name}'.")
        self.commands = self.parent_commands

    def to_dict(self):
        data = super().to_dict()
        data['daily_payment_rate'] = self.daily_payment_rate
        return data
    
    def assign_campers_menu(self):
        camps = self.camp_manager.read_all()
        my_camps = [camp for camp in camps if camp.camp_leader == self.username]

        if not my_camps:
            print("You are not supervising any camps.")
            return

        print("\nYour Camps:")
        for i, camp in enumerate(my_camps, 1):
            print(f"{i}. {camp.name} ({camp.start_date} → {camp.end_date})")

        try:
            choice = int(input("Select a camp to assign campers to: "))
            selected_camp = my_camps[choice - 1]
        except:
            print("Invalid choice.")
            return

        csv_path = input("Enter the CSV file path: ")

        manager = LeaderManager()
        manager.assign_campers_from_csv(selected_camp.camp_id, csv_path)

    def view_statistics(self):
        from program.statistics_and_trends import StatisticsAndTrends

        stats = StatisticsAndTrends()
        camps = self.camp_manager.read_all()
        my_camps = [camp for camp in camps if camp.camp_leader == self.username]

        if not my_camps:
            print("You are not supervising any camps.")
            return

        print("\n===== Statistics Summary =====")

        for camp in my_camps:
            print(f"\nCamp: {camp.name} ({camp.start_date} → {camp.end_date})")

            participation = stats.get_participation(camp)
            food_usage = stats.get_food_usage(camp)
            incidents = stats.get_incident_count(camp.camp_id)
            earnings = stats.get_earnings(self.username, camp)

            print(f"- Participants: {participation}")
            print(f"- Food Usage: {food_usage} units")
            print(f"- Incidents: {incidents}")
            print(f"- Earnings: £{earnings}")

class LeaderManager:
    def __init__(self):
        self.camp_manager = CampManager()

    def assign_campers_from_csv(self, camp_id, csv_path):
        camp = self.camp_manager.get_camp_by_id(camp_id)
        if not camp:
            print(f"Camp with id {camp_id} not found.")
            return

        try:
            with open(csv_path, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row in reader:
                    name = row.get("name")
                    age = row.get("age")
                    contact = row.get("contact")
                    medical_info = row.get("medical_info")

                    camper = Camper(
                        name=name,
                        age=int(age) if age else None,
                        contact=contact,
                        medical_info=medical_info
                    )

                    camp.add_camper(camper)

            self.camp_manager.update(camp)
            print(f"Successfully assigned campers from {csv_path} to camp {camp_id}")

        except FileNotFoundError:
            print(f"CSV file not found: {csv_path}")
        except Exception as e:
            print(f"Error processing CSV: {e}")