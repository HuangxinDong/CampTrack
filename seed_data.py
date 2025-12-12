from datetime import datetime, timedelta
import os
import shutil
from persistence.dao.camp_manager import CampManager
from persistence.dao.activity_manager import ActivityManager
from persistence.dao.user_manager import UserManager
from models.camp import Camp
from models.activity import Activity, Session

def reset_data():
    # Paths
    print("Resetting data...")
    if os.path.exists("persistence/data/camps.json"):
        os.remove("persistence/data/camps.json")
    # We keep users to avoid login issues, or ensure 'leader1' exists
    # We keep campers csvs if they exist, or maybe just clear camps activities
    
    # We WILL clear activities library to ensure clean schema
    if os.path.exists("persistence/data/activities.json"):
        os.remove("persistence/data/activities.json")

def seed():
    am = ActivityManager()
    cm = CampManager()
    um = UserManager()

    # 1. Ensure Leader
    if not um.find_user("leader1"):
        um.create_user("leader1", "password", "Leader")
        print("Created user 'leader1' (password: password)")
    else:
        print("User 'leader1' exists.")

    # 2. Seed Activity Library
    activities = {
        "Archery": {"is_indoor": False},
        "Swimming": {"is_indoor": False},
        "Arts & Crafts": {"is_indoor": True},
        "Night Hike": {"is_indoor": False},
        "Cooking": {"is_indoor": True}
    }
    am.save_library(activities)
    print("Seeded Activity Library.")

    # Dates
    today = datetime.now().date()
    start_next_month = today + timedelta(days=30)
    
    # Create dummy campers
    from models.camper import Camper
    c1 = Camper("Alex", 12, "Mom: 555-0101", "None")
    c2 = Camper("Sam", 13, "Dad: 555-0102", "Peanut Allergy")
    c3 = Camper("Jordan", 11, "Guard: 555-0103", "None")

    # Camp 1: Future Full (3 days)
    camp1 = Camp(
        camp_id=None,
        name="Camp Alpha",
        location="Forest",
        camp_type="Adventure",
        start_date=start_next_month,
        end_date=start_next_month + timedelta(days=2),
        camp_leader="leader1",
        food_per_camper_per_day=3,
        initial_food_stock=100
    )
    camp1.campers.extend([c1, c2, c3])
    
    # Add activities for Day 1
    d1 = camp1.get_date_range()[0]
    camp1.activities.append(Activity("Archery", d1, Session.Morning, False).to_dict())
    camp1.activities.append(Activity("Arts & Crafts", d1, Session.Afternoon, True).to_dict())
    camp1.activities.append(Activity("Night Hike", d1, Session.Evening, False).to_dict())
    
    cm.add(camp1)

    # Camp 2: Future Partial (4 days) - Day 1 Full, Day 2 Empty
    camp2 = Camp(
        camp_id=None,
        name="Camp Beta",
        location="Lakeside",
        camp_type="Relax",
        start_date=start_next_month + timedelta(days=5),
        end_date=start_next_month + timedelta(days=8),
        camp_leader="leader1"
    )
    camp2.campers.extend([c1, c2]) # Add campers

    # Day 1 activities
    d1_c2 = camp2.get_date_range()[0]
    camp2.activities.append(Activity("Swimming", d1_c2, Session.Morning, False).to_dict())
    # Day 2 empty
    # Day 3 partial
    d3_c2 = camp2.get_date_range()[2]
    camp2.activities.append(Activity("Cooking", d3_c2, Session.Evening, True).to_dict())

    cm.add(camp2)

    # Camp 3: Empty (2 days)
    camp3 = Camp(
        camp_id=None,
        name="Camp Gamma",
        location="Mountain",
        camp_type="Hiking",
        start_date=start_next_month + timedelta(days=10),
        end_date=start_next_month + timedelta(days=11),
        camp_leader="leader1"
    )
    camp3.campers.append(c3) # Add camper
    cm.add(camp3)


    print("Seeded 3 Camps.")

if __name__ == "__main__":
    reset_data()
    seed()
