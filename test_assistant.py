import os
import sys
from time import sleep

def test_assistant():
    """Quick test of core assistant features"""
    print("\n=== AI Assistant Test ===\n")
    
    # 1. Test Voice
    print("Testing Voice System...")
    try:
        from features.voice_recognition import speak
        speak("Hello, this is a test message")
        print("✓ Voice test passed")
    except Exception as e:
        print(f"✗ Voice test failed: {str(e)}")
    
    sleep(2)  # Wait between tests
    
    # 2. Test Ollama
    print("\nTesting Ollama Integration...")
    try:
        from features.ollama_integration import ask_ollama
        response = ask_ollama("What is the time?")
        print(f"Ollama response: {response}")
        print("✓ Ollama test passed")
    except Exception as e:
        print(f"✗ Ollama test failed: {str(e)}")
    
    sleep(2)
    
    # 3. Test System Controls
    print("\nTesting System Controls...")
    try:
        from features.system_control import SystemControl
        system = SystemControl()
        # Test volume
        system.adjust_volume("increase")
        sleep(1)
        system.adjust_volume("decrease")
        print("✓ System controls test passed")
    except Exception as e:
        print(f"✗ System controls test failed: {str(e)}")
    
    # 4. Test AI Services
    print("\nTesting AI Services...")
    try:
        from features.ai_services import AIServices
        ai = AIServices()
        result = ai.handle_complex_task("what is the weather today")
        print(f"AI response: {result}")
        print("✓ AI Services test passed")
    except Exception as e:
        print(f"✗ AI Services test failed: {str(e)}")

if __name__ == "__main__":
    test_assistant()