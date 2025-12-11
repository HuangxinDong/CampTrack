# Architecture Refactoring Handover Document

## Project Context
Masters degree coursework - Scout Camp Management CLI application.
User wants proper layered architecture with separation of concerns.

---

## FINAL Target Architecture

```
group3/
├── main.py                      # Entry point + DI + handler factory
├── models/                      # DATA ONLY (User subclasses just store data)
├── handlers/                    # COMMANDS + BUSINESS LOGIC + I/O (full command flow)
├── cli/                         # Main loop, session, input utilities
└── persistence/                 # Data access (unchanged)
```

### Key Insight
**Handlers own the commands**, not User classes. Each handler has:
- `self.commands` list (what this role can do)
- Methods that do the full flow (input → logic → output)

---

## COMPLETED - Handler Updates

### base_handler.py ✅ DONE
- Has `self.parent_commands` with messaging
- Has `self.commands`
- Has `messages()` submenu method
- Has `read_messages()` and `send_message()` with `@cancellable` and `get_input()`

### admin_handler.py ✅ DONE
- Has `self.commands = self.parent_commands + [...]`
- Has `handle_create_user()` and `handle_delete_user()` with `@cancellable` and `get_input()`

### coordinator_handler.py ✅ DONE
- Has `self.commands = self.parent_commands + [...]`
- Has `create_camp()`, `edit_camp_resources()`, `top_up_food_stock()`, `set_daily_payment_limit()`
- All methods use `@cancellable` and `get_input()`

### leader_handler.py ⚠️ NEEDS FIXES
Methods copied but need these changes:
1. **Add imports at top:**
   ```python
   from cli.input_utils import get_input, cancellable
   from cli.prompts import get_positive_int
   ```

2. **Add commands list in `__init__`:**
   ```python
   self.commands = self.parent_commands + [
       {"name": "Select Camps to Supervise", "command": self.select_camps_to_supervise},
       {"name": "Edit Camp", "command": self.edit_camp},
   ]
   ```

3. **Fix all `self.username` → `self.user.username`** (multiple places)

4. **Fix all `input()` → `get_input()`** (lines 37, 94)

5. **Add `@cancellable` decorator** to `select_camps_to_supervise()` and `assign_food_per_camper_per_day()`

---

## NEXT STEPS (in order)

### Step 1: Fix leader_handler.py (see above)

### Step 2: Update main.py
Change the `create_handler` function to use simple dict:
```python
from handlers.admin_handler import AdminHandler
from handlers.coordinator_handler import CoordinatorHandler
from handlers.leader_handler import LeaderHandler
from handlers.base_handler import BaseHandler

HANDLERS = {
    "Admin": AdminHandler,
    "Leader": LeaderHandler,
    "Coordinator": CoordinatorHandler,
}

# In main():
handler_class = HANDLERS.get(user.role, BaseHandler)
handler = handler_class(user, user_manager, message_manager, camp_manager)
```

### Step 3: Update main_loop.py
Change to use `handler.commands` instead of `user.commands`:
```python
def display_menu(handler):
    for i, command in enumerate(handler.commands):
        print(f"{i + 1}. {command['name']}")

def run_program(user, handler):
    while True:
        display_menu(handler)
        # ... get choice ...
        handler.commands[choice - 1]["command"]()
```

### Step 4: Strip User model classes to DATA ONLY

**Remove from each User class:**
- `self.commands`
- `self.parent_commands`
- All command methods
- Manager instantiation (`self.user_manager`, etc.)
- `display_commands()`
- `process_command()`

**Keep:**
- `__init__` with data fields (username, password, role, enabled)
- `to_dict()`
- `@register` decorator
- For Leader: `daily_payment_rate` field

### Step 5: Test everything

---

## Current File Structure

```
group3/
├── main.py                      ⚠ Needs HANDLERS dict update
├── cli/
│   ├── input_utils.py          ✅ Done
│   ├── prompts.py              ✅ Done
│   ├── display.py              ✅ Done
│   ├── session.py              ✅ Done
│   └── main_loop.py            ⚠ Needs to use handler.commands
├── handlers/
│   ├── base_handler.py         ✅ Done
│   ├── admin_handler.py        ✅ Done
│   ├── coordinator_handler.py  ✅ Done
│   ├── leader_handler.py       ⚠ Needs fixes (see above)
│   ├── message_handler.py      ✅ Done (utilities)
│   └── statistics_handler.py   ✅ Done (utilities)
├── models/users/
│   ├── users.py                ⚠ Strip to data only
│   ├── admin.py                ⚠ Strip to data only
│   ├── coordinator.py          ⚠ Strip to data only
│   ├── leader.py               ⚠ Strip to data only
│   └── class_map.py            ✅ Keep as-is
└── persistence/                ✅ Unchanged
```

---

## Key Design Decisions

1. **Handlers own commands** - cleaner than CLI dispatch tables
2. **Handlers do full flow** (I/O + logic) - acceptable for CLI app
3. **User classes are DATA ONLY** - just store user info
4. **Keep @register decorator** - still needed for User subclass creation from JSON
5. **Simple dict for handler factory** - no need for handler_map.py
6. **Keep class_map.py** - still needed for user_from_dict() in login
7. **Managers via DI** - created once in main.py, passed to handlers
