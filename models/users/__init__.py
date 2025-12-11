from .users import User

def register_user_types():
    """Import all user modules to trigger @register decorators."""
    from . import admin, coordinator, leader