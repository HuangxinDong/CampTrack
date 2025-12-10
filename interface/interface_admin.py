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

    def get_toggle_status_input(self):
        print("--- Toggle User Status ---\n")
        username = input("Enter username: ")
        enable_input = input("Enable user? (y/n): ")
        enabled = enable_input.lower() == 'y'
        return username, enabled

    @staticmethod
    def show_message(message):
        print(f"[System]: {message}")

