import os
import psutil
import pyautogui
import time
from datetime import datetime
import screen_brightness_control as sbc

class SystemControl:
    def __init__(self):
        try:
            # Create screenshots directory
            self.screenshots_dir = "screenshots"
            os.makedirs(self.screenshots_dir, exist_ok=True)
            
            # Common application process names mapping
            self.app_map = {
                "chrome": ["chrome.exe"],
                "firefox": ["firefox.exe"],
                "edge": ["msedge.exe"],
                "spotify": ["spotify.exe"],
                "notepad": ["notepad.exe"],
                "word": ["winword.exe"],
                "excel": ["excel.exe"],
                "powerpoint": ["powerpnt.exe"],
                "teams": ["teams.exe"],
                "discord": ["discord.exe"],
                "code": ["code.exe"],
                "explorer": ["explorer.exe"]
            }
            
            print(" System control initialized!")
        except Exception as e:
            print(f" System control initialization error: {str(e)}")

    def increase_volume(self):
        """Increase system volume using keyboard"""
        try:
            for _ in range(2):  # Press twice for more noticeable change
                pyautogui.press('volumeup')
            return "Volume increased"
        except Exception as e:
            print(f"Volume error: {str(e)}")
            return f"Error adjusting volume: {str(e)}"

    def decrease_volume(self):
        """Decrease system volume using keyboard"""
        try:
            for _ in range(2):  # Press twice for more noticeable change
                pyautogui.press('volumedown')
            return "Volume decreased"
        except Exception as e:
            return f"Error adjusting volume: {str(e)}"

    def get_volume(self):
        """Get current volume level - approximate based on system info"""
        try:
            return "Volume adjusted"
        except:
            return 0.5

    def set_brightness(self, level):
        """Set screen brightness"""
        try:
            sbc.set_brightness(level)
            return f"Brightness set to {level}%"
        except Exception as e:
            return f"Error setting brightness: {str(e)}"

    def increase_brightness(self, step=10):
        """Increase screen brightness"""
        try:
            current = sbc.get_brightness()[0]
            new_level = min(100, current + step)
            sbc.set_brightness(new_level)
            return "Brightness increased"
        except Exception as e:
            return f"Error adjusting brightness: {str(e)}"

    def decrease_brightness(self, step=10):
        """Decrease screen brightness"""
        try:
            current = sbc.get_brightness()[0]
            new_level = max(0, current - step)
            sbc.set_brightness(new_level)
            return "Brightness decreased"
        except Exception as e:
            return f"Error adjusting brightness: {str(e)}"

    def close_application(self, app_name):
        """Close application by name"""
        try:
            app_name = app_name.lower()
            closed = False
            
            # Map common MS Office names
            office_map = {
                "ms word": ["winword.exe", "word.exe"],
                "microsoft word": ["winword.exe", "word.exe"],
                "word": ["winword.exe", "word.exe"],
                "ms excel": ["excel.exe"],
                "microsoft excel": ["excel.exe"],
                "excel": ["excel.exe"],
                "ms powerpoint": ["powerpnt.exe"],
                "microsoft powerpoint": ["powerpnt.exe"],
                "powerpoint": ["powerpnt.exe"]
            }
            
            # Get process names to look for
            process_names = []
            if app_name in office_map:
                process_names = office_map[app_name]
            elif app_name in self.app_map:
                process_names = self.app_map[app_name]
            else:
                # Try to match partial names
                for key, value in {**self.app_map, **office_map}.items():
                    if key in app_name or any(name.lower() in app_name for name in value):
                        process_names.extend(value)
            
            # If no matches found, use the app name as is
            if not process_names:
                process_names = [f"{app_name}.exe"]
            
            print(f"Attempting to close processes: {process_names}")
            
            # Try to close the application
            for proc in psutil.process_iter(['pid', 'name']):
                for process_name in process_names:
                    if proc.info['name'].lower() == process_name.lower():
                        try:
                            process = psutil.Process(proc.info['pid'])
                            process.terminate()
                            process.wait(timeout=3)  # Wait for termination
                            closed = True
                        except psutil.TimeoutExpired:
                            process.kill()  # Force kill if timeout
                            closed = True
                        except Exception as e:
                            print(f"Error terminating process: {e}")
                            # Try using taskkill as last resort
                            os.system(f'taskkill /F /IM "{process_name}"')
                            closed = True
            
            if closed:
                return f"Closed {app_name}"
            return f"Couldn't find {app_name} running"
            
        except Exception as e:
            print(f"Error closing application: {str(e)}")
            return f"Error closing {app_name}"

    def take_screenshot(self):
        """Take a screenshot and save it"""
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            return filepath, f"Screenshot saved as {filename}"
        except Exception as e:
            return None, f"Error taking screenshot: {str(e)}" 