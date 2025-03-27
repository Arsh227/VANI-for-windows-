import speech_recognition as sr
import time

class VoiceRecognition:
    def __init__(self):
        try:
            self.recognizer = sr.Recognizer()
            # Optimized settings for faster processing
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = False  # Fixed threshold for faster processing
            self.recognizer.pause_threshold = 0.8
            self.recognizer.phrase_threshold = 0.4
            self.recognizer.non_speaking_duration = 0.4
            
            print("Voice recognition initialized!")
        except Exception as e:
            print(f"Voice recognition initialization error: {e}")
            raise

    def listen(self):
        """Listen to user's voice input using Google Speech Recognition"""
        with sr.Microphone() as source:
            try:
                print("\nListening...")
                
                # Quick noise adjustment
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                
                # Optimized listening timeouts
                audio = self.recognizer.listen(
                    source,
                    timeout=5,              # Balanced timeout
                    phrase_time_limit=10    # Enough for complete sentences
                )
                
                # Quick processing message
                print("Processing...", end='\r')
                
                # Faster recognition
                text = self.recognizer.recognize_google(
                    audio,
                    language='en-US',
                    show_all=False
                )
                if text:
                    text = text.lower().strip()
                    print(f"\nRecognized: '{text}'")
                    return text
                    
            except sr.WaitTimeoutError:
                print("Listening timed out")
                return None
            except sr.UnknownValueError:
                print("Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"Speech service error: {e}")
                return None
            except Exception as e:
                print(f"Error in voice recognition: {str(e)}")
                return None 