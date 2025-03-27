import os
import subprocess
import psutil
import pyautogui
import keyboard
import time
import winreg
import random
import pyperclip
from typing import Optional

class QuickActions:
    def __init__(self):
        # Common keyboard shortcuts
        self.shortcuts = {
            "copy": ["ctrl", "c"],
            "paste": ["ctrl", "v"],
            "cut": ["ctrl", "x"],
            "select_all": ["ctrl", "a"],
            "save": ["ctrl", "s"],
            "undo": ["ctrl", "z"],
            "redo": ["ctrl", "y"],
            "find": ["ctrl", "f"],
            "new_tab": ["ctrl", "t"],
            "close_tab": ["ctrl", "w"],
            "switch_tab": ["ctrl", "tab"],
            "refresh": ["f5"],
            "screenshot": ["win", "prtsc"]
        }
        print("Quick actions initialized!")
        
        # Common process names for closing apps
        self.process_names = {
            "whatsapp": ["WhatsApp.exe"],
            "chrome": ["chrome.exe"],
            "firefox": ["firefox.exe"],
            "spotify": ["Spotify.exe"],
            "notepad": ["notepad.exe"],
            "word": ["WINWORD.EXE"],
            "excel": ["EXCEL.EXE"],
            "teams": ["Teams.exe"],
            "discord": ["Discord.exe"],
            "telegram": ["Telegram.exe"],
            "vlc": ["vlc.exe"],
            "vscode": ["Code.exe"]
        }

        self._should_stop = False

        self.search_bar_coords = {
            'chrome': (450, 60),    # Chrome search/URL bar
            'firefox': (450, 60),   # Firefox search/URL bar
            'edge': (450, 60),      # Edge search/URL bar
            'notepad': None,        # Will use keyboard shortcuts
            'word': None            # Will use keyboard shortcuts
        }
        pyautogui.PAUSE = 0.1  # Reduce delay between actions

    def open_application(self, app_name):
        """Open application using subprocess and registry paths"""
        try:
            # Try to get path from registry first
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\\" + app_name + ".exe")
                path = winreg.QueryValue(key, None)
                winreg.CloseKey(key)
                
                # Verify path exists
                if os.path.exists(path):
                    subprocess.Popen(path)
                    return f"Opened {app_name}"
                    
            except:
                # Fallback to basic paths
                program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
                app_paths = {
                    'notepad': os.path.join(os.environ['WINDIR'], 'notepad.exe'),
                    'word': os.path.join(program_files, 'Microsoft Office\\root\\Office16\\WINWORD.EXE'),
                    'excel': os.path.join(program_files, 'Microsoft Office\\root\\Office16\\EXCEL.EXE'),
                    'chrome': os.path.join(program_files, 'Google\\Chrome\\Application\\chrome.exe'),
                    'firefox': os.path.join(program_files, 'Mozilla Firefox\\firefox.exe'),
                    'spotify': os.path.join(os.environ['APPDATA'], 'Spotify\\Spotify.exe')
                }
                
                exe_path = app_paths.get(app_name.lower())
                if exe_path and os.path.exists(exe_path):
                    subprocess.Popen(exe_path)
                else:
                    subprocess.Popen(f"{app_name}.exe", shell=True)
                
            time.sleep(1)
            return f"Opened {app_name}"
            
        except Exception as e:
            print(f"Error opening application: {str(e)}")
            return f"Error opening {app_name}: {str(e)}"

    def close_application(self, app_name):
        """Close application by name"""
        try:
            app_name = app_name.lower()
            closed = False
            
            # Get process names to look for
            process_map = {
                'notepad': ['notepad.exe'],
                'spotify': ['spotify.exe'],
                'chrome': ['chrome.exe'],
                'firefox': ['firefox.exe'],
                'word': ['winword.exe'],
                'excel': ['excel.exe'],
                'teams': ['teams.exe'],
                'discord': ['discord.exe'],
                'telegram': ['telegram.exe'],
                'whatsapp': ['whatsapp.exe']
            }
            
            # Get target process names
            targets = process_map.get(app_name, [f"{app_name}.exe"])
            
            # Try to close the application
            for proc in psutil.process_iter(['pid', 'name']):
                proc_name = proc.info['name'].lower()
                if any(target.lower() in proc_name for target in targets):
                    try:
                        process = psutil.Process(proc.info['pid'])
                        process.terminate()
                        closed = True
                        time.sleep(0.5)  # Wait for process to close
                    except:
                        try:
                            process.kill()
                            closed = True
                            time.sleep(0.5)
                        except:
                            pass
            
            return f"Closed {app_name}" if closed else f"Could not find {app_name} running"
            
        except Exception as e:
            return f"Error closing {app_name}: {str(e)}"

    def press_shortcut(self, shortcut_name):
        """Execute keyboard shortcut"""
        try:
            if shortcut_name in self.shortcuts:
                keys = self.shortcuts[shortcut_name]
                # Press all keys in the shortcut
                for key in keys:
                    keyboard.press(key)
                # Release in reverse order
                for key in reversed(keys):
                    keyboard.release(key)
                return f"Executed {shortcut_name} shortcut"
            return f"Unknown shortcut: {shortcut_name}"
        except Exception as e:
            print(f"⚠️ Shortcut error: {str(e)}")
            return f"Error executing shortcut: {str(e)}"

    def type_text(self, text: str) -> Optional[str]:
        """Enhanced typing with context awareness"""
        try:
            if not text:
                return "No text to type"

            # Wait briefly for stability
            time.sleep(0.2)
            
            # Get active window title
            active_window = pyautogui.getActiveWindow()
            if not active_window:
                return "No active window found"
                
            window_title = active_window.title.lower()
            
            # Handle different contexts
            if any(browser in window_title for browser in ['chrome', 'firefox', 'edge']):
                # Browser context - find and click search bar
                self._handle_browser_typing(text, window_title)
                
            elif any(editor in window_title for editor in ['notepad', 'word', '.txt', '.doc']):
                # Text editor context - select all and replace
                self._handle_editor_typing(text)
                
            else:
                # Default typing behavior
                self._simple_type(text)
            
            return f"Typed: {text}"
            
        except Exception as e:
            print(f"Typing error: {e}")
            return f"Error typing text: {str(e)}"

    def _handle_browser_typing(self, text: str, window_title: str):
        """Handle typing in browser search bars"""
        try:
            # Focus on search bar
            keyboard.press_and_release('ctrl+l')
            time.sleep(0.1)
            
            # Clear existing text
            keyboard.press_and_release('ctrl+a')
            keyboard.press_and_release('backspace')
            time.sleep(0.1)
            
            # Type new text
            pyperclip.copy(text)  # Use clipboard for reliable unicode
            keyboard.press_and_release('ctrl+v')
            time.sleep(0.1)
            
            # Press enter
            keyboard.press_and_release('enter')
            
        except Exception as e:
            print(f"Browser typing error: {e}")
            self._simple_type(text)  # Fallback to simple typing

    def _handle_editor_typing(self, text: str):
        """Handle typing in text editors"""
        try:
            active_window = pyautogui.getActiveWindow()
            window_title = active_window.title.lower()
            
            # Special handling for Word documents
            if 'word' in window_title:
                # Just paste the text at current cursor position
                pyperclip.copy(text)  # Use clipboard for reliable unicode
                keyboard.press_and_release('ctrl+v')
                time.sleep(0.1)
            else:
                # For other editors, use the original behavior
                # Select all existing text
                keyboard.press_and_release('ctrl+a')
                time.sleep(0.1)
                
                # Delete selection
                keyboard.press_and_release('backspace')
                time.sleep(0.1)
                
                # Type new text
                pyperclip.copy(text)  # Use clipboard for reliable unicode
                keyboard.press_and_release('ctrl+v')
                time.sleep(0.1)
                
                # Press enter
                keyboard.press_and_release('enter')
            
        except Exception as e:
            print(f"Editor typing error: {e}")
            self._simple_type(text)  # Fallback to simple typing

    def _simple_type(self, text: str):
        """Basic typing with faster speed"""
        try:
            # Type text with much faster interval (5x faster)
            pyautogui.write(text, interval=0.01)  # Changed from 0.05 to 0.01
            time.sleep(0.1)  # Reduced wait time
            
        except Exception as e:
            print(f"Simple typing error: {e}")
            raise

    def press_key(self, key):
        """Press a single key"""
        try:
            keyboard.press_and_release(key)
            return f"Pressed {key}"
        except Exception as e:
            print(f"⚠️ Key press error: {str(e)}")
            return f"Error pressing key: {str(e)}"

    def press_keys_combination(self, *keys):
        """Press multiple keys in combination"""
        try:
            # Press all keys
            for key in keys:
                keyboard.press(key)
            time.sleep(0.1)  # Brief hold
            # Release in reverse order
            for key in reversed(keys):
                keyboard.release(key)
            return f"Pressed keys: {' + '.join(keys)}"
        except Exception as e:
            print(f"⚠️ Key combination error: {str(e)}")
            return f"Error pressing keys: {str(e)}"

    def simulate_typing(self, text, delay=0.005):
        """Simulate typing with faster but still natural delays"""
        try:
            if not text:
                return "No text to type"

            # Ensure window is focused
            time.sleep(0.2)
            
            # Type the text character by character
            for char in text:
                if char == '\n':
                    pyautogui.press('enter')
                    time.sleep(delay)
                else:
                    pyautogui.write(char)
                    time.sleep(delay + random.uniform(0.001, 0.002))
            
            return f"Typed: {text}"
            
        except Exception as e:
            print(f"Typing error: {e}")
            return f"Error typing text: {str(e)}"

    def create_word_document(self, content: str) -> str:
        """Create and type content in a new Word document"""
        try:
            # Check if Word is already running
            word_running = False
            for proc in psutil.process_iter(['pid', 'name']):
                if 'WINWORD.EXE' in proc.info['name'].upper():
                    word_running = True
                    break
            
            if not word_running:
                print("Opening Microsoft Word...")
                self.open_application('word')
                time.sleep(3)  # Wait for Word to fully load
            
            # Create new document using keyboard shortcuts
            keyboard.press_and_release('ctrl+n')
            time.sleep(1)
            
            # Press alt+h to ensure we're in the Home tab
            keyboard.press_and_release('alt+h')
            time.sleep(0.5)
            
            # Press esc to clear any ribbon focus
            keyboard.press_and_release('esc')
            time.sleep(0.5)
            
            # Type content using clipboard for reliability
            print("Writing content...")
            pyperclip.copy(content)
            keyboard.press_and_release('ctrl+v')
            time.sleep(1)
            
            # Save the document (Ctrl+S)
            keyboard.press_and_release('ctrl+s')
            time.sleep(1)
            
            return "Document has been created and written. Please save it to your desired location."
            
        except Exception as e:
            print(f"Word document error: {e}")
            return f"Error creating Word document: {str(e)}" 