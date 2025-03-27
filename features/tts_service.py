import asyncio
import os
from edge_tts import Communicate
import pygame
import time
import threading

class TTSService:
    def __init__(self, voice="en-IN-NeerjaNeural"):
        self.voice = voice
        self.is_speaking = False
        self.voice_styles = {
            "default": "",
            "friendly": "style=cheerful",
            "calm": "style=calm",
            "cheerful": "style=cheerful",
            "excited": "style=excited"
        }
        self.current_style = "default"
        pygame.mixer.init()
        
        # Add threading lock for speech operations
        self.speech_lock = threading.Lock()
        self.speech_thread = None

    async def _speak_async(self, text: str) -> None:
        """Internal async method to handle TTS"""
        try:
            if not text:
                return
                
            # Apply voice style only if not default
            if self.current_style == "default":
                communicate = Communicate(text, self.voice)
            else:
                voice_with_style = f"{self.voice},{self.voice_styles[self.current_style]}"
                communicate = Communicate(text, voice_with_style)
            await communicate.save("temp_speech.mp3")
            
            # Play audio
            pygame.mixer.music.load("temp_speech.mp3")
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            # Cleanup
            pygame.mixer.music.unload()
            os.remove("temp_speech.mp3")
                
        except Exception as e:
            print(f"TTS error: {e}")
            
    def speak(self, text: str) -> None:
        """Speak text using a separate thread"""
        if text and isinstance(text, str):
            self.speech_thread = threading.Thread(target=self._speak_threaded, args=(text,))
            self.speech_thread.start()

    def _speak_threaded(self, text: str) -> None:
        """Internal method to handle threaded speech"""
        with self.speech_lock:
            self.is_speaking = True
            asyncio.run(self._speak_async(text))
        self.is_speaking = False

    def stop_speaking(self):
        """Stop current speech"""
        try:
            pygame.mixer.music.stop()
            self.is_speaking = False
        except Exception as e:
            print(f"Error stopping speech: {e}")

    def change_voice(self, voice_type="hinglish"):
        """Change TTS voice"""
        try:
            voice_options = {
                "hinglish": "hi-IN-SwaraNeural",
                "english": "en-US-JennyNeural",
                "british": "en-GB-SoniaNeural",
                "indian": "en-IN-NeerjaNeural"
            }
            if voice_type in voice_options:
                self.voice = voice_options[voice_type]
            return f"Changed voice to {voice_type}"
        except Exception as e:
            return f"Error changing voice: {e}"

    def set_style(self, style: str) -> str:
        """Change speaking style"""
        if style in self.voice_styles:
            self.current_style = style
            return f"Changed speaking style to {style}"
        return f"Unknown style: {style}"

    @property
    def speaking(self):
        """Check if TTS is currently speaking"""
        return self.is_speaking

    def is_stopped(self):
        """Check if TTS is stopped"""
        return not self.speaking

    def is_paused(self):
        """Check if TTS is paused"""
        return pygame.mixer.music.get_busy() == 0

    def is_playing(self):
        """Check if TTS is playing"""
        return pygame.mixer.music.get_busy() > 0

 