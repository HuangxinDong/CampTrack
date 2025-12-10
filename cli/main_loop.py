# program.py
# Responsible for main program loop
from cli import interface_main 

def run_program(user):
    run_program = True
    while run_program:
        run_program = interface_main.main_ui.process_command(user)
    return