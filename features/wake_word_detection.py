import os
import pyaudio
import speech_recognition as sr
from datetime import datetime
from plyer import notification
import logging

# Configure logging to suppress GRPC warnings
logging.getLogger('absl').setLevel(logging.ERROR)
os.environ['GRPC_PYTHON_LOG_LEVEL'] = 'error'

class WakeWordDetection:
    def __init__(self, default_wake_word="Alexa", notifier=None, tts_service=None):
        try:
            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024,
                input_device_index=self._get_input_device_index()
            )
            
            # Initialize voice recognition
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = False
            self.recognizer.pause_threshold = 0.3
            self.recognizer.phrase_threshold = 0.1
            self.recognizer.non_speaking_duration = 0.2
            self.microphone = sr.Microphone(sample_rate=16000)
            
            # Other settings
            self.config_file = "data/wake_word_config.json"
            self.notifier = notifier
            self.tts_service = tts_service
            self.wake_word = default_wake_word.lower()
            
            # Notification settings
            self.last_notification = None
            self.notification_cooldown = 60  # seconds
            
            print("Voice recognition initialized!")
            
        except Exception as e:
            print(f"Initialization error: {e}")
            raise

    def _get_input_device_index(self):
        """Get default input device index"""
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                return i
        return None

    def __del__(self):
        """Cleanup audio resources"""
        if hasattr(self, 'stream'):
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, 'audio'):
            self.audio.terminate()

    def listen_for_wake_word(self):
        """Listen for wake word with optimized processing"""
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=0.5,
                    phrase_time_limit=1.0
                )
                
                try:
                    text = self.recognizer.recognize_google(
                        audio,
                        language='en-US',
                        show_all=False
                    )
                    
                    if self.wake_word in text.lower():
                        self.notify_wake_word(self.wake_word)
                        if self.tts_service:
                            self.tts_service.stop_speaking()
                        return True
                        
                except sr.UnknownValueError:
                    pass
                    
        except sr.WaitTimeoutError:
            pass
        except Exception as e:
            if "recognition connection failed" not in str(e).lower():
                print(f"Error: {str(e)}")
            
        return False

    def notify_wake_word(self, wake_word: str):
        """Send notification when wake word is detected"""
        now = datetime.now()
        
        # Check cooldown to avoid spam
        if (not self.last_notification or 
            (now - self.last_notification).total_seconds() > self.notification_cooldown):
            
            notification.notify(
                title='Assistant Activated',
                message=f'Wake word "{wake_word}" detected',
                app_icon=None,
                timeout=2,
            )
            self.last_notification = now 