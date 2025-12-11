
import sys
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# Add project root to path
sys.path.append('/Users/maayancarno/Desktop/CS MASTERS/Intro Programming/COURSEWORK/group3')
from handlers.coordinator_handler import CoordinatorHandler

def test_date_validation():
    # Mock dependencies
    user = MagicMock()
    user_manager = MagicMock()
    message_manager = MagicMock()
    camp_manager = MagicMock()
    announcement_manager = MagicMock()
    
    handler = CoordinatorHandler(user, user_manager, message_manager, camp_manager, announcement_manager)
    
    # Dates
    today = datetime.now().date()
    yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    future_end_str = (today + timedelta(days=5)).strftime("%Y-%m-%d")
    
    # Inputs: 
    # 1. Name
    # 2. Location
    # 3. Type
    # 4. Start Date (Yesterday) -> Should fail
    # 5. Start Date (Tomorrow) -> Should pass
    # 6. End Date (Future) -> Should pass
    # 7. Food Stock
    
    inputs = [
        "Test Camp", "London", "Fun", 
        yesterday_str, tomorrow_str, # First pair fails, loop repeats to ask for start/end again
        tomorrow_str, future_end_str, # Second pair succeeds
        "100"
    ]
    
    input_iter = iter(inputs)
    
    def mock_input(prompt):
        val = next(input_iter)
        print(f"Mock Input for '{prompt}': {val}")
        return val
    
    with patch('handlers.coordinator_handler.get_input', side_effect=mock_input) as m_input:
        with patch('handlers.coordinator_handler.get_positive_int', return_value=100):
            handler.create_camp()
            
    # Verify camp was added
    assert camp_manager.add.called
    created_camp = camp_manager.add.call_args[0][0]
    
    assert str(created_camp.start_date) == tomorrow_str
    print("✓ Successfully prevented past start date and accepted valid future date.")

if __name__ == "__main__":
    try:
        test_date_validation()
    except StopIteration:
        print("❌ Failed: Handler probably didn't loop correctly or asked for input too many times.")
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
