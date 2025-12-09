class MainUI:
    def __init__(self):
        pass

# Process User Commands
#
# For Each Command, pass in session and data if these are needed
# This ensures that all data is accessible without the need for global scope


def process_user_command(user):
    user.display_commands()

    user_input = input("Please enter a number or q to quit\n> ")
    
    if user_input == 'q':
        return False
    
    try:
        user_input_as_int = int(user_input)
    except ValueError:
        print("Please enter a valid number.")
        return True

    # Validate range (positive and exists in list)
    if user_input_as_int < 1 or user_input_as_int > len(user.commands):
        print("Please enter a number from the list.")
        return True

    # b for back to homepage

    user.process_command(user_input_as_int)
    return True