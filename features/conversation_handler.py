import google.generativeai as genai
import os
import time
from dotenv import load_dotenv
from conversation_manager import ConversationManager
from subprocess_handler import SubprocessHandler
from ai_services import AIServices
from command_handler import CommandHandler
import pyautogui
import PIL.Image
import keyboard

class ConversationHandler:
    def __init__(self, ai_services=None):
        try:
            # Load environment variables
            load_dotenv()
            
            # Initialize services first
            self.ai_services = ai_services or AIServices()
            
            # Initialize managers and handlers
            self.conversation_manager = ConversationManager(self.ai_services)
            self.subprocess_handler = SubprocessHandler(self.ai_services, self)
            self.command_handler = CommandHandler()
            
            # Set AI personality
            self.personality = """You are Vani, a friendly and helpful AI assistant.
            Be conversational and natural in responses.
            Keep answers concise but engaging.
            Remember context from our conversation."""
            
            # Try to initialize Gemini with retry
            self.initialize_gemini()
            
        except Exception as e:
            print(f"Error initializing conversation handler: {e}")
            # Continue without Gemini if it fails
            self.model = None
            self.chat = None

    def initialize_gemini(self, max_retries=3):
        """Initialize Gemini API with retry logic"""
        for attempt in range(max_retries):
            try:
                # Configure Gemini API for text
                genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
                self.model = genai.GenerativeModel('gemini-1.5-flash')  # For text tasks
                
                # Configure vision model with separate API key
                genai.configure(api_key=os.getenv('GEMINI_VISION_API_KEY'))
                self.vision_model = genai.GenerativeModel('gemini-1.5-flash')  # For vision tasks
                
                self.generation_config = {
                    'temperature': 0.9,
                    'top_p': 0.95,
                    'top_k': 40,
                    'max_output_tokens': 1024,
                    'stop_sequences': ["."]
                }
                
                # Initialize chat
                self.chat = self.model.start_chat(history=[])
                self.chat.send_message(self.personality)
                return True
                
            except Exception as e:
                print(f"Gemini initialization attempt {attempt + 1} failed: {e}")
                time.sleep(1)
                
        print("Failed to initialize Gemini after all retries")
        return False

    def process_user_input(self, text: str) -> str:
        """Process user input - both commands and conversation"""
        try:
            # Handle "what do you see" command first
            if "what do you see" in text.lower():
                print("\n📸 Taking a photo for analysis...")
                photo_result = self.ai_services.camera.take_photo()
                if isinstance(photo_result, tuple) and len(photo_result) == 2:
                    photo_path, _ = photo_result
                    if photo_path and os.path.exists(photo_path):
                        return self.analyze_image(photo_path)
                return "I couldn't take a photo to analyze."
            
            # Check for typing command first
            if text.lower().startswith('type '):
                content = text.replace('type', '', 1).strip()
                print("\n⌨️ Typing text...")
                return self.ai_services.quick.type_text(content)
            
            # Check for writing/essay commands
            if any(word in text.lower() for word in ["write me", "write an", "create", "make"]) and \
               any(word in text.lower() for word in ["assignment", "report", "essay"]):
                
                print("\n📝 Creating document...")
                
                # Extract topic
                topic = text.lower()
                for remove in ["write me", "write an", "create", "make", "an", "a", "assignment", "report", "essay", "on", "about"]:
                    topic = topic.replace(remove, "").strip()
                
                # Get content from Gemini
                prompt = f"""Write a comprehensive essay on {topic}. 
                Include:
                - Clear introduction
                - Well-structured body paragraphs
                - Supporting evidence and examples
                - Strong conclusion
                Make it detailed and engaging."""
                
                try:
                    # Get content first
                    print("Generating content...")
                    response = self.chat.send_message(prompt).text
                    
                    # Create and type in document
                    if self.create_word_document(topic, response):
                        return "Essay has been written in Word!"
                    return "Error creating essay"
                    
                except Exception as e:
                    print(f"Essay generation error: {e}")
                    return "Error creating essay"
            
            # Check for flight-related queries first
            if any(phrase in text.lower() for phrase in [
                "search flights", "book flight", "find flights", 
                "search for flights", "flight from", "flights from"
            ]):
                print("\n✈️ Starting flight search...")
                return self.ai_services.browser.handle_flight_search(text)
            
            # Check if command needs subprocess handling
            if text.startswith(('open', 'run', 'execute', 'launch')):
                return self.subprocess_handler.handle_process(text)
            
            # Regular command handling
            if text.startswith(('play', 'close', 'search', 'volume', 'what do you see')):
                return self.command_handler.execute_command(text)
            
            # Use conversation manager for context-aware responses
            response = self.conversation_manager.process_input(text)
            if response:
                from ollama_integration import speak
                speak(response)
                return response
            
            # Try Gemini if available
            if self.chat:
                try:
                    response = self.chat.send_message(
                        text,
                        generation_config=self.generation_config
                    ).text
                    return response
                except Exception as e:
                    print(f"Gemini error: {e}")
            
            # Fallback response
            return "I understand your request but I'm having trouble with some services right now."
            
        except Exception as e:
            print(f"Error processing input: {e}")
            return "I'm having trouble understanding that right now"

    def handle_conversation(self, text: str) -> str:
        """Handle normal conversation (non-command input)"""
        try:
            # Clean and normalize input
            text = text.strip()
            
            # Get response from Gemini
            response = self.chat.send_message(text)
            
            return response.text
            
        except Exception as e:
            print(f"Conversation error: {e}")
            return "I'm having trouble understanding that right now"

    def handle_command(self, text):
        """Handle specific commands"""
        try:
            # Research/Assignment/Report commands
            if any(word in text.lower() for word in ["write me", "write an", "create", "make"]) and \
               any(word in text.lower() for word in ["assignment", "report", "essay"]):
                
                print("\n📝 Creating document...")
                
                # Extract topic
                topic = text.lower()
                for remove in ["write me", "write an", "create", "make", "an", "a", "assignment", "report", "essay", "on", "about"]:
                    topic = topic.replace(remove, "").strip()
                
                # Better prompt for report generation
                prompt = f"""Generate a comprehensive academic report on {topic}."""
                
                try:
                    # Get content first - don't speak it
                    print("Generating content...")
                    response = self.chat.send_message(prompt).text
                    
                    # Open Word and create new document
                    print("Opening Microsoft Word...")
                    self.ai_services.quick.open_application('word')
                    time.sleep(3)
                    
                    # Create new document
                    pyautogui.hotkey('ctrl', 'n')
                    time.sleep(2)
                    
                    # Click in document to ensure focus
                    screen_width, screen_height = pyautogui.size()
                    pyautogui.click(screen_width//2, screen_height//2)
                    time.sleep(1)
                    
                    # Type the content without speaking
                    print("Writing content...")
                    return self.ai_services.quick.type_text(response)
                    
                except Exception as e:
                    print(f"Report generation error: {e}")
                    return "Error creating report"
            
            # Stock prices
            if any(phrase in text.lower() for phrase in ["stock price", "stock prices", "stock market", "stocks", "check stock"]):
                try:
                    stock_query = text.lower()
                    stock = None
                    
                    # Extract specific stock if mentioned
                    if "of" in stock_query:
                        stock_name = stock_query.split("of")[-1].strip()
                        stock_map = {
                            "apple": "AAPL",
                            "microsoft": "MSFT", 
                            "google": "GOOGL",
                            "amazon": "AMZN",
                            "tesla": "TSLA"
                        }
                        stock = stock_map.get(stock_name)
                    
                    print("\n📈 Checking stock market...")
                    return self.ai_services.handle_stock_prices(stock)
                except Exception as e:
                    print(f"Stock command error: {e}")
                    return "Error processing stock command"
                
            # Flight comparison
            elif "compare" in text and ("flights" in text or "flight" in text):
                print("\n✈️ Checking flights...")
                return self.ai_services.handle_flight_comparison(text)
                
            # Price comparison    
            elif "compare" in text and ("prices" in text or "price" in text):
                print("\n💰 Comparing prices...")
                return self.ai_services.handle_price_comparison(text)
                
            # Search commands
            elif "search" in text:
                if "youtube" in text:
                    query = text.replace("search", "").replace("youtube", "").replace("on", "").strip()
                    return self.ai_services.browser.search_youtube(query)
                else:
                    query = text.replace("search", "").replace("google", "").replace("on", "").strip()
                    return self.ai_services.browser.search_google(query)
                    
            elif "research" in text:
                topic = text.replace("research", "").strip()
                return self.ai_services.handle_research_task(topic)
                
            elif "type" in text:
                content = text.replace("type", "").strip()
                return self.ai_services.quick.type_text(content)
                
            # Handle typing commands
            if text.startswith('type '):
                content = text.replace('type', '', 1).strip()
                return self.ai_services.quick.type_text(content)
                
            return None  # Let other handlers process it
            
        except Exception as e:
            print(f"Command error: {e}")
            return f"Error processing command: {str(e)}"
            
    def get_response(self, user_input):
        """Get AI response with sentiment-aware context"""
        try:
            response = self.chat.send_message(
                user_input,
                generation_config=self.generation_config
            )
            return response.text
            
        except Exception as e:
            print(f" Response error: {str(e)}")
            return "I'm having trouble right now, could you try again?"

    def setup_initial_context(self):
        """Setup initial personality and context"""
        context = """You are Vani, a helpful and friendly AI assistant. Keep your responses:
        1. Brief but informative (2-3 sentences)
        2. Natural and conversational
        3. Direct and relevant
        4. Occasionally use emojis for warmth
        """
        
        try:
            self.chat.send_message(context, generation_config=self.generation_config)
        except Exception as e:
            print(f"Context setup error: {e}")

    def analyze_image(self, image_path):
        """Analyze image using Gemini Vision"""
        try:
            print("🔍 Analyzing image with Gemini...")
            
            # Load image
            image = PIL.Image.open(image_path)
            
            # Create a specific prompt for vision analysis
            prompt = """Describe what you see in this image in detail. Focus on:
            - Main subjects/objects
            - Colors and visual elements
            - Actions or activities
            - Notable details or context
            Keep the description natural and clear."""
            
            # Use gemini-1.5-flash-vision model specifically for vision tasks
            response = self.vision_model.generate_content(
                [prompt, image],
                generation_config={
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'top_k': 40,
                    'max_output_tokens': 1024,
                }
            )
            
            # Clean up the image file after analysis
            try:
                os.remove(image_path)
                print(f"Deleted temporary image: {image_path}")
            except:
                pass
            
            return f"""
👁️ Image Analysis:
------------------
{response.text}"""
            
        except Exception as e:
            print(f"Image analysis error: {e}")
            return "I had trouble analyzing that image. Please try again."

    def create_word_document(self, topic, content):
        """Create and type content in Word document"""
        try:
            print("Opening Microsoft Word...")
            # Use the quick actions to open Word
            self.ai_services.quick.open_application('winword')
            time.sleep(3)  # Wait for Word to fully load
            
            # Create new document using Ctrl+N
            print("Creating new document...")
            keyboard.press_and_release('ctrl+n')
            time.sleep(2)
            
            # Press Enter to ensure we're on a new line
            keyboard.press_and_release('enter')
            time.sleep(0.5)
            
            # Press Home key to ensure cursor is at start of line
            keyboard.press_and_release('home')
            time.sleep(0.5)
            
            # Type title
            print("Adding title...")
            title = f"Essay on {topic.title()}\n\n"
            self.ai_services.quick.type_text(title)
            time.sleep(1)
            
            # Type content in paragraphs
            print("Writing content...")
            paragraphs = content.split('\n\n')
            for paragraph in paragraphs:
                if paragraph.strip():
                    self.ai_services.quick.type_text(paragraph.strip() + '\n\n')
                    time.sleep(0.5)
            
            return True
            
        except Exception as e:
            print(f"Document creation error: {e}")
            return False 