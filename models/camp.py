import uuid
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict
from models.camper import Camper
from models.resource import Equipment

class Camp:
    def __init__(
        self,
        camp_id: Optional[str],
        name: str,
        location: str,
        camp_type: str,
        start_date: date,
        end_date: date,
        camp_leader: Optional[str] = None,
        campers: List = [],
        food_per_camper_per_day: int = 1,
        initial_food_stock: int = 0,
        current_food_stock: int=0,
        food_usage: Optional[Dict] = None,
        equipment: List = [],
        activities: Optional[List] = None
    ):
        self.camp_id = camp_id if camp_id else str(uuid.uuid4())
        self.name = name
        self.location = location
        self.camp_type = camp_type
        self.start_date = start_date
        self.end_date = end_date
        self.camp_leader = camp_leader
        self.campers = campers
        self.food_per_camper_per_day = food_per_camper_per_day
        self.initial_food_stock = initial_food_stock
        self.current_food_stock = initial_food_stock
        self.food_usage = {}
        self.equipment = equipment
        self.activities = activities if activities is not None else []

    def add_food(self, amount: int):
        if amount < 0:
            raise ValueError("amount must be positive")
        if self.has_camp_finished():
            raise ValueError("Cannot add food to a finished camp")
        self.current_food_stock += amount

    def remove_food(self, amount: int, date_str: Optional[str] = None):
        if amount < 0:
            raise ValueError("amount must be positive")
        if not self.has_camp_started():
            raise ValueError("Cannot remove food before camp start")
        if self.has_camp_finished():
            raise ValueError("Cannot remove food after camp end")
        if amount > self.current_food_stock:
            raise ValueError("Not enough food in stock")

        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        self.current_food_stock -= amount
        if date_str in self.food_usage:
            self.food_usage[date_str] += amount
        else:
            self.food_usage[date_str] = amount

    def has_camp_started(self):
        now = datetime.now().date()
        return self.start_date <= now

    def has_camp_finished(self):
        now = datetime.now().date()
        return now > self.end_date
    
    def get_date_range(self):
        delta = self.end_date - self.start_date
        return [(self.start_date + timedelta(days=i)).isoformat() for i in range(delta.days + 1)]
    

    def can_edit_dates(self) -> tuple[bool, str]:
        """
        Check if camp dates can be edited.

        Returns:
            tuple: (can_edit: bool, reason: str)
            - If editable: (True, "")
            - If not: (False, "reason message")
        """
        if self.has_camp_started():
            return False, "Cannot edit dates: camp has already started"
        if self.has_camp_finished():
            return False, "Cannot edit dates: camp has already finished"
        return True, ""

    @staticmethod
    def dates_overlap(start1: date, end1: date, start2: date, end2: date) -> bool:
        """
        Check if two date ranges overlap.

        Args:
            start1, end1: First date range
            start2, end2: Second date range

        Returns:
            bool: True if ranges overlap, False otherwise
        """
        return start1 <= end2 and start2 <= end1

    def set_food_per_camper_per_day(self, amount):
        self.food_per_camper_per_day = amount

    def total_food_required(self):
        total_campers = len(self.campers)
        days = (self.end_date - self.start_date).days + 1
        return total_campers * self.food_per_camper_per_day * days

    def is_food_shortage(self):
        if self.has_camp_finished():
            return False

        total_campers = len(self.campers)
        total_stock = self.current_food_stock

        if not self.has_camp_started():
            total_days = (self.end_date - self.start_date).days + 1
            total_required = total_campers * self.food_per_camper_per_day * total_days
            return total_stock < total_required

        remaining_days = (self.end_date - datetime.now().date()).days + 1
        remaining_required = total_campers * self.food_per_camper_per_day * remaining_days
        return total_stock < remaining_required

    def add_camper(self, camper):
        self.campers.append(camper)

    def remove_camper(self, camper_id):
        self.campers = [c for c in self.campers if c.camper_id != camper_id]

    def assign_leader(self, username):
        self.camp_leader = username

    def to_dict(self):
        return {
            "camp_id": self.camp_id,
            "name": self.name,
            "location": self.location,
            "camp_type": self.camp_type,
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
            "camp_leader": self.camp_leader,
            "campers": [camper.to_dict() for camper in self.campers],
            "food_per_camper_per_day": self.food_per_camper_per_day,
            "initial_food_stock": self.initial_food_stock,
            "current_food_stock": self.current_food_stock,
            "food_usage": self.food_usage,
            "equipment": [e.to_dict() for e in self.equipment],
            "activities": self.activities
        }

    @classmethod
    def from_dict(cls, data):
        start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
        camp = cls(
            camp_id=data["camp_id"],
            name=data["name"],
            location=data["location"],
            camp_type=data["camp_type"],
            start_date=start_date,
            end_date=end_date,
            camp_leader=data.get("camp_leader"),
            campers=[Camper.from_dict(c) for c in data.get("campers", [])],
            food_per_camper_per_day=data.get("food_per_camper_per_day", 1),
            initial_food_stock=data.get("initial_food_stock", 0),
            equipment=[Equipment.from_dict(e) for e in data.get("equipment", [])],
            activities=data.get("activities", [])
        )
        camp.current_food_stock = data.get("current_food_stock", camp.initial_food_stock)
        camp.food_usage = data.get("food_usage", {})
        return camp
    def get_schedule_status(self) -> str:
        """
        Calculates the schedule status based on activity coverage.
        Returns:
            str: "Empty", "Partial", or "Full"
        """
        if not self.activities:
            return "Empty"

        all_dates = set(self.get_date_range())
        
        # activities is list of dicts or objects depending on state, handle both safely
        covered_dates = set()
        for act in self.activities:
            d = act.get("date") if isinstance(act, dict) else str(act.date)
            covered_dates.add(d)
        
        if not covered_dates:
            return "Empty"
            
        if all_dates.issubset(covered_dates):
            return "Full"
            
        return "Partial"
