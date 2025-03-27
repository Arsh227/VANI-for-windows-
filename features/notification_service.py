from plyer import notification

class NotificationService:
    def __init__(self):
        self.notification_settings = {
            "duration": 5,
            "threaded": True
        }
        print("Notification service initialized")

    def notify(self, title, message, urgent=False):
        """Show notification even when minimized"""
        try:
            duration = 10 if urgent else self.notification_settings["duration"]
            
            notification.notify(
                title=title,
                message=message,
                app_name="AI Assistant",
                timeout=duration,
                toast=True
            )
            
        except Exception as e:
            print(f"Notification error: {e}")

    def send_error(self, error_message):
        """Show error notification"""
        self.notify(
            "AI Assistant Error",
            error_message,
            urgent=True
        )

    def send_status(self, status_message):
        """Show status notification"""
        self.notify(
            "AI Assistant Status",
            status_message
        )

    def send_comparison_update(self, site, status):
        """Show price comparison progress"""
        self.notify(
            "Price Comparison",
            f"Searching {site}: {status}",
            urgent=False
        ) 