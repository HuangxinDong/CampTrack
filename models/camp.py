import uuid
from datetime import datetime, date

from models.camper import Camper


class Camp:
    def __init__(
        self,
        camp_id: str,
        name: str,
        location: str,
        camp_type: str,
        start_date: date,
        end_date: date,
        camp_leader: str = None,
        campers: list[str] = [],
        food_per_camper_per_day: int = 1,
        initial_food_stock: int = 0,
        current_food_stock: int = 0,
        food_usage: dict = None
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
        self.current_food_stock = current_food_stock
        self.food_usage = food_usage if food_usage else {}

    def add_food(self, amount: int):
        if amount < 0:
             raise ValueError("amount must be positive")
        
        # Check if camp has finished
        if self.has_camp_finished():
            raise ValueError("Cannot add food to a finished camp")

        # Optionally check if camp has started? User said "Checking to see if the camp has started as well as ended"
        # for "topping up and removing food".
        # UPDATED REQ: User wants to allow top up BEFORE start.
        # if not self.has_camp_started():
        #      raise ValueError("Cannot add food before camp has started")

        self.current_food_stock += amount

    def remove_food(self, amount: int, date_str: str = None):
        if amount < 0:
             raise ValueError("amount must be positive")
        
        if not self.has_camp_started():
            raise ValueError("Cannot remove food before camp start")
        
        if self.has_camp_finished():
            raise ValueError("Cannot remove food after camp end")

        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        self.current_food_stock -= amount
        
        # Track usage
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

    # Used by coordinator to see how much is required based on current campers
    def total_food_required(self):
        total_campers = len(self.campers)
        days = (self.end_date - self.start_date).days + 1
        return total_campers * self.food_per_camper_per_day * days

    def is_food_shortage(self):
        if self.has_camp_finished():
            return False

        today = datetime.now().date()
        total_campers = len(self.campers)
        
        # If camp hasn't started, check against total duration requirements
        if not self.has_camp_started():
            days_needed = (self.end_date - self.start_date).days + 1
        else:
            # Camp started, check remaining days
            days_needed = (self.end_date - today).days + 1
            if days_needed < 0: days_needed = 0

        total_required = total_campers * self.food_per_camper_per_day * days_needed
        return self.current_food_stock < total_required

    def add_camper(self, camper):
        self.campers.append(camper)

    def remove_camper(self, camper_id):
        for camper in self.campers:
            if camper.camper_id == camper_id:
                self.campers.remove(camper)
                break

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
            "food_usage": self.food_usage
        }

    @classmethod
    def from_dict(cls, data):
        start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
        
        # MIGRATION LOGIC:
        # If 'current_food_stock' is missing, try to calculate it from old fields.
        if "current_food_stock" in data:
            stock = data["current_food_stock"]
        else:
            # Fallback calculation
            precamp = data.get("precamp_stock", 0)
            if precamp == 0: 
                # Catch the bug I just fixed in previous turn: maybe it's in initial_food_stock_per_day
                precamp = data.get("initial_food_stock_per_day", 0)
                if precamp is None: precamp = 0
            
            topups = sum(data.get("topups", []))
            usage = sum(data.get("food_usage", {}).values())
            stock = precamp + topups - usage
        
        camp = cls(
            camp_id=data["camp_id"],
            name=data["name"],
            location=data["location"],
            camp_type=data["camp_type"],
            start_date=start_date,
            end_date=end_date,
            camp_leader=data["camp_leader"],
            campers=[Camper.from_dict(camper) for camper in data["campers"]],
            food_per_camper_per_day=data.get("food_per_camper_per_day", 1),
            initial_food_stock=data.get("initial_food_stock", 0),
            current_food_stock=stock,
            food_usage=data.get("food_usage", {})
        )

        return camp

