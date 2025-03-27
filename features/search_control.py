import pyautogui
import time
import win32gui
import win32con
from typing import Dict, Optional

class SearchControl:
    def __init__(self):
        # Updated coordinates and delays for better reliability
        self.search_patterns = {
            "google": {
                "url": "https://www.google.com",
                "search_coords": None,  # Will use keyboard shortcuts instead
                "delay": 1.0
            },
            "youtube": {
                "url": "https://www.youtube.com",
                "search_coords": None,  # Will use keyboard shortcuts instead
                "delay": 1.5
            },
            "spotify": {
                "app_name": "Spotify",
                "search_hotkey": ["ctrl", "l"],  # Use hotkey instead of coordinates
                "delay": 1.0
            },
            "windows": {
                "search_hotkey": ["win"],
                "delay": 0.5
            },
            "chrome": {
                "search_hotkey": ["ctrl", "l"],
                "delay": 0.5
            },
            "firefox": {
                "search_hotkey": ["ctrl", "l"],
                "delay": 0.5
            }
        }
        print(" Search control initialized!")

    def perform_search(self, query: str, platform: str) -> str:
        """Perform search on specified platform"""
        try:
            platform = platform.lower()
            if platform not in self.search_patterns:
                return f"Unsupported platform: {platform}"

            pattern = self.search_patterns[platform]
            print(f"\n Searching for '{query}' on {platform}")

            # Handle different platforms
            if platform == "spotify":
                return self._app_search(query, pattern)
            else:
                return self._web_search(query, platform, pattern)

        except Exception as e:
            print(f"⚠️ Search error: {str(e)}")
            return f"Error performing search: {str(e)}"

    def _app_search(self, query: str, pattern: Dict) -> str:
        """Handle searches in desktop applications"""
        try:
            if pattern.get("app_name") == "Spotify":
                print(" Searching Spotify...")
                
                if not self.focus_window("Spotify"):
                    return "Could not find Spotify window"
                time.sleep(1.0)
                
                # Use keyboard shortcuts instead of coordinates
                pyautogui.hotkey('ctrl', 'l')
                time.sleep(0.5)
                
                pyautogui.hotkey('ctrl', 'a')
                pyautogui.press('backspace')
                time.sleep(0.3)
                
                pyautogui.write(query, interval=0.05)  # Added interval for reliability
                time.sleep(0.5)
                pyautogui.press('enter')
                time.sleep(1.0)
                
                # Play first result
                pyautogui.press('tab')
                time.sleep(0.5)
                pyautogui.press('enter')
                time.sleep(0.5)
                pyautogui.press('space')
                
                return f" Playing '{query}' on Spotify"

        except Exception as e:
            print(f"⚠️ App search error: {str(e)}")
            return f"Error in app search: {str(e)}"

    def _web_search(self, query: str, platform: str, pattern: Dict) -> str:
        """Handle searches on websites"""
        try:
            # Use keyboard shortcuts instead of coordinates
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.5)
            
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('backspace')
            time.sleep(0.3)
            
            pyautogui.write(query, interval=0.05)  # Added interval for reliability
            time.sleep(0.5)
            pyautogui.press('enter')
            
            return f" Searched for '{query}' on {platform}"

        except Exception as e:
            print(f" Web search error: {str(e)}")
            return f"Error in web search: {str(e)}"

    def focus_window(self, window_name: str) -> bool:
        """Focus a specific window by name"""
        try:
            def callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd).lower()
                    if window_name.lower() in title:
                        if win32gui.IsIconic(hwnd):
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        win32gui.SetForegroundWindow(hwnd)
                        return False
                return True

            win32gui.EnumWindows(callback, None)
            time.sleep(0.5)
            return True
            
        except Exception as e:
            print(f" Window focus error: {str(e)}")
            return False 