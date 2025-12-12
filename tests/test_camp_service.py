import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import MagicMock
from datetime import date, timedelta, datetime
from services.camp_service import CampService
from models.camp import Camp

class TestCampService(unittest.TestCase):
    def setUp(self):
        self.mock_camp_manager = MagicMock()
        self.camp_service = CampService(self.mock_camp_manager)

    def test_create_camp_success(self):
        # Setup
        self.mock_camp_manager.read_all.return_value = []
        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=5)
        
        # Action
        camp = self.camp_service.create_camp(
            name="Test Camp",
            location="Forest",
            camp_type="Adventure",
            start_date=start_date,
            end_date=end_date,
            initial_food_stock=100
        )

        # Assert
        self.assertIsInstance(camp, Camp)
        self.assertEqual(camp.name, "Test Camp")
        self.mock_camp_manager.add.assert_called_once()

    def test_create_camp_duplicate_name(self):
        # Setup
        existing_camp = MagicMock(spec=Camp)
        existing_camp.name = "Existing Camp"
        self.mock_camp_manager.read_all.return_value = [existing_camp]
        
        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=5)

        # Action & Assert
        with self.assertRaises(ValueError) as context:
            self.camp_service.create_camp(
                name="Existing Camp",
                location="Forest",
                camp_type="Adventure",
                start_date=start_date,
                end_date=end_date,
                initial_food_stock=100
            )
        self.assertIn("already exists", str(context.exception))

    def test_validate_dates_past_start_date(self):
        start_date = date.today() - timedelta(days=1)
        end_date = date.today() + timedelta(days=5)
        
        with self.assertRaises(ValueError) as context:
            self.camp_service.validate_dates(start_date, end_date)
        self.assertIn("cannot be in the past", str(context.exception))

    def test_validate_dates_end_before_start(self):
        start_date = date.today() + timedelta(days=5)
        end_date = date.today() + timedelta(days=1)
        
        with self.assertRaises(ValueError) as context:
            self.camp_service.validate_dates(start_date, end_date)
        self.assertIn("must be on or after start date", str(context.exception))

    def test_update_dates_conflict(self):
        # Setup
        camp = MagicMock(spec=Camp)
        camp.name = "My Camp"
        camp.camp_id = "1"
        camp.camp_leader = "Leader1"
        camp.can_edit_dates.return_value = (True, "")
        
        self.mock_camp_manager.find_camp.return_value = camp
        
        # Mock conflicting camp
        conflicting_camp = MagicMock(spec=Camp)
        conflicting_camp.camp_id = "2"
        conflicting_camp.name = "Other Camp"
        
        # Set conflicting dates
        new_start = date.today() + timedelta(days=10)
        new_end = date.today() + timedelta(days=15)
        
        conflicting_camp.start_date = new_start
        conflicting_camp.end_date = new_end
        
        self.mock_camp_manager.get_camps_by_leader.return_value = [conflicting_camp]
        
        # Action
        success, message, conflicts = self.camp_service.update_dates("My Camp", new_start, new_end)
        
        # Assert
        self.assertFalse(success)
        self.assertIn("conflict", message.lower())
        self.assertEqual(len(conflicts), 1)
