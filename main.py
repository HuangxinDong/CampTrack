# Program entry point
from cli.session import Session
from cli.main_loop import run_program

from persistence.dao.user_manager import UserManager
from persistence.dao.camp_manager import CampManager
from persistence.dao.message_manager import MessageManager
from persistence.dao.announcement_manager import AnnouncementManager
from persistence.dao.system_notification_manager import SystemNotificationManager
from persistence.dao.audit_log_manager import AuditLogManager

from handlers.admin_handler import AdminHandler
from handlers.coordinator_handler import CoordinatorHandler
from handlers.leader_handler import LeaderHandler

from models.users import register_user_types
from handlers.base_handler import BaseHandler
from app_context import AppContext

register_user_types()

HANDLERS = {
    "Admin": AdminHandler,
    "Coordinator": CoordinatorHandler,
    "Leader": LeaderHandler,
}

def create_handler(user, context):
    """Create the appropriate handler based on user role."""
    handler_class = HANDLERS.get(user.role, BaseHandler)
    return handler_class(user, context)

def main():
    # Create managers ONCE (dependency injection)
    user_manager = UserManager()
    camp_manager = CampManager()
    message_manager = MessageManager()
    announcement_manager = AnnouncementManager()
    system_notification_manager = SystemNotificationManager()
    audit_log_manager = AuditLogManager()

    # Startup Banner
    from cli.startup_display import startup_display
    startup_display.display_welcome_banner()

    # Login
    session = Session()
    user = session.login()
    
    if user is None:
        return

    # Create Context
    context = AppContext(
        user_manager, 
        camp_manager, 
        message_manager, 
        announcement_manager, 
        system_notification_manager,
        audit_log_manager
    )

    # Create handler for this user's role
    handler = create_handler(user, context)

    # Run main loop with both user and handler
    run_program(user, handler)


if __name__ == "__main__":
    main()