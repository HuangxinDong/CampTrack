from enum import Enum
class Session(Enum):
    Morning = 0
    Afternoon = 1
    Evening = 2

class Activity:
    def __init__(self, name, date, session: Session, is_indoor: bool):
        self.name = name
        self.date = date
        self.session = session
        self.is_indoor = is_indoor
        self.campers = []

    def to_dict(self):
        return {
            "name": self.name,
            "date": str(self.date),
            "session": self.session.name,  
            "camper_ids": self.campers 
        }

    @staticmethod
    def from_dict(data):
        session_str = data.get("session", "Morning")
        try:
            session = Session[session_str]
        except KeyError:
            session = Session.Morning
            
        activity = Activity(
            name=data["name"], 
            date=data["date"], 
            session=session,
            is_indoor = data.get("is_indoor", False)
        )
        activity.campers = data.get("camper_ids", [])
        return activity

