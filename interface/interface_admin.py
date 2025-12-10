class AdminInterface:
    @staticmethod
    def get_user_details():
        print("\n--- Create New User ---")
        username = input("Enter username: ")
        password = input("Enter password: ")
        role = input("Enter role (Leader/Coordinator): ")
        kwargs = {}
        if role.lower() == "leader":
            try:
                rate = float(input("Enter daily payment rate: "))
                kwargs['daily_payment_rate'] = rate
            except ValueError:
                print("Invalid rate, defaulting to 0.0")
                kwargs['daily_payment_rate'] = 0.0
        return username, password, role, kwargs

    @staticmethod
    def get_username_to_delete():
        print("\n--- Delete User ---")
        return input("Enter username to delete: ")

    @staticmethod
    def get_status_toggle_details():
        print("\n--- Toggle User Status ---")
        username = input("Enter username: ")
        enable_input = input("Enable user? (y/n): ")
        enabled = enable_input.lower() == 'y'
        return username, enabled

    @staticmethod
    def show_message(message):
        print(f"[System]: {message}")
