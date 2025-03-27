from features.voice_recognition import speak, listen

def test_audio():
    print("Testing audio...")
    speak("Testing, can you hear me?")
    print("If you heard the test message, press spacebar and say something.")
    response = listen()
    if response:
        speak(f"I heard you say: {response}")
    else:
        print("No audio input detected.")

if __name__ == "__main__":
    test_audio() 