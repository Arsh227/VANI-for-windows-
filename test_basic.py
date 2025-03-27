import pyttsx3
import speech_recognition as sr
import time

def test_components():
    # Test text-to-speech
    print("\nTesting text-to-speech...")
    try:
        engine = pyttsx3.init()
        engine.say("Testing speech. Can you hear me?")
        engine.runAndWait()
        print("Speech test completed")
    except Exception as e:
        print(f"Speech error: {str(e)}")

    # Test microphone
    print("\nTesting microphone...")
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Please say something...")
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            print(f"I heard: {text}")
            print("Microphone test completed")
    except Exception as e:
        print(f"Microphone error: {str(e)}")

if __name__ == "__main__":
    test_components() 