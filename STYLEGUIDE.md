# Style Guide

## 1. Messages

### 1.1. Get user commands in the following format:
```
Please enter a command, or enter 'q' to quit:
> 
```

### 1.2. Smaller inputs like form filling can be done more compactly, if preferred:
```
Please enter a username: user1
Please enter a password: password123
```

## 2. Project Structure
Project to follow an MVC (model, view, controller) structure.

Models -> The files like admin.py which execute the commands sent by the user.
View -> the functions which display data.
Controller -> The interface between the user and the project.

```
data (for all persistent data storage)
interface (for all command management)
program (first entrypoint after main. Used to set up the app)
session (for session management)

```

## 3. Functions/Codebase
Functions in our project should be "pure" where possible. This means a function only operates on data passed in as a parameter. We do this to improve readability of the codebase, ability to refactor, and for data integrity.

Said functions will be called largely from controllers. And the controllers will handle user input.

For example:
```py
# Like this
def add_user(username, password, account_type):
    # do smth here

## But preferably not like this
def add_user():
    username = input()
    password = input()
```

Another example:
```py
run_program(user, session)
```

### 3.1. Controller-related functions
If applicable, make functions return a bool to determine the outcome of that function execution.

## 4. Commands and Dialogs
Commands are managed at the top level by the interfaces. The interfaces should be used to execute all of the functions throughout the project, thus abstracting the inner workings of the project from users.

All commands at the top level should start with `/`.

### 4.1. Universal Commands
Some commands should be accessed by all users. These include:
```
/help -> provides a list of all commands accessible to the user
/quit or /q -> saves and exits the program
/account -> show account details
```

If a universal command is not recognised, the interface switches to the appropriate account-type interface to process the rest.

Commands should return a boolean to inform the caller of their outcome.

### 4.2. Admin Commands
Admins have the ability to create new leader and coordinator accounts, edit those accounts, and delete or disable user records.

(Extra feature) Admins should not be able to edit other admin accounts.
(Extra feature) Visualisation of all users, a dashboard?

Some commands may include the following, subject to changes:
```
/user create -> opens the account creation dialog
/user delete -> delete user account
/user edit -> edit user account
```

### 4.3. Coordinator Commands
Coordinators should be able to define camps (names, locs, availability, type(day, overnight, expedition)).

Coordinators should be able to define camp food stock. Top up food stock.

Coordinators should be able to see dashboards.

Coordinators should be able to receive application notification for resource shortages (i.e. when the stock level might go below the planned level for the whole duration of the camp).

Coordinators should be able to set daily payment rate for leaders.

Some commands could include:
```
/camp ... -> command management for all camp functionality
/display -> possible command to manage dashboard visualisation
- /display users (or user)
- /display camps (or camp)
/payrate or /pay -> command to manage pay for a leader
```

### 4.4. Leader Commands
Leaders should be able to "select camps to supervise from the list created by the coordinator"
    - What list is this?

Leaders should "bulk assign campers to their activities"
    - How would this be implemented?

Assign amount of food required per camper per day.

Record daily activity outcomes, incidents, achievements "as one text block"

View statistics/trends for all camps she/he led
    - participation rates, food resources, incident reports, money earned per camp, overall data

Some commands could include:
```
/record -> open dialog to record daily activity outcomes? This can get parsed like a csv
/display -> similar to coordinator, except this will be a separate set of display commands
```