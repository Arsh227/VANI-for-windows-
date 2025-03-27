import pyttsx3
import speech_recognition as sr
import time

def test_voice_components():
    """Test both speech and recognition"""
    print("\n=== Voice System Test ===\n")
    
    # 1. Test Text-to-Speech
    print("Testing speech engine...")
    try:
        engine = pyttsx3.init()
        engine.say("This is a test message. Can you hear me?")
        engine.runAndWait()
        print("✓ Speech test passed")
    except Exception as e:
        print(f"✗ Speech test failed: {str(e)}")
    
    time.sleep(2)
    
    # 2. Test Speech Recognition
    print("\nTesting microphone...")
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Please say something...")
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            print(f"I heard: {text}")
            print("✓ Microphone test passed")
    except Exception as e:
        print(f"✗ Microphone test failed: {str(e)}")

if __name__ == "__main__":
    test_voice_components()