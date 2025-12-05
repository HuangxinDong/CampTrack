from models.users.users import Leader, Coordinator, Admin
from data.data_manager import save_data

class UserManager:
    """
    All functions related with users
    """
    def __init__(self, data):
        self.data = data

    def create_user(self, username, password, role, **kwargs):
        # Check if username exists
        if self.find_user(username):
            return False, "Username already exists."
        new_user = None
        
        if role == "Leader":
            # Leader needs daily_payment_rate
            rate = kwargs.get('daily_payment_rate', 0.0)
            new_user = Leader(username, password, role="Leader", enabled=True, daily_payment_rate=rate)
        elif role == "Coordinator":
            new_user = Coordinator(username, password, role="Coordinator", enabled=True)
        elif role == "Admin":
             new_user = Admin(username, password, role="Admin", enabled=True)
        else:
            return False, "Invalid role."

        self.data.users.append(new_user)
        save_data(self.data)
        return True, f"User {username} created successfully."

    def find_user(self, username):
        for user in self.data.users:
            if user.username == username:
                return user
        return None

    def delete_user(self, username):
        user = self.find_user(username)
        if user:
            self.data.users.remove(user)
            save_data(self.data)
            return True, f"User {username} deleted."
        return False, "User not found."

    def toggle_user_status(self, username, enabled):
        user = self.find_user(username)
        if user:
            user.enabled = enabled
            save_data(self.data)
            return True, f"User {username} status set to {'enabled' if enabled else 'disabled'}."
        return False, "User not found."
    
    def update_password(self, username, new_password):
        user = self.find_user(username)
        if user:
            user.password = new_password
            save_data(self.data)
            return True, f"Password updated for {username}."
        return False, "User not found."
