# program.py
# Responsible for main program loop
import interface

def run_program(user):
    run_program = True
    while run_program:
        run_program = interface.process_user_command(user)
    return