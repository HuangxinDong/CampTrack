# Primary controller for user input processing
from controller_coordinator import process_coordinator_command
from controller_admin import process_admin_command
from controller_leader import process_leader_command

# This may be temporary
msg_prompt_enter_input = "Please enter a number or type '/quit' to exit the program\n> "

msg_error_unrecognised_command = "Error: Unrecognised Command. Please enter a valid command, or type '/help'."
msg_error_account_type = "Error: No valid account type found"

def process_user_command(user):
    user.display_commands()

    user_input = input(msg_prompt_enter_input)
    
    if not user_input.startswith("/"):
        return True

    match user_input:
        case '/quit' | '/q':
            return False
        case '/help' | '/h':
            return cmd_help(user, user_input)
            # todo: run the help command, passing in the user (as the help command displays different)
        case _:
            match user.account_type:
                case "admin":
                    return process_admin_command(user, user_input)
                case "leader":
                    return process_leader_command(user, user_input)
                case "coordinator":
                    return process_coordinator_command(user, user_input)
                case _:
                    print(msg_error_account_type)
                    return True
    
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

user_commands_list = [
    ["/help", "", ["admin", "coordinator", "leader"]],
    ["/help", "", []],
]

def cmd_help(user, user_input) -> bool:
    help_cmd = """
        ========== Help ==========\n
        This is a full list of commands. For more specific support, please type '/help command'\n"""
    
    print(help_cmd)
    for command in user_commands_list:
        if user.account_type in command[2]:
            print(f"{command[0]} - {command[1]}")

    return True