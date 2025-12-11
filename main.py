# Program entry point
from cli.session import Session
from cli.main_loop import run_program

from persistence.dao.user_manager import UserManager
from persistence.dao.camp_manager import CampManager
from persistence.dao.message_manager import MessageManager
from persistence.dao.announcement_manager import AnnouncementManager
from persistence.dao.system_notification_manager import SystemNotificationManager

from handlers.admin_handler import AdminHandler
from handlers.coordinator_handler import CoordinatorHandler
from handlers.leader_handler import LeaderHandler

from models.users import register_user_types
from handlers.base_handler import BaseHandler

register_user_types()

HANDLERS = {
    "Admin": AdminHandler,
    "Coordinator": CoordinatorHandler,
    "Leader": LeaderHandler,
}

def create_handler(user, user_manager, camp_manager, message_manager, announcement_manager, system_notification_manager):
    """Create the appropriate handler based on user role."""
    handler_class = HANDLERS.get(user.role, BaseHandler)
    return handler_class(user, user_manager, message_manager, camp_manager, announcement_manager, system_notification_manager)

def main():
    # Create managers ONCE (dependency injection)
    user_manager = UserManager()
    camp_manager = CampManager()
    message_manager = MessageManager()
    announcement_manager = AnnouncementManager()
    system_notification_manager = SystemNotificationManager()

    # Login
    session = Session()
    user = session.login()
    
    if user is None:
        return

    # Create handler for this user's role
    handler = create_handler(user, user_manager, camp_manager, message_manager, announcement_manager)

    # Run main loop with both user and handler
    run_program(user, handler)


if __name__ == "__main__":
    main()