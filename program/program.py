# program.py
# Responsible for main program loop
import interface

def run_program(session, data):
    run_program = True
    while run_program:
        # do
        # stuff
        # here
        # until
        # program
        # is
        # exited
        run_program = interface.process_user_command(session, data)
    return