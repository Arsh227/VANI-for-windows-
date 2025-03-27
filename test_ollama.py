import time
import os
import sys

def test_ollama():
    """Test Ollama integration"""
    print("\n=== Ollama Integration Test ===\n")
    
    try:
        from features.voice_recognition import speak
        from features.ollama_integration import ask_ollama
        
        # Test basic query
        print("Testing basic query...")
        response = ask_ollama("What time is it?")
        print(f"Response: {response}")
        print("✓ Basic query test passed")
        
    except ImportError as e:
        print(f"✗ Import failed: {str(e)}")
        print("Make sure all required modules are installed and in the correct location")
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")

def test_voice_integration():
    """Test voice with Ollama"""
    print("\nTesting voice + Ollama integration...")
    
    try:
        from features.voice_recognition import speak
        from features.ollama_integration import ask_ollama
        
        # Test voice response
        question = "What's the weather like?"
        print(f"\nAsking: {question}")
        response = ask_ollama(question)
        print(f"Response: {response}")
        speak(response)
        print("✓ Voice integration test passed")
        
    except Exception as e:
        print(f"✗ Integration test failed: {str(e)}")

if __name__ == "__main__":
    print("Starting Ollama tests...")
    print("Make sure Ollama is running locally!")
    
    while True:
        print("\nTest Options:")
        print("1. Test Ollama only")
        print("2. Test Ollama + Voice")
        print("3. Run all tests")
        print("0. Exit")
        
        choice = input("\nEnter choice (0-3): ")
        
        if choice == "1":
            test_ollama()
        elif choice == "2":
            test_voice_integration()
        elif choice == "3":
            test_ollama()
            time.sleep(2)
            test_voice_integration()
        elif choice == "0":
            break
        else:
            print("Invalid choice!")