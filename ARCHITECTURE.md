# Architecture Explained
┌─────────────┐
│   main.py   │  ← Entry point, creates managers, creates handler
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Handlers   │  ← Business logic + commands + I/O
└──────┬──────┘
       │
       ▼
┌─────────────┐
│     CLI     │  ← UI layer (main_loop, display, input_utils, session)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Models    │  ← Data classes only (User, Camp, Message)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Persistence │  ← Data access (Managers read/write JSON)
└─────────────┘

## Folder	Responsibility
handlers/	Commands + business logic + user interaction
models/	Data classes only (no logic, no I/O)
persistence/	Data access layer (JSON read/write)
cli/	Input utilities, main loop, session management

## Key Design Patterns
A. Dependency Injection
- Managers are created ONCE in main.py
- Passed to handlers via constructor
- Handlers don't create their own managers
- Why: Easier testing, single source of truth
B. Handler Pattern
- Each role has a handler (AdminHandler, CoordinatorHandler, LeaderHandler)
- Handlers inherit from BaseHandler
Each handler has:
- self.commands - current menu options
- self.main_commands - home menu (for back navigation)
- self.parent_commands - inherited from BaseHandler (messaging)
- Commands are dicts: {"name": "Display Name", "command": self.method}
C. Register Decorator
- @register("RoleName") maps role strings to User subclasses
- Used by user_from_dict() to instantiate correct class from JSON
- Explanation: When JSON has {"role": "Leader"}, it creates a Leader object

## Flow Diagrams
A. Login Flow
main.py → session.py (get credentials) → UserManager.login() 
        → class_map.user_from_dict() → User subclass instance
        → create_handler() → Handler instance
        → run_program(user, handler)
B. Command Execution Flow
main_loop displays handler.commands
  → User enters number
  → handler.commands[choice-1]["command"]() is called
  → Handler method runs (may change handler.commands for submenu)
  → Loop continues
C. Back Navigation Flow
User presses 'b'
  → BackException raised
  → main_loop catches it
  → handler.commands = handler.main_commands
  → Menu returns to home

## How to Add New Features

### Adding a new command to an existing role
1. Add method to the handler class
2. Add entry to `self.commands` in `__init__`
3. Use `@cancellable` decorator if it takes user input
4. Use `get_input()` instead of `input()`

### Adding a new role
1. Create `models/users/newrole.py` with `@register("NewRole")`
2. Create `handlers/newrole_handler.py` extending `BaseHandler`
3. Add to `HANDLERS` dict in `main.py`
4. Add import to `register_user_types()` in `models/users/__init__.py`

### Adding a submenu
1. Create a method that sets `self.commands = [...]` with submenu options
2. At end of submenu action, reset with `self.commands = self.main_commands`

## Rules for Contributors

1. **User models are DATA ONLY** - no methods that do I/O or business logic
2. **Handlers own commands** - not User classes
3. **Use `get_input()` not `input()`** - for consistent quit/back handling
4. **Use `@cancellable`** on methods that take user input
5. **Managers via DI** - don't instantiate managers inside handlers