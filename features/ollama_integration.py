# Standard library imports
import sys
import os
import shutil
import logging
import keyboard
import time
import threading
from queue import Queue, Empty
import speech_recognition as sr
import atexit
import urllib3
import warnings
import signal
import json

# Suppress all warnings
warnings.filterwarnings('ignore')

# Configure logging to suppress all warnings
logging.getLogger('absl').setLevel(logging.ERROR)
logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)
logging.getLogger('comtypes').setLevel(logging.ERROR)
logging.getLogger('PIL').setLevel(logging.ERROR)
os.environ['GRPC_PYTHON_LOG_LEVEL'] = 'error'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
urllib3.disable_warnings()

# Disable GRPC debug logging
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GRPC_TRACE'] = 'none'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # Simplified format
    handlers=[
        logging.StreamHandler()  # Console output only
    ]
)
logger = logging.getLogger(__name__)

# Local imports - using relative imports
from voice_recognition import VoiceRecognition
from tts_service import TTSService
from wake_word_detection import WakeWordDetection
from spotify_control import SpotifyControl
from system_control import SystemControl
from quick_actions import QuickActions
from browser_control import BrowserControl
from file_search import FileManager
from ai_services import AIServices
from camera_control import CameraControl
from search_control import SearchControl
from notification_service import NotificationService
from conversation_handler import ConversationHandler
from conversation_manager import ConversationManager

# Initialize components
print("Initializing components...")
spotify = SpotifyControl()
system = SystemControl()
quick = QuickActions()
browser = BrowserControl()
files = FileManager()

# Initialize TTS engine with specific settings
tts_service = TTSService()
speech_queue = Queue()
is_speaking = False
stop_speaking = False

# Initialize AI services first
ai_services = AIServices()

# Initialize camera
camera = CameraControl()

# Initialize search control
search = SearchControl()

# Initialize notification service first
notifier = NotificationService()

# Initialize voice recognition
voice = VoiceRecognition()

# Initialize wake word detection with notifier and TTS
wake_word = WakeWordDetection(
    notifier=notifier,
    tts_service=tts_service
)

# Initialize conversation handler with AI services
conversation = ConversationHandler(ai_services)

# Initialize conversation manager
conversation_manager = ConversationManager(ai_services)

# Command handlers dictionary - moved to top level for better organization
COMMAND_HANDLERS = {
    "music": {
        "play": lambda t, spotify: spotify.play_music(t.replace("play", "").strip()) if t.replace("play", "").strip() else "Please specify what to play",
        "pause": lambda _, spotify: spotify.pause_music(),
        "stop music": lambda _, spotify: spotify.pause_music(),
        "pause music": lambda _, spotify: spotify.pause_music(),
        "stop song": lambda _, spotify: spotify.pause_music(),
        "pause song": lambda _, spotify: spotify.pause_music(),
        "next": lambda _, spotify: spotify.next_track(),
        "previous": lambda _, spotify: spotify.previous_track(),
        "back": lambda _, spotify: spotify.previous_track()
    },
    "system": {
        "volume up": lambda _, system: system.increase_volume(),
        "volume down": lambda _, system: system.decrease_volume(),
        "increase volume": lambda _, system: system.increase_volume(),
        "decrease volume": lambda _, system: system.decrease_volume(),
    },
    "shortcuts": {
        "copy": lambda _, quick: quick.press_shortcut("copy"),
        "paste": lambda _, quick: quick.press_shortcut("paste"),
        "cut": lambda _, quick: quick.press_shortcut("cut"),
        "select all": lambda _, quick: quick.press_shortcut("select_all"),
        "save": lambda _, quick: quick.press_shortcut("save"),
        "undo": lambda _, quick: quick.press_shortcut("undo")
    },
    "camera": {
        "take picture": lambda _, camera: handle_camera_command(camera),
        "capture image": lambda _, camera: handle_camera_command(camera),
        "what do you see": lambda _, camera: handle_camera_command(camera)
    },
    "files": {
        "open files": lambda _, files: files.open_file_explorer(),
        "search files": lambda t, files: files.search_in_explorer(t.replace("search files", "").replace("for", "").strip()),
        "find file": lambda t, files: files.search_in_explorer(t.replace("find file", "").replace("find", "").strip())
    },
    "search": {
        "search for": lambda t, search: handle_search_command(t, search),
        "find": lambda t, search: handle_search_command(t, search),
        "look up": lambda t, search: handle_search_command(t, search)
    },
    "voice": {
        "change voice to hindi": lambda _, __: tts_service.change_voice("hinglish"),
        "change voice to hinglish": lambda _, __: tts_service.change_voice("hinglish"),
        "change voice to english": lambda _, __: tts_service.change_voice("english")
    },
    "screenshot": {
        "take screenshot": lambda _, system: handle_screenshot_command(system),
        "capture screen": lambda _, system: handle_screenshot_command(system),
        "screenshot": lambda _, system: handle_screenshot_command(system)
    },
    "wake_word": {
        "change wake word to": lambda t, _: wake_word.set_wake_word(t.replace("change wake word to", "").strip()),
        "set wake word to": lambda t, _: wake_word.set_wake_word(t.replace("set wake word to", "").strip())
    }
}

# Add to global variables
STOP_KEYWORDS = {"stop", "halt", "quiet", "silence", "shut up", "stop speaking", "be quiet"}
is_processing = False  # Track if assistant is processing anything
command_queue = Queue()
MAX_QUEUE_SIZE = 5
COMMAND_COOLDOWN = 1.0  # seconds
last_command_time = 0

def cleanup_resources():
    """Clean up all resources properly"""
    try:
        print("\nCleaning up resources...")
        
        # Clean up TTS engine
        global tts_service, spotify, system, browser
        if tts_service:
            try:
                tts_service.stop_speaking()
                tts_service = None
            except:
                pass

        # Clean up Spotify
        if spotify:
            try:
                if hasattr(spotify, 'sp'):
                    spotify.sp = None
                spotify = None
            except:
                pass

        # Clean up System resources
        if system:
            try:
                if hasattr(system, 'volume'):
                    system.volume = None
                system = None
            except:
                pass

        # Clean up Browser
        if browser:
            try:
                if hasattr(browser, 'driver'):
                    browser.cleanup()
                browser = None
            except:
                pass

        # Clean up cache directories
        cache_dirs = [
            '.cache',
            'data/tts_cache',
            'data/captured_images',
            'data/screenshots'
        ]
        
        for cache_dir in cache_dirs:
            try:
                cache_path = os.path.join(os.path.dirname(__file__), cache_dir)
                if os.path.exists(cache_path):
                    for file in os.listdir(cache_path):
                        try:
                            os.remove(os.path.join(cache_path, file))
                        except:
                            pass
            except:
                pass

        print("Cleanup complete!")
        
    except Exception as e:
        print(f"Cleanup error: {str(e)}")
    finally:
        # Don't call sys.exit() here
        pass

# Register cleanup function
atexit.register(cleanup_resources)

def process_speech_queue():
    """Process queued speech in a separate thread"""
    try:
        while True:
            if not speech_queue.empty() and not stop_speaking:
                text = speech_queue.get()
                if text:
                    tts_service.speak(str(text))
            time.sleep(0.1)
    except Exception as e:
        print(f"Speech queue error: {e}")

def speak_worker():
    """Worker thread to handle speech queue"""
    global is_speaking, stop_speaking
    try:
        while True:
            try:
                if not speech_queue.empty() and not stop_speaking:
                    text = speech_queue.get_nowait()
                    if text and str(text).strip():
                        is_speaking = True
                        tts_service.speak(str(text))
                        is_speaking = False
                        stop_speaking = False
            except Empty:
                pass
            except Exception as e:
                print(f"Speech error: {e}")
            time.sleep(0.1)
    except Exception as e:
        print(f"Error in speech worker: {e}")

def speak(text):
    """Speak text using TTS service"""
    if text and str(text).strip():
        try:
            tts_service.speak(str(text))
        except Exception as e:
            print(f"Speak error: {str(e)}")

def listen():
    """Listen to user's voice input"""
    return voice.listen()

def process_voice_input(text=None):
    """Process voice input and get response"""
    try:
        # Get input if not provided
        if text is None:
            text = listen()
        
        # Validate input
        if not text or not isinstance(text, str):
            return None
        
        # Clean and normalize input
        text = text.lower().strip()
        print(f"Processing command: '{text}'")
        
        # Help command
        if "what can you do" in text:
            capabilities = """I'm your personal assistant! Here's what I can do:

🎵 Music Control:
- "Play [song name]" - Play on Spotify
- "Play [song] on YouTube" - Play on YouTube
- "Pause/Stop/Next/Previous" - Control playback
- "Volume up/down" - Adjust volume

🔍 Search & Browse:
- "Search [query] on Google/YouTube"
- "Open/Close [app name]" - Control applications
- "Research [topic]" - Get detailed information

📸 Camera:
- "What do you see" - I'll analyze what's in view
- "Take photo" - Capture a picture
- "Start/Stop recording" - Video control

✈️ Travel & Shopping:
- "Compare flights from [city] to [city]"
- "Compare prices for [product]"
- "Find best deals for [item]"

Just tell me what you need!"""
            speak(capabilities)
            return True
        
        # Stop command
        if any(word in text for word in STOP_KEYWORDS):
            print("\n🛑 Stopping all activities...")
            handle_stop_command()
            return "Stopped all activities"
        
        # Music controls
        try:
            if text.startswith('play'):
                if 'youtube' in text:
                    query = text.replace('play', '').replace('on youtube', '').strip()
                    return browser.play_youtube(query)
                else:
                    query = text.replace('play', '').strip()
                    return spotify.play_music(query)
                    
            if any(cmd in text for cmd in ['pause', 'stop music', 'pause music']):
                return spotify.pause_music()
                
            if 'next' in text:
                return spotify.next_track()
                
            if 'previous' in text or 'back' in text:
                return spotify.previous_track()
        except Exception as e:
            print(f"Music control error: {e}")
            return f"Error controlling music: {str(e)}"

        # Volume controls
        try:
            if 'volume' in text:
                if any(word in text for word in ['up', 'increase']):
                    return system.increase_volume()
                if any(word in text for word in ['down', 'decrease', 'reduce']):
                    return system.decrease_volume()
        except Exception as e:
            print(f"Volume control error: {e}")
            return f"Error adjusting volume: {str(e)}"
            
        # Browser & Search
        if text.startswith('search'):
            if 'youtube' in text:
                query = text.replace('search', '').replace('on youtube', '').strip()
                return browser.search_youtube(query)
            if 'google' in text:
                query = text.replace('search', '').replace('on google', '').strip()
                return browser.search_google(query)

        # App control
        if text.startswith('open'):
            app = text.replace('open', '').strip()
            return quick.open_application(app)
            
        if text.startswith('close'):
            app = text.replace('close', '').strip()
            return quick.close_application(app)

        # Camera features
        if "what do you see" in text:
            print("\n📸 Taking a photo...")
            photo_result = camera.take_photo()
            if "saved" in photo_result:
                photo_path = photo_result.split("as ")[-1].strip()
                print("🔍 Analyzing image with Gemini...")
                
                # Add the prompt for image analysis
                prompt = """Describe what you see in this image in 2-3 sentences. 
                Focus on the main subjects, colors, and important details."""
                
                response = ai_services.analyze_image(photo_path, prompt)
                print("\n👁️ Image Analysis:")
                print("------------------")
                print(response)
                print("------------------\n")
                
                # Speak the analysis
                speak(f"Here's what I see: {response}")
                return True  # Return True to indicate success
            
            speak("I couldn't take a photo")
            return "Camera error: Could not take photo"

        # Flight search
        if ('flights' in text or 'flight' in text) and 'from' in text and 'to' in text:
            try:
                print("\n✈️ Searching flights...")
                from_idx = text.index('from') + 4
                to_idx = text.index('to')
                from_city = text[from_idx:to_idx].strip()
                to_city = text[to_idx + 2:].strip().split()[0]
                return ai_services.handle_flight_comparison(from_city, to_city)
            except Exception as e:
                print(f"Flight search error: {e}")
                return "Could not process flight search"

        # Price comparison
        if 'compare prices' in text or 'price check' in text:
            try:
                print("\n💰 Comparing prices...")
                product = text.split('for')[-1].strip() if 'for' in text else text.split('prices')[-1].strip()
                return ai_services.handle_price_comparison(product)
            except Exception as e:
                print(f"Price comparison error: {e}")
                return "Could not compare prices"

        # Research
        if text.startswith('research'):
            topic = text.replace('research', '').strip()
            print(f"\n📚 Researching: {topic}")
            return ai_services.handle_research_task(topic)

        # Default to conversation
        response = conversation.process_user_input(text)
        if response:
            print(f"\nResponse: {response}")
            return response
        return "I'm not sure how to help with that"

    except Exception as e:
        print(f"Voice input error: {e}")
        return f"Error processing command: {str(e)}"

# Make sure to start the speech thread
speech_thread = threading.Thread(target=speak_worker, daemon=True)
speech_thread.start()

def validate_command(command):
    """Validate command input"""
    if not command:
        raise ValueError("No command provided")
    if not isinstance(command, str):
        raise ValueError("Command must be a string")
    return command.lower().strip()

def handle_camera_command(camera_obj):
    """Handle camera-related commands"""
    try:
        print("Opening camera...")
        image_path, capture_msg = camera_obj.capture_image()
        
        if not image_path:
            return capture_msg
            
        try:
            # Analyze image
            analysis = ai_services.analyze_image(image_path)
            
            # Delete image after analysis
            try:
                os.remove(image_path)
                print(f"Deleted temporary image: {image_path}")
            except Exception as e:
                print(f"Error deleting image: {e}")
            
            return analysis
            
        except Exception as e:
            # Ensure image is deleted even if analysis fails
            try:
                os.remove(image_path)
            except:
                pass
            raise e
            
    except Exception as e:
        return f"Camera error: {str(e)}"

def handle_open_command(text, quick, browser):
    """Handle open commands with validation"""
    try:
        target = text.replace("open", "").strip().lower()
        if not target:
            return "Please specify what to open"

        # List of common applications with variations
        applications = {
            "spotify": ["spotify"],
            "chrome": ["chrome", "google chrome"],
            "firefox": ["firefox", "mozilla firefox"],
            "notepad": ["notepad"],
            "word": ["word", "microsoft word", "winword"],
            "excel": ["excel", "microsoft excel"],
            "calculator": ["calc", "calculator"],
            "paint": ["paint", "mspaint"],
            "settings": ["settings", "ms-settings:"],
            "task manager": ["taskmgr", "task manager"],
            "control panel": ["control", "control panel"],
            "cmd": ["cmd", "command prompt"],
            "powershell": ["powershell"],
            "zoom": ["zoom"],
            "teams": ["teams", "microsoft teams"],
            "skype": ["skype"],
            "vlc": ["vlc", "vlc player"],
            "vscode": ["code", "visual studio code"],
            "whatsapp": ["whatsapp", "whatsapp.exe", "whatsapp desktop"],
            "discord": ["discord"],
            "telegram": ["telegram"],
            "steam": ["steam"],
            "epic": ["epic games", "epic"],
            "outlook": ["outlook"],
            "edge": ["edge", "microsoft edge"]
        }

        # Check if it's a known application
        for app_name, variations in applications.items():
            if any(variation in target for variation in variations):
                print(f"Opening {app_name}...")  # Debug print
                return quick.open_application(app_name)
            
        # Handle special folders
        if "files" in target or "explorer" in target:
            return files.open_file_explorer()
        if "documents" in target:
            return files.open_documents()
        if "downloads" in target:
            return files.open_downloads()
        if "pictures" in target:
            return files.open_pictures()
        
        # If not found in known apps, try to open as-is
        print(f"Trying to open unknown application: {target}")  # Debug print
        return quick.open_application(target)
            
    except Exception as e:
        return f"Error opening: {str(e)}"

def handle_close_command(text, quick, browser):
    """Handle close commands with validation"""
    try:
        target = text.replace("close", "").strip().lower()
        if not target:
            return "Please specify what to close"

        # Handle special cases first
        if "all" in target or "everything" in target:
            # Close browser windows first
            browser.close_all()
            # Then try to close other applications
            for app in quick.process_names.keys():
                quick.close_application(app)
            return "Attempted to close all applications"
            
        # Check for browser-specific commands
        if any(site in target for site in ["chrome", "firefox", "edge"]):
            return quick.close_application(target)
            
        if any(site in target for site in ["youtube", "google", "facebook"]):
            return browser.close_website(target)
        
        # Try to close as application
        return quick.close_application(target)
            
    except Exception as e:
        return f"Error closing: {str(e)}"

def execute_single_command(command):
    """Execute a single command with interactive follow-up"""
    try:
        text = validate_command(command)
        
        # Handle closing commands first
        if "close" in text:
            return handle_close_command(text, quick, browser)
            
        # Handle screenshot commands first
        if any(phrase in text for phrase in ["take screenshot", "capture screen", "screenshot"]):
            print("Taking screenshot...")  # Debug print
            return handle_screenshot_command(system)
            
        # Handle Spotify commands first
        if "spotify" in text.lower() or "play" in text.lower():
            query = text.lower()
            
            # Handle play commands
            if "play" in query:
                song = query.replace("play", "").replace("on spotify", "").replace("spotify", "").strip()
                return spotify.play_music(song)
                
            # Handle other Spotify commands
            elif "pause" in text or "stop" in text:
                return spotify.pause_music()
            elif "next" in text:
                return spotify.next_track()
            elif "previous" in text or "back" in text:
                return spotify.previous_track()
            
            return "Please specify a Spotify command"

        # Handle file commands with interaction
        if "files" in text or "file explorer" in text:
            response = files.open_file_explorer()
            if "Would you like to search" in response:
                speak(response)
                search_response = listen()
                
                if search_response and any(word in search_response.lower() for word in ["yes", "yeah", "sure", "okay"]):
                    speak("What would you like to search for?")
                    search_query = listen()
                    
                    if search_query:
                        results = files.search_in_explorer(search_query)
                        speak(results)
                        
                        # Ask if user wants to open any of the found files
                        if "Found" in results:
                            speak("Would you like to open any of these files?")
                            open_response = listen()
                            
                            if open_response and any(word in open_response.lower() for word in ["yes", "yeah", "sure", "okay"]):
                                speak("Which file number would you like to open?")
                                file_num = listen()
                                if file_num and file_num.isdigit():
                                    return files.open_file_by_number(int(file_num))
                                
                        return results
                    return "No search query provided"
                return "Okay, File Explorer is ready to use"
            return response

        # Check direct commands first
        # System commands
        for cmd, handler in COMMAND_HANDLERS["system"].items():
            if cmd in text:
                return handler(text, system)
                
        # Keyboard shortcuts
        for cmd, handler in COMMAND_HANDLERS["shortcuts"].items():
            if cmd in text:
                return handler(text, quick)
        
        # Music commands
        for cmd, handler in COMMAND_HANDLERS["music"].items():
            if cmd in text:
                return handler(text, spotify)

        # Camera commands
        for cmd, handler in COMMAND_HANDLERS["camera"].items():
            if cmd in text:
                return handler(text, camera)

        # Handle opening commands
        if "open" in text:
            return handle_open_command(text, quick, browser)
            
        # Handle search commands
        if "search" in text:
            if "youtube" in text:
                query = text.replace("search", "").replace("on youtube", "").replace("youtube", "").strip()
                return browser.search_site("youtube", query) if query else "Please specify what to search on YouTube"
            query = text.replace("search", "").strip()
            return browser.search_site("google", query) if query else "Please specify what to search for"
        
        # Handle typing commands
        if any(cmd in text for cmd in ["type", "write"]):
            content = text.replace("type", "").replace("write", "").strip()
            return quick.type_text(content) if content else "Please specify what to type"

        # Basic conversation handling without AI interpretation
        if any(greeting in text for greeting in ["hi", "hello", "hey"]):
            return "Hello! How can I help you?"
        if "joke" in text:
            return "Why don't scientists trust atoms? Because they make up everything!"
        if "thank" in text:
            return "You're welcome!"
        
        # AI interpretation as fallback for unknown commands
        return ai_services.query_gemini(command)
        
    except ValueError as ve:
        return f"Invalid command: {str(ve)}"
    except Exception as e:
        print(f"Error executing command: {str(e)}")
        return f"Error: {str(e)}"

def ask_ollama(query):
    """Handle multiple commands and AI queries"""
    try:
        # Split into multiple commands using conjunctions
        commands = []
        
        # Split by different conjunctions
        for splitter in [" and then ", " then ", " and ", ", "]:
            if splitter in query.lower():
                commands = [cmd.strip() for cmd in query.lower().split(splitter) if cmd.strip()]
                break
        
        # If no conjunctions found, treat as single command
        if not commands:
            commands = [query]
        
        # Execute each command in sequence
        responses = []
        for cmd in commands:
            print(f"\nExecuting: {cmd}")
            response = execute_single_command(cmd)
            
            # If command not recognized, use Gemini
            if response is None:
                response = ai_services.query_gemini(cmd)
            
            responses.append(response)
            time.sleep(0.5)  # Small delay between commands
        
        # Return combined responses
        return "\n".join(responses)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return "I encountered an error processing your request."

def handle_search_command(text, search_control):
    """Handle search commands across platforms"""
    try:
        # Remove command words
        query = text.lower()
        for cmd in ["search for", "find", "look up", "search"]:
            query = query.replace(cmd, "").strip()

        # Detect platform
        platform = "google"  # default
        for site in ["youtube", "spotify", "google"]:
            if site in query:
                platform = site
                query = query.replace(site, "").replace("on", "").strip()

        # Execute search
        return search_control.perform_search(query, platform)

    except Exception as e:
        return f"Error processing search: {str(e)}"

def handle_screenshot_command(system_obj):
    """Handle screenshot commands"""
    try:
        print("Capturing screenshot...")
        filepath, msg = system_obj.take_screenshot()
        
        if filepath and os.path.exists(filepath):
            try:
                analysis = ai_services.analyze_image(filepath)
                
                # Delete screenshot after analysis
                try:
                    os.remove(filepath)
                    print(f"Deleted temporary screenshot: {filepath}")
                except Exception as e:
                    print(f"Error deleting screenshot: {e}")
                
                return f"Screenshot analyzed. Here's what I see: {analysis}"
                
            except Exception as e:
                # Ensure screenshot is deleted even if analysis fails
                try:
                    os.remove(filepath)
                except:
                    pass
                return f"Error analyzing screenshot: {str(e)}"
        else:
            return "Failed to take screenshot"
            
    except Exception as e:
        return f"Screenshot error: {str(e)}"

def greet_user():
    """Greet the user when assistant starts"""
    greeting = "Hello Arsh, How is your day today?"
    print(f"\n {greeting}")
    notifier.notify("AI Assistant", greeting)
    speak(greeting)
    time.sleep(1)

def setup_directories():
    """Ensure only required directories exist"""
    required_dirs = [
        'data/captured_images',    # For camera captures
        'data/screenshots',        # For screenshots
        'data/tts_cache'          # For TTS caching
    ]
    
    # Create required directories
    for dir_path in required_dirs:
        os.makedirs(os.path.join(os.path.dirname(__file__), dir_path), exist_ok=True)

def initialize_data_files():
    """Initialize only necessary data files"""
    data_files = {
        'data/command_history.json': {},    # For command history
        'data/tts_cache/index.json': {}     # For TTS cache index
    }
    
    for file_path, default_data in data_files.items():
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if not os.path.exists(full_path):
            with open(full_path, 'w') as f:
                json.dump(default_data, f)

def cleanup_unused_files():
    """Remove unnecessary files and folders"""
    unused_paths = [
        'features/logs/assistant.log',  # Using console output instead
        'features/logs/assistant_*.log',  # Remove dated logs
        'features/.cache',             
        'test_audio.py',              
        'test_basic.py',
        'test_speak.py',
        'test_speech.py',
        'test_spotify.py',
        'main.py/main.py',            
        'config.py'                    
    ]
    
    for path in unused_paths:
        try:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        except Exception as e:
            print(f"Error removing {path}: {e}")

def handle_stop_command():
    """Universal stop command to halt all activities"""
    global is_processing
    try:
        # Stop TTS
        if tts_service:
            tts_service.stop_speaking()
            tts_service.is_speaking = False
            
        # Stop Spotify if active
        try:
            if spotify:
                spotify.pause_music()
        except:
            pass
            
        # Stop browser playback if active
        try:
            if browser:
                browser.stop_playback()
        except:
            pass
            
        # Reset processing flag
        is_processing = False
        
        print("\n🛑 Stopping all activities...")
        
    except Exception as e:
        print(f"Error stopping activities: {str(e)}")
    finally:
        # Always acknowledge stop command
        speak("Stopped.")

def process_command_queue():
    """Process commands in queue"""
    while True:
        try:
            if is_processing:
                time.sleep(0.1)
                continue
            
            try:
                command = command_queue.get_nowait()
                process_voice_input(command)
            except Empty:
                time.sleep(0.1)
            except Exception as e:
                print(f"Error processing command: {e}")
                time.sleep(0.1)
        except Exception as e:
            print(f"Queue processing error: {e}")
            break

def cleanup_memory():
    """Periodic memory cleanup"""
    try:
        import gc
        gc.collect()
        
        # Clear conversation history if too long
        if hasattr(conversation, 'chat') and len(conversation.chat.history) > 50:
            conversation.reset_chat()
            
        # Clear caches periodically
        if hasattr(ai_services, 'prompt_cache'):
            ai_services.prompt_cache.clear()
            
        # Clear audio cache
        if hasattr(tts_service, 'audio_cache'):
            tts_service.audio_cache.clear()
            
    except Exception as e:
        print(f"Memory cleanup error: {str(e)}")

def can_process_command():
    """Check if enough time has passed since last command"""
    global last_command_time
    current_time = time.time()
    if current_time - last_command_time >= COMMAND_COOLDOWN:
        last_command_time = current_time
        return True
    return False

def process_command(command):
    command = command.lower().strip()
    
    if not command:
        return "No command received"
        
    try:
        # Check for complex tasks with "and"
        if " and " in command or "then" in command:
            return ai_services.handle_complex_task(command)
            
        # Regular command processing
        if command.startswith(('what', 'how', 'why')):
            return handle_query_command(command)
            
        if command.startswith(('open', 'start', 'launch')):
            return handle_action_command(command)
            
        if command.startswith('stop'):
            return handle_stop_command()
            
        response = ai_services.query_gemini(command)
        return response
        
    except Exception as e:
        print(f"Command error: {e}")
        return "Error processing command"

def handle_query_command(command):
    """Handle information queries efficiently"""
    try:
        # Use shorter context window
        response = ai_services.query_gemini(
            command,
            generation_config={"max_output_tokens": 50}
        )
        return response
    except Exception as e:
        return f"Query error: {e}"

def handle_action_command(command):
    """Handle action commands like open, start, launch"""
    try:
        # Extract target from command
        for action in ["open", "start", "launch"]:
            if action in command:
                target = command.replace(action, "").strip()
                if target:
                    return handle_open_command(target, quick, browser)
        return "Please specify what to open"
    except Exception as e:
        return f"Action error: {e}"

def main():
    print("\nAI Assistant Ready!")
    print("Waiting for wake word...")
    
    greet_user()
    
    try:
        while True:
            try:
                # Check for wake word
                result = wake_word.listen_for_wake_word()
                
                if result:
                    print("\n Wake word detected!")
                    
                    # Stop any ongoing speech
                    if tts_service and tts_service.is_speaking:
                        print("Stopping current speech...")
                    tts_service.stop_speaking()
                    time.sleep(0.1)
                    
                    if isinstance(result, str):  # Got immediate command
                        print(f"Got command with wake word: '{result}'")
                        response = conversation.process_user_input(result)
                        if response:
                            print(f" Response: {response}")
                            speak(str(response))
                    else:  # Just wake word detected
                        process_voice_input()
                
                # Brief pause to prevent CPU overuse
                time.sleep(0.05)
                
            except Exception as e:
                print(f"\n⚠️ Error in main loop: {str(e)}")
                time.sleep(0.1)
                
            # Check for quit
            if keyboard.is_pressed('q'):
                print("\nShutting down...")
                break
            
    except KeyboardInterrupt:
        print("\nReceived interrupt signal...")
    finally:
        cleanup_resources()

if __name__ == "__main__":
    try:
        # Clean up unnecessary files first
        cleanup_unused_files()
        
        # Setup required directories
        setup_directories()
        initialize_data_files()
        
        # Register cleanup
        atexit.register(cleanup_resources)
        
        # Handle interrupts gracefully
        def signal_handler(signum, frame):
            print("\nReceived interrupt signal...")
            cleanup_resources()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        
        # Start the main program
        threading.Thread(target=speak_worker, daemon=True).start()
        main()
        
    except KeyboardInterrupt:
        print("\nReceived interrupt signal...")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
    finally:
        cleanup_resources()
        cleanup_resources()