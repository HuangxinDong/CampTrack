# program.py
# Responsible for main program loop
import interface

import interface
from models.users.admin import Admin
from controllers.controller_admin import AdminController

def run_program(user):
    # If the user is an Admin, use the AdminController (MVC pattern)
    if isinstance(user, Admin):
        controller = AdminController(user)
        controller.run()
        return

    run_program = True
    while run_program:
        run_program = interface.main_ui.process_command(user)
    return