from features.voice_recognition import listen, speak
from features.ollama_integration import ask_ollama

def main():
    speak("Hello! I am your Arsh's assistant. How can I help you today?")
    while True:
        command = listen()
        if command:
            if "stop" in command.lower():
                speak("Goodbye!")
                break
            response = ask_ollama(command)
            speak(response)

if __name__ == "__main__":
    main()
