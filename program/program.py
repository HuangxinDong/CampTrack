# program.py
# Responsible for main program loop
import interface

def run_program(user):
    run_program = True
    while run_program:
        run_program = interface.main_ui.process_command(user)
    return