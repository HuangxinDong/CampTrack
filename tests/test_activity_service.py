import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import MagicMock
from services.activity_service import ActivityService
from models.activity import Activity, Session

class TestActivityService(unittest.TestCase):
    def setUp(self):
        self.mock_activity_manager = MagicMock()
        self.mock_camp_manager = MagicMock()
        self.activity_service = ActivityService(self.mock_activity_manager, self.mock_camp_manager)

    def test_schedule_activity_success(self):
        # Setup
        camp = MagicMock()
        camp.activities = []
        self.mock_camp_manager.find_camp.return_value = camp
        
        self.mock_activity_manager.load_library.return_value = {"Archery": {"is_indoor": False}}
        
        # Action
        success, msg, conflict = self.activity_service.schedule_activity(
            camp_name="Camp A",
            activity_name="Archery",
            date_str="2025-01-01",
            session_name="Morning"
        )
        
        # Assert
        self.assertTrue(success)
        self.assertEqual(len(camp.activities), 1)
        self.mock_camp_manager.update.assert_called_once()

    def test_schedule_activity_limit_reached(self):
        # Setup
        camp = MagicMock()
        # Already 2 Archery sessions on this day
        camp.activities = [
            {"name": "Archery", "date": "2025-01-01", "session": "Morning"},
            {"name": "Archery", "date": "2025-01-01", "session": "Afternoon"}
        ]
        self.mock_camp_manager.find_camp.return_value = camp
        self.mock_activity_manager.load_library.return_value = {"Archery": {"is_indoor": False}}
        
        # Action
        success, msg, conflict = self.activity_service.schedule_activity(
            camp_name="Camp A",
            activity_name="Archery",
            date_str="2025-01-01",
            session_name="Evening"
        )
        
        # Assert
        self.assertFalse(success)
        self.assertIn("Limit reached", msg)
