from interface.interface_admin import AdminInterface


class AdminController:
    def __init__(self, admin_model):
        self.model = admin_model
        self.view = AdminInterface()

    def get_menu(self):
        menu = [
            { 'name': 'Create User', 'command': self.run_create_user },
            { 'name': 'Delete User', 'command': self.run_delete_user },
            { 'name': 'Toggle User Status', 'command': self.run_toggle_status },
            { 'name': 'Update User Info', 'command': self.run_update_user },
        ]
        # Add shared commands from the model base class
        if hasattr(self.model, 'commands'):
            menu.extend(self.model.commands)
        return menu

    def run_create_user(self):
        username, password, role, kwargs = self.view.get_create_user_input()
        success, message = self.model.create_user(username, password, role, **kwargs)
        self.view.show_message(message)

    def run_delete_user(self):
        username = self.view.get_delete_user_input()
        success, message = self.model.delete_user(username)
        self.view.show_message(message)

    def run_toggle_status(self):
        username, enabled = self.view.get_toggle_status_input()
        success, message = self.model.toggle_status(username, enabled)
        self.view.show_message(message)

    def run_update_user(self):
        choice = self.view.get_update_user_selection()
        if choice == '1':
            username, pwd = self.view.get_update_password_input()
            success, msg = self.model.update_user_password(username, pwd)
            self.view.show_message(msg)
        elif choice == '2':
            username, rate = self.view.get_update_rate_input()
            if username:
                success, msg = self.model.update_user_rate(username, rate)
                self.view.show_message(msg)
        else:
            self.view.show_message("Invalid selection")

    def run(self):
        """
        Main loop for the Admin Controller.
        """
        while True:
            menu = self.get_menu()
            print("\n--- Admin Menu ---")
            for i, item in enumerate(menu):
                print(f"{i + 1}. {item['name']}")
            print("q. Logout")

            choice = input("Select an option: ")

            if choice.lower() == 'q':
                break

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(menu):
                    menu[idx]['command']()
                else:
                    print("Invalid option.")
            except ValueError:
                print("Invalid input.")

