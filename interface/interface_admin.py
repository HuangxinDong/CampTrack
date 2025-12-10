class AdminInterface:
    def __init__(self):
        pass

    def get_create_user_input(self):
        print("--- Create New User ---\n")
        username = input("Enter username: ")
        password = input("Enter password: ")
        role = input("Enter role (Leader/Coordinator): ")
        kwargs = {}
        return username, password, role, kwargs

    def get_delete_user_input(self):
        print("--- Delete User ---\n")
        username = input("Enter username to delete: ")
        return username

    def get_username_input(self, title):
        print(f"\n--- {title} ---")
        username = input("Enter username: ")
        return username

    def get_enable_selection(self, username, current_status):
        status_str = "Enabled" if current_status else "Disabled"
        print(f"Current status for {username}: {status_str}")
        
        if current_status:
            confirm = input("Disable user? (y/n): ")
            return False if confirm.lower() == 'y' else True
        else:
            confirm = input("Enable user? (y/n): ")
            return True if confirm.lower() == 'y' else False

    def get_update_user_selection(self):
        print("\n--- Update User Info ---")
        print("1. Update Password")
        print("2. Update Daily Rate (Leader only)")
        choice = input("Select option: ")
        return choice

    def get_update_password_input(self):
        username = input("Enter username: ")
        new_password = input("Enter new password: ")
        return username, new_password

    def get_update_rate_input(self):
        username = input("Enter username: ")
        try:
            new_rate = float(input("Enter new daily rate: "))
            return username, new_rate
        except ValueError:
            print("Invalid rate.")
            return None, None

    @staticmethod
    def show_message(message):
        print(f"[System]: {message}")

