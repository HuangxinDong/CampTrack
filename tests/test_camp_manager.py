
import sys
import json
import os
import shutil

# Add project root to path
sys.path.append('/Users/maayancarno/Desktop/CS MASTERS/Intro Programming/COURSEWORK/group3')
from persistence.dao.camp_manager import CampManager
from models.camp import Camp

def test_camp_manager_robustness():
    test_file = "persistence/data/camps_test_robustness.json"
    
    # 1. Create a file with mixed valid and invalid data
    data = [
        [], # Invalid: list instead of dict (the original bug)
        "some string", # Invalid
        {"camp_id": "valid_1", "name": "Valid Camp", "location": "Loc", "camp_type": "Type", "start_date": "2025-01-01", "end_date": "2025-01-05", "camp_leader": "None", "campers": []} # Valid
    ]
    
    with open(test_file, "w") as f:
        json.dump(data, f)
        
    print(f"Created test file with mixed data: {data}")

    # 2. Instantiate manager
    manager = CampManager(filepath=test_file)
    
    # 3. Read all
    try:
        camps = manager.read_all()
        print(f"Successfully read {len(camps)} camps.")
        
        assert len(camps) == 1, f"Expected 1 valid camp, got {len(camps)}"
        assert camps[0].camp_id == "valid_1"
        print("✓ Successfully skipped invalid items and loaded valid one.")
        
    except Exception as e:
        print(f"❌ Failed: Manager crashed with {e}")
        import traceback
        traceback.print_exc()

    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)

if __name__ == "__main__":
    test_camp_manager_robustness()
