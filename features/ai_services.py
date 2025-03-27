import os
import logging
import google.generativeai as genai
from PIL import Image
import requests
from dotenv import load_dotenv
import time
from quick_actions import QuickActions
from search_control import SearchControl
from browser_control import BrowserControl
from spotify_control import SpotifyControl
from camera_control import CameraControl
from datetime import datetime
import re

# Load environment variables
load_dotenv()

# Configure logging to suppress GRPC warnings
logging.getLogger('absl').setLevel(logging.ERROR)
os.environ['GRPC_PYTHON_LOG_LEVEL'] = 'error'

class AIServices:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIServices, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            try:
                print("Initializing core services...")
                self._should_stop = False
                
                # Assistant identity
                self.name = "Vani"
                self.personality = {
                    "name": "Vani",
                    "traits": ["helpful", "friendly", "efficient"],
                    "introduction": "Hi, I'm Vani, your AI assistant!"
                }
                
                # Initialize services
                genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
                self.quick = QuickActions()
                self.search = SearchControl()
                self.browser = BrowserControl()
                
                # Configure models
                self.gemini = genai.GenerativeModel('gemini-1.5-flash')
                self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Configure generation settings
                self.generation_config = {
                    "temperature": 0.9,
                    "top_k": 40,
                    "top_p": 0.95,
                    "max_output_tokens": 1024,
                    "candidate_count": 1,
                    "stop_sequences": ["."]
                }
                
                # Initialize caches and services
                self.prompt_cache = {}
                self.spotify = SpotifyControl()
                self.camera = CameraControl()
                self.flight_details = {}
                
                # Mark initialization complete
                self._initialized = True
                print(f"{self.name} initialized!")
            except Exception as e:
                print(f"Error initializing {self.name}: {str(e)}")
                raise

    def create_subtasks(self, main_task):
        """Break down main task into subtasks using Gemini"""
        try:
            prompt = f"""Break down this task into 3-5 clear, actionable subtasks:
            Task: {main_task}
            
            Format each subtask as:
            1. [subtask 1]
            2. [subtask 2]
            etc.
            
            Keep subtasks concise and specific."""
            
            response = self.gemini.generate_content(
                prompt,
                    generation_config=self.generation_config
                )
            
            if response and hasattr(response, 'text'):
                return response.text.strip()
            return "Could not break down the task."
            
        except Exception as e:
            print(f"Error creating subtasks: {str(e)}")
            return "Error breaking down task into subtasks."

    def analyze_subtask(self, subtask):
        """Analyze subtask complexity using Ollama"""
        try:
            payload = {
                "model": "mistral",
                "prompt": f"""Analyze this subtask and provide:
                1. Estimated time to complete
                2. Complexity level (Easy/Medium/Hard)
                3. Key requirements
                
                Subtask: {subtask}
                
                Keep the response brief and structured.""",
                "stream": False
            }
            
            response = requests.post(self.ollama_url, json=payload)
            if response.status_code == 200:
                return response.json()['response']
            return "Could not analyze subtask."
            
        except Exception as e:
            print(f"Error analyzing subtask: {str(e)}")
            return "Error analyzing subtask complexity."

    def get_subtask_suggestions(self, subtask):
        """Get suggestions for completing subtask using Gemini"""
        try:
            prompt = f"""Provide 2-3 practical suggestions for completing this subtask:
            Subtask: {subtask}
            
            Format as bullet points and keep suggestions specific and actionable."""
            
            response = self.gemini.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            if response and hasattr(response, 'text'):
                return response.text.strip()
            return "Could not generate suggestions."
            
        except Exception as e:
            print(f"Error getting suggestions: {str(e)}")
            return "Error generating subtask suggestions."

    def analyze_image(self, image_path, prompt):
        """Analyze image using Gemini Vision"""
        try:
            # Load image
            image = Image.open(image_path)
            
            # Generate response with Gemini Vision
            response = self.vision_model.generate_content([
                prompt,
                image
            ])
            
            # Clean up temporary image file
            try:
                os.remove(image_path)
                print(f"Deleted temporary image: {image_path}")
            except:
                pass
            
            return response.text
            
        except Exception as e:
            print(f"Image analysis error: {e}")
            return "I had trouble analyzing that image."

    def query_gemini(self, prompt, timeout=5):
        """Query Gemini with caching"""
        try:
            # Check cache first
            cache_key = prompt.lower().strip()
            if cache_key in self.prompt_cache:
                return self.prompt_cache[cache_key]
            
            # Generate new response
            response = self.gemini.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            if response and hasattr(response, 'text'):
                # Cache the response
                self.prompt_cache[cache_key] = response.text
                # Limit cache size
                if len(self.prompt_cache) > 100:
                    self.prompt_cache.pop(next(iter(self.prompt_cache)))
            return response.text
            
            return "Could not generate response"
            
        except Exception as e:
            print(f"Query error: {str(e)}")
            return f"Error generating response: {str(e)}"

    def handle_complex_task(self, task):
        """Handle multi-step tasks"""
        try:
            print(f"Processing complex task: {task}")
            task = task.lower()

            # Browser Search Command
            if "search on browser" in task or "search in browser" in task:
                # Extract search query
                query = task.split("browser")[-1].strip()
                print(f"Searching in browser: '{query}'")
                
                # Open Chrome and wait for it to load
                self.quick.open_application("chrome")
                time.sleep(2)
                
                # Open new tab
                self.quick.press_keys_combination('ctrl', 't')
                time.sleep(0.5)
                
                # Type query and search
                self.quick.simulate_typing(query)
                time.sleep(0.2)
                self.quick.press_key('enter')
                
                # Generate brief explanation
                prompt = f"""Give a brief explanation (50-100 words) of:
                {query}
                
                Focus on core concepts and key points only."""
                
                explanation = self.query_gemini(prompt)
                return f"Searched for '{query}' in browser\n\nBrief Overview:\n{explanation}"

            # 1. Open and Type Commands
            if "open" in task and "type" in task:
                full_command = task
                app_part = full_command[full_command.find("open")+4:full_command.find("and type")].strip()
                text_part = full_command[full_command.find("type")+4:].strip()
                
                self.quick.open_application(app_part)
                time.sleep(2)
                self.quick.simulate_typing(text_part)
                return f"Opened {app_part} and typed: {text_part}"

            # 2. Search Commands
            elif "search for" in task or "google" in task:
                query = task.split("for")[-1].strip() if "search for" in task else task.split("google")[-1].strip()
                self.search.perform_search(query, "google")
                return f"Searched for: {query}"

            # 3. Voice Control
            elif "change voice" in task and "say" in task:
                voice_type = "hinglish" if "hinglish" in task else "english"
                text_to_say = task.split("say")[-1].strip()
                self.tts_service.change_voice(voice_type)
                self.tts_service.speak(text_to_say)
                return f"Changed voice to {voice_type} and speaking"

            # 4. System Controls
            elif any(x in task for x in ["volume", "screenshot"]):
                if "volume" in task:
                    action = "increase" if "increase" in task else "decrease"
                    self.system.adjust_volume(action)
                    if "play" in task:
                        song = task.split("play")[-1].strip()
                        self.spotify.play_music(song)
                    return f"{action}d volume and playing music"
                else:
                    filepath = self.system.take_screenshot()
                    return "Screenshot taken and saved"

            # 5. File Operations
            elif "files" in task:
                if "find" in task or "search" in task:
                    query = task.split("find")[-1].strip() if "find" in task else task.split("search")[-1].strip()
                    self.files.search_in_explorer(query)
                    return f"Searching for files: {query}"

            # 6. Camera Commands
            elif any(x in task for x in ["picture", "photo", "capture"]):
                image_path = self.camera.capture_image()
                if "analyze" in task or "describe" in task:
                    analysis = self.analyze_image(image_path)
                    return f"Captured and analyzed image: {analysis}"
                return "Picture taken and saved"

            # 7. Browser Actions
            elif "browser" in task or any(x in task for x in ["chrome", "firefox"]):
                browser_name = "chrome" if "chrome" in task else "firefox"
                self.quick.open_application(browser_name)
                if "go to" in task:
                    url = task.split("go to")[-1].strip()
                    self.browser.navigate_to(url)
                    return f"Opened {browser_name} and navigated to {url}"

            # 8. Music Controls
            elif any(x in task for x in ["play", "music", "spotify"]):
                if "spotify" in task:
                    self.quick.open_application("spotify")
                    time.sleep(2)
                if "play" in task:
                    song = task.split("play")[-1].strip()
                    self.spotify.play_music(song)
                if "volume" in task:
                    action = "increase" if "increase" in task else "decrease"
                    self.system.adjust_volume(action)
                return "Music command executed"

            # Default: Break into subtasks
            else:
                subtasks = self.create_subtasks(task)
                if not subtasks:
                    return "Could not break down the task"
                
                results = []
                for subtask in subtasks.split('\n'):
                    if not subtask.strip():
                        continue
                    subtask = subtask.split('.', 1)[-1].strip()
                    response = self.query_gemini(subtask)
                    results.append(response)
                
                return "\n".join(results)
            
        except Exception as e:
            print(f"Error handling complex task: {e}")
            return f"Error executing the task: {str(e)}" 

    def handle_research_task(self, topic):
        """Handle research requests and type into Word"""
        try:
            print(f"\n📚 Researching: {topic}")
            
            # Get detailed research content from Gemini
            prompt = f"""Provide a comprehensive research report on: {topic}

            Please structure the report as follows:

            1. Title
            2. Executive Summary (2-3 paragraphs)
            3. Introduction (2-3 paragraphs)
            4. Key Findings
               - Major trends
               - Current developments
               - Statistical data
               - Expert opinions
            5. Detailed Analysis (3-4 sections)
               - Current state
               - Future implications
               - Challenges and opportunities
               - Industry impact
            6. Recommendations
            7. Conclusion

            Make it detailed and informative with around 1000-1500 words.
            Include relevant statistics and expert insights where applicable.
            """
            
            # Set longer timeout for detailed research
            response = self.query_gemini(prompt, timeout=30)
            
            if not response:
                return "Could not generate research content"
            
            # Open Microsoft Word and prepare document
            print("Opening Microsoft Word...")
            self.quick.open_application("word")
            time.sleep(2)
            
            # Create new document
            print("Creating new document...")
            self.quick.press_keys_combination('ctrl', 'n')
            time.sleep(0.5)
            
            # Type content with status updates
            print("Typing research content...")
            current_time = time.strftime("%Y-%m-%d %H:%M")
            header = f"Research Report\nTopic: {topic}\nDate: {current_time}\n\n"
            
            self.quick.simulate_typing(header, delay=0.02)
            time.sleep(0.3)
            
            # Type main content in chunks for better reliability
            chunks = response.split('\n\n')
            for chunk in chunks:
                self.quick.simulate_typing(chunk + '\n\n', delay=0.01)
                time.sleep(0.2)
            
            print("✅ Detailed research completed and typed!")
            return f"Completed comprehensive research on '{topic}'"
            
        except Exception as e:
            print(f"Research error: {e}")
            return f"Error during research: {str(e)}"

    def stop(self):
        """Stop current operation"""
        self._should_stop = True 

    def handle_price_comparison(self, product):
        """Handle price comparison requests"""
        try:
            # Clean up the product query
            product = product.replace("compare prices of", "").replace("compare price of", "").strip()
            print(f"\n💰 Starting price comparison for: {product}")
            
            # Open browser if not already open
            if not hasattr(self.browser, 'driver') or not self.browser.driver:
                self.browser.initialize_driver()
                time.sleep(1)
            
            # Search on major retailers
            prices = {}
            
            # Amazon
            try:
                print("Checking Amazon...")
                self.browser.search_site("amazon", product)
                time.sleep(1.5)
                prices["Amazon"] = self.browser.extract_price()
            except Exception as e:
                print(f"Error searching amazon: {e}")
            
            # Best Buy
            try:
                print("Checking Best Buy...")
                self.browser.search_site("bestbuy", product)
                time.sleep(1.5)
                prices["Best Buy"] = self.browser.extract_price()
            except Exception as e:
                print(f"Error searching bestbuy: {e}")
            
            # Walmart
            try:
                print("Checking Walmart...")
                self.browser.search_site("walmart", product)
                time.sleep(1.5)
                prices["Walmart"] = self.browser.extract_price()
            except Exception as e:
                print(f"Error searching walmart: {e}")
            
            # Format results
            if prices:
                # Open Word and create new document
                print("Opening Microsoft Word...")
                self.quick.open_application("word")
                time.sleep(1)
                
                self.quick.press_keys_combination('ctrl', 'n')
                time.sleep(0.5)
                
                # Create content for Word
                header = f"""Price Comparison Report
Product: {product}
Date: {time.strftime('%Y-%m-%d %H:%M')}

Current Prices:
--------------"""
                
                self.quick.simulate_typing(header + "\n\n", delay=0.01)
                
                # Add prices
                for store, price in prices.items():
                    if price:
                        self.quick.simulate_typing(f"{store}: {price}\n", delay=0.01)
                
                # Find best deal
                valid_prices = {k: v for k, v in prices.items() if v and isinstance(v, str)}
                if valid_prices:
                    try:
                        best_deal = min(valid_prices.items(), 
                                      key=lambda x: float(x[1].replace('$', '').replace(',', '')))
                        self.quick.simulate_typing(f"\nBest Deal: {best_deal[0]} at {best_deal[1]}", delay=0.01)
                    except Exception as e:
                        print(f"Error finding best deal: {e}")
                
                return f"\nCompleted price comparison for {product}. Results have been typed into Word."
            else:
                return f"Could not find prices for {product}. Please try a more specific search."
            
        except Exception as e:
            print(f"Price comparison error: {e}")
            return f"Error comparing prices: {str(e)}"

    def modify_skyscanner_url(self, departure, arrival, dep_date, ret_date=None, 
                            adults=1, children=0, cabin="economy", round_trip=0):
        """Generate Skyscanner URL with search parameters"""
        base_url = "https://www.skyscanner.ca/transport/flights/"
        
        # Format dates (assuming input is DD/MM/YYYY)
        dep_date = datetime.strptime(dep_date, '%d/%m/%Y').strftime('%y%m%d')
        if ret_date:
            ret_date = datetime.strptime(ret_date, '%d/%m/%Y').strftime('%y%m%d')
        else:
            ret_date = dep_date
            
        return f"{base_url}{departure}/{arrival}/{dep_date}/{ret_date}/?adultsv2={adults}&cabinclass={cabin}&childrenv2={children}&inboundaltsenabled=false&outboundaltsenabled=false&preferdirects=false&ref=home&rtn={round_trip}"

    def handle_flight_comparison(self, text: str) -> str:
        """Interactive flight search handler"""
        try:
            # Base Skyscanner URL
            base_url = "https://www.skyscanner.ca/transport/flights/"
            
            # Extract initial info from query
            self.flight_details = {}
            
            # Get departure and arrival
            if 'from' in text and 'to' in text:
                from_idx = text.index('from') + 4
                to_idx = text.index('to')
                self.flight_details['departure'] = text[from_idx:to_idx].strip()
                self.flight_details['arrival'] = text[to_idx + 2:].strip().split()[0]
                
                # Start building URL with departure and arrival
                partial_url = f"{base_url}{self.flight_details['departure']}/{self.flight_details['arrival']}/"
                print(f"\n🔄 Initial URL: {partial_url}")
                return "What's your departure date? (DD/MM/YYYY)"
            
            # Process date and build URL progressively
            if 'departure' in self.flight_details and 'arrival' in self.flight_details:
                if 'dep_date' not in self.flight_details:
                    # Format date for URL (YYMMDD)
                    formatted_date = datetime.strptime(text, '%d/%m/%Y').strftime('%y%m%d')
                    self.flight_details['dep_date'] = formatted_date
                    partial_url = f"{base_url}{self.flight_details['departure']}/{self.flight_details['arrival']}/{formatted_date}/"
                    print(f"\n🔄 URL with departure date: {partial_url}")
                    return "Is this a round trip? (yes/no)"
                
                if 'round_trip' not in self.flight_details:
                    self.flight_details['round_trip'] = text.lower() == 'yes'
                    if self.flight_details['round_trip']:
                        return "What's your return date? (DD/MM/YYYY)"
                    else:
                        # No return date, use same date
                        partial_url = f"{base_url}{self.flight_details['departure']}/{self.flight_details['arrival']}/{self.flight_details['dep_date']}/{self.flight_details['dep_date']}"
                        print(f"\n🔄 URL with one-way: {partial_url}")
                        return "What cabin class would you prefer? (economy/business/first)"
                
                if self.flight_details['round_trip'] and 'ret_date' not in self.flight_details:
                    formatted_date = datetime.strptime(text, '%d/%m/%Y').strftime('%y%m%d')
                    self.flight_details['ret_date'] = formatted_date
                    partial_url = f"{base_url}{self.flight_details['departure']}/{self.flight_details['arrival']}/{self.flight_details['dep_date']}/{formatted_date}"
                    print(f"\n🔄 URL with return date: {partial_url}")
                    return "What cabin class would you prefer? (economy/business/first)"
                
                # Continue building URL with remaining details...
                # Final URL will look like:
                # base_url/departure/arrival/depdate/retdate/?adultsv2=1&cabinclass=economy&childrenv2=0&rtn=1
                
                # Once all details are collected, open the final URL
                final_url = self.modify_skyscanner_url(
                    departure=self.flight_details['departure'],
                    arrival=self.flight_details['arrival'],
                    dep_date=self.flight_details['dep_date'],
                    ret_date=self.flight_details.get('ret_date', self.flight_details['dep_date']),
                    adults=self.flight_details.get('adults', 1),
                    children=self.flight_details.get('children', 0),
                    cabin=self.flight_details.get('cabin', 'economy'),
                    round_trip=1 if self.flight_details.get('round_trip') else 0
                )
                
                print(f"\n✈️ Final Skyscanner URL: {final_url}")
                self.browser.ensure_browser()
                self.browser.driver.get(final_url)
                return "Opening Skyscanner with your flight search..."
            
            return "Which city are you departing from?"
            
        except Exception as e:
            print(f"Flight search error: {e}")
            return "Error processing flight search"

    def process_flight_response(self, text: str) -> str:
        """Process user responses for flight search"""
        try:
            text = text.lower().strip()
            
            # Handle date inputs
            if re.match(r'\d{2}/\d{2}/\d{4}', text):
                if 'dep_date' not in self.flight_details:
                    self.flight_details['dep_date'] = text
                    return "Is this a round trip? (yes/no)"
                else:
                    self.flight_details['ret_date'] = text
                    return "What cabin class would you prefer? (economy/business/first)"
            
            # Handle yes/no for round trip
            if text in ['yes', 'no']:
                self.flight_details['round_trip'] = text == 'yes'
                if text == 'yes':
                    return "What's your return date? (DD/MM/YYYY)"
                return "What cabin class would you prefer? (economy/business/first)"
            
            # Handle cabin class
            if text in ['economy', 'business', 'first']:
                self.flight_details['cabin'] = text
                return "How many adults are traveling?"
            
            # Handle numeric responses
            if text.isdigit():
                if 'adults' not in self.flight_details:
                    self.flight_details['adults'] = int(text)
                    return "How many children are traveling?"
                else:
                    self.flight_details['children'] = int(text)
                    # All details collected, proceed with search
                    return self.handle_flight_comparison("")
            
            # Handle city inputs
            if 'departure' not in self.flight_details:
                self.flight_details['departure'] = text
                return "Which city are you traveling to?"
            elif 'arrival' not in self.flight_details:
                self.flight_details['arrival'] = text
                return "What's your departure date? (DD/MM/YYYY)"
            
            return "I didn't understand that. Please try again."
            
        except Exception as e:
            print(f"Response processing error: {e}")
            return "Error processing your response"

    def handle_spotify_command(self, command):
        """Handle Spotify commands"""
        try:
            if "play" in command:
                query = command.replace("play", "").strip()
                return self.spotify.play_music(query)
            elif "pause" in command:
                return self.spotify.pause_music()
            elif "next" in command:
                return self.spotify.next_track()
            elif "previous" in command:
                return self.spotify.previous_track()
            
        except Exception as e:
            print(f"Spotify command error: {e}")
            return "Error handling Spotify command"

    def handle_camera_command(self, command):
        """Handle camera commands"""
        try:
            if "take photo" in command or "take picture" in command:
                return self.camera.take_photo()
            elif "start recording" in command:
                return self.camera.start_recording()
            elif "stop recording" in command:
                return self.camera.stop_recording()
            
        except Exception as e:
            print(f"Camera command error: {e}")
            return "Error handling camera command"

    def handle_stock_prices(self, stock=None):
        """Handle stock price queries using Alpha Vantage API"""
        try:
            print("\n📈 Checking stock market...")
            API_KEY = "5Z506N2UCG373JIA"
            
            # Determine which stocks to check
            if stock:
                symbols = [stock]  # Check specific stock
            else:
                # Check major stocks
                symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
            
            # Open Word for report
            try:
                print("Opening Microsoft Word...")
                self.quick.open_application("word")
                time.sleep(1)
                
                self.quick.press_keys_combination('ctrl', 'n')
                time.sleep(0.5)
                
                # Create header
                header = f"""Stock Price Report
Date: {time.strftime('%Y-%m-%d %H:%M')}

Current Market Prices:
--------------------"""
                
                self.quick.simulate_typing(header + "\n\n", delay=0.005)
                
                # Fetch prices
                for symbol in symbols:
                    try:
                        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
                        response = requests.get(url)
                        data = response.json()
                        
                        if "Global Quote" in data and "05. price" in data["Global Quote"]:
                            price = data["Global Quote"]["05. price"]
                            change = data["Global Quote"]["09. change"]
                            percent = data["Global Quote"]["10. change percent"]
                            
                            stock_info = f"{symbol}: ${float(price):.2f} "
                            if float(change) > 0:
                                stock_info += f"↑ +{float(change):.2f} ({percent})"
                            else:
                                stock_info += f"↓ {float(change):.2f} ({percent})"
                                
                            self.quick.simulate_typing(stock_info + "\n", delay=0.005)
                            time.sleep(0.5)  # API rate limit
                            
                    except Exception as e:
                        print(f"Error fetching {symbol}: {e}")
                        self.quick.simulate_typing(f"Error fetching {symbol}: Price data unavailable\n", delay=0.005)
                        continue
                
                return "Stock prices have been written to Word document"
                
            except Exception as e:
                print(f"Error with Word document: {e}")
                return "Error writing to Word document. Displaying in console instead."
            
        except Exception as e:
            print(f"Stock price error: {e}")
            return f"Error getting stock prices: {str(e)}"

    def cleanup(self):
        """Clean up resources properly"""
        try:
            # Clean up Spotify
            if hasattr(self, 'spotify'):
                self.spotify.cleanup()
                
            # Other cleanup code...
            
        except Exception as e:
            print(f"Cleanup warning: {e}") 