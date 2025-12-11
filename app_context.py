class AppContext:
    """
    Holds references to all manager instances (DAOs) to be passed around
    the application, avoiding long argument lists and circular dependency issues.
    """
    def __init__(self, user_manager, camp_manager, message_manager, announcement_manager, system_notification_manager):
        self.user_manager = user_manager
        self.camp_manager = camp_manager
        self.message_manager = message_manager
        self.announcement_manager = announcement_manager
        self.system_notification_manager = system_notification_manager
