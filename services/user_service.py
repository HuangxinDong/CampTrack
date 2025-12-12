from typing import Optional, Tuple, List, Dict, Any
from persistence.dao.user_manager import UserManager
from persistence.dao.camp_manager import CampManager

class UserService:
    def __init__(self, user_manager: UserManager, camp_manager: CampManager):
        self.user_manager = user_manager
        self.camp_manager = camp_manager

    def create_user(self, username: str, password: str, role: str, **kwargs) -> Tuple[bool, str]:
        if not username.strip():
            return False, "Username cannot be empty."
        if not username.isalnum():
            return False, "Username must contain only letters and numbers."
        
        if self.user_manager.find_user(username):
            return False, f"User '{username}' already exists."

        return self.user_manager.create_user(username, password, role=role, **kwargs)

    def delete_user(self, username: str) -> Tuple[bool, str]:
        # Check if user is leader of active camps
        camps = self.camp_manager.read_all()
        active_leadership = []
        for camp in camps:
            if camp.camp_leader == username and not camp.has_camp_finished():
                active_leadership.append(camp.name)
        
        if active_leadership:
            return False, f"Cannot delete user '{username}'. They are currently assigned as leader for active camps: {', '.join(active_leadership)}."

        return self.user_manager.delete_user(username)

    def toggle_status(self, username: str, current_user_username: str, new_status: bool) -> Tuple[bool, str]:
        if username == current_user_username:
            return False, "You cannot disable your own account."
        
        user = self.user_manager.find_user(username)
        if not user:
            return False, f"User '{username}' not found."

        return self.user_manager.toggle_user_status(username, new_status)

    def update_password(self, username: str, new_password: str) -> Tuple[bool, str]:
        return self.user_manager.update_password(username, new_password)

    def update_daily_payment_rate(self, username: str, rate: float) -> Tuple[bool, str]:
        user = self.user_manager.find_user(username)
        if not user:
            return False, f"User '{username}' not found."
        
        if user.get('role') != 'Leader':
            return False, f"User '{username}' is not a Leader."

        return self.user_manager.update_daily_payment_rate(username, rate)

    def update_username(self, old_username: str, new_username: str) -> Tuple[bool, str]:
        if not new_username.strip():
            return False, "Username cannot be empty."
        if not new_username.isalnum():
            return False, "Username must contain only letters and numbers."
            
        return self.user_manager.update_username(old_username, new_username)

    def update_role(self, username: str, new_role: str) -> Tuple[bool, str]:
        return self.user_manager.update_role(username, new_role)
        
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        return self.user_manager.find_user(username)

    def get_all_users(self) -> List[Dict[str, Any]]:
        return self.user_manager.read_all()
