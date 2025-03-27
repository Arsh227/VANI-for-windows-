import os
from typing import Dict, List, Optional, Tuple
from browser_control import BrowserControl
from spotify_control import SpotifyControl
from system_control import SystemControl
from quick_actions import QuickActions
from camera_control import CameraControl
from ai_services import AIServices

class CommandHandler:
    def __init__(self):
        # Initialize all services
        self.browser = BrowserControl()
        self.spotify = SpotifyControl()
        self.system = SystemControl()
        self.quick = QuickActions()
        self.camera = CameraControl()
        self.ai_services = AIServices()
        
        # Set up command history directory
        self.history_dir = os.path.join(os.path.dirname(__file__), 'data', 'command_history')
        os.makedirs(self.history_dir, exist_ok=True)
        
        # Command patterns with typing command added
        self.command_patterns: Dict[str, List[str]] = {
            'play': ['play', 'start music', 'start playing'],
            'stop': ['stop', 'pause', 'end'],
            'volume': ['volume up', 'volume down', 'increase volume', 'decrease volume'],
            'search': ['search', 'look up', 'find'],
            'open': ['open', 'launch', 'start'],
            'close': ['close', 'exit', 'quit'],
            'camera': ['take photo', 'what do you see', 'capture'],
            'research': ['research', 'study', 'investigate'],
            'compare': ['compare prices', 'compare flights'],
            'type': ['type', 'write']
        }
        
        # Command history with timestamps
        self.command_history: List[Tuple[str, float]] = []
        self.max_history = 10
        self.history_file = os.path.join(self.history_dir, 'history.txt')
        self._load_history()

    def _load_history(self) -> None:
        """Load command history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            cmd, timestamp = line.strip().split('|')
                            self.command_history.append((cmd, float(timestamp)))
        except Exception as e:
            print(f"Error loading history: {e}")

    def _save_history(self) -> None:
        """Save command history to file"""
        try:
            with open(self.history_file, 'w') as f:
                for cmd, timestamp in self.command_history:
                    f.write(f"{cmd}|{timestamp}\n")
        except Exception as e:
            print(f"Error saving history: {e}")

    def execute_command(self, text: str) -> Optional[str]:
        """Execute a command based on text input"""
        try:
            text = text.lower().strip()
            
            # Add to history
            self.add_to_history(text)
            
            # Check for type command first
            if text.startswith('type '):
                content = text[5:].strip()  # Remove 'type ' from the start
                return self.quick.type_text(content)
            
            # Check each command pattern
            for cmd_type, patterns in self.command_patterns.items():
                if any(pattern in text for pattern in patterns):
                    return self.route_command(cmd_type, text)
                    
            return None
            
        except Exception as e:
            print(f"Command execution error: {e}")
            return f"Error executing command: {str(e)}"

    def route_command(self, cmd_type: str, text: str) -> Optional[str]:
        """Route command to appropriate handler"""
        try:
            if cmd_type == 'play':
                if 'youtube' in text:
                    query = text.replace('play', '').replace('on youtube', '').strip()
                    from browser_control import browser
                    return browser.play_youtube(query)
                else:
                    query = text.replace('play', '').strip()
                    from spotify_control import spotify
                    return spotify.play_music(query)
                    
            elif cmd_type == 'stop':
                from ollama_integration import handle_stop_command
                return handle_stop_command()
                
            elif cmd_type == 'volume':
                from system_control import system
                if any(word in text for word in ['up', 'increase']):
                    return system.increase_volume()
                return system.decrease_volume()
                
            elif cmd_type == 'search':
                from browser_control import browser
                if 'youtube' in text:
                    query = text.replace('search', '').replace('on youtube', '').strip()
                    return browser.search_youtube(query)
                query = text.replace('search', '').replace('on google', '').strip()
                return browser.search_google(query)
                
            elif cmd_type == 'open':
                from quick_actions import quick
                app = text.replace('open', '').strip()
                return quick.open_application(app)
                
            elif cmd_type == 'close':
                from quick_actions import quick
                app = text.replace('close', '').strip()
                return quick.close_application(app)
                
            elif cmd_type == 'camera':
                from camera_control import camera
                if 'what do you see' in text:
                    return camera.analyze_view()
                return camera.take_photo()
                
            elif cmd_type == 'research':
                from ai_services import ai_services
                topic = text.replace('research', '').strip()
                return ai_services.handle_research_task(topic)
                
            elif cmd_type == 'compare':
                from ai_services import ai_services
                if 'flight' in text:
                    return ai_services.handle_flight_comparison(text)
                return ai_services.handle_price_comparison(text)
                
            elif cmd_type == 'type':
                content = text.replace('type', '', 1).strip()  # Remove first occurrence of 'type'
                return self.quick.type_text(content)
                
            return None
            
        except Exception as e:
            print(f"Command routing error: {e}")
            return f"Error routing command: {str(e)}"

    def add_to_history(self, command: str) -> None:
        """Add command to history with timestamp and save"""
        import time
        self.command_history.append((command, time.time()))
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)
        self._save_history()

    def get_last_command(self) -> Optional[Tuple[str, float]]:
        """Get most recent command with timestamp"""
        return self.command_history[-1] if self.command_history else None

    def clear_history(self) -> None:
        """Clear command history"""
        self.command_history.clear() 