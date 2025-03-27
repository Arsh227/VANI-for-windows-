from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import psutil
import os
import logging
from datetime import datetime, timedelta
import pyautogui
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import re

class BrowserControl:
    def __init__(self):
        self.driver = None
        self.options = Options()
        self.options.add_argument('--headless')  # Run in background
        self.options.add_argument('--log-level=3')  # Minimize logging
        self.urls = {
            'youtube': {
                'base_url': 'https://www.youtube.com',
                'search_url': 'https://www.youtube.com/results?search_query='
            },
            'google': {
                'base_url': 'https://www.google.com',
                'search_url': 'https://www.google.com/search?q='
            }
        }
        self.shopping_sites = {
            'amazon': 'https://www.amazon.com/s?k=',
            'bestbuy': 'https://www.bestbuy.com/site/searchpage.jsp?st=',
            'walmart': 'https://www.walmart.com/search?q='
        }
        self.active_sites = set()
        self.flight_sites = {
            'google_flights': 'https://www.google.com/travel/flights/search?tfs=CBwQAhokagcIARIDREVMEgoyMDI0LTAyLTI0cgcIARIDRFhCGgJERcABAggB'
        }
        self.flight_details = {}
        print("Browser control initialized!")

    def initialize_driver(self):
        """Initialize Chrome driver if not already running"""
        try:
            if not self.driver:
                self.driver = webdriver.Chrome(options=self.options)
            return True
        except Exception as e:
            print(f"Browser initialization error: {e}")
            return False

    def ensure_browser(self):
        """Ensure browser is running"""
        try:
            # Check if Chrome is already running
            chrome_running = False
            for proc in psutil.process_iter(['name']):
                if 'chrome.exe' in proc.info['name'].lower():
                    chrome_running = True
                    break
            
            # Only open if not running
            if not chrome_running:
                os.startfile('chrome')
                time.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"Browser error: {str(e)}")
            return False

    def search_and_play_youtube(self, query):
        """Search YouTube and play first video"""
        try:
            if not self.ensure_browser():
                return "Failed to start browser"
            
            print(f"Searching YouTube for: {query}")
            search_url = f"{self.urls['youtube']['search_url']}{query.replace(' ', '+')}"
            self.driver.get(search_url)
            
            try:
                wait = WebDriverWait(self.driver, 10)
                first_video = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "ytd-video-renderer #video-title")
                ))
                
                first_video.click()
                print("Video started playing")
                return f"Playing '{query}' on YouTube"
            except TimeoutException:
                print("Could not find video results")
                return "Could not find video results. Please try again."
        except Exception as e:
            print(f"YouTube playback error: {str(e)}")
            return f"Error playing video: {str(e)}"

    def search_site(self, site, query):
        """Search on specific website"""
        try:
            if not self.driver:
                self.initialize_driver()

            if site == "google":
                # Go directly to Google Finance
                self.driver.get("https://www.google.com/finance/markets/indexes")
                time.sleep(2)
                
                # Wait for page to load
                try:
                    # Try to find major indices directly
                    indices = {
                        "S&P 500": "//div[contains(text(), 'S&P 500')]",
                        "Dow Jones": "//div[contains(text(), 'Dow Jones')]",
                        "NASDAQ": "//div[contains(text(), 'NASDAQ')]"
                    }
                    
                    # Wait for at least one index to be visible
                    for xpath in indices.values():
                        try:
                            self.driver.find_element("xpath", xpath)
                            break
                        except:
                            continue
                    
                except Exception as e:
                    print(f"Error finding indices: {e}")
                    
            elif site == "amazon":
                self.driver.get(f"https://www.amazon.com/s?k={query}")
            elif site == "bestbuy":
                self.driver.get(f"https://www.bestbuy.com/site/searchpage.jsp?st={query}")
            elif site == "walmart":
                self.driver.get(f"https://www.walmart.com/search?q={query}")
                
            time.sleep(2)
            return True
            
        except Exception as e:
            print(f"Search error: {e}")
            return False

    def extract_price(self):
        """Extract price from current page"""
        try:
            time.sleep(3)
            current_url = self.driver.current_url.lower()
            store = None
            
            # Determine which store we're on
            for store_name in ["amazon", "bestbuy", "walmart"]:
                if store_name in current_url:
                    store = store_name
                    break
            
            if not store:
                return None

            # For Amazon, use direct extraction
            if store == "amazon":
                selectors = [
                    "//span[@class='a-price-whole']",
                    "//span[contains(@class, 'a-price')]//span[contains(@class, 'a-offscreen')]"
                ]
                
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements("xpath", selector)
                        for element in elements:
                            price_text = element.text or element.get_attribute("textContent")
                            if price_text:
                                matches = re.findall(r'\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?', price_text)
                                if matches:
                                    price = matches[0]
                                    if not price.startswith('$'):
                                        price = f"${price}"
                                    print(f"Found price for {store}: {price}")
                                    return price
                    except:
                        continue
                        
            # For Best Buy and Walmart, use Google search
            else:
                product_name = self.driver.title.split('-')[0].strip()
                search_query = f"{store} {product_name} price"
                
                # Switch to Google search
                self.driver.get(f"https://www.google.com/search?q={search_query}")
                time.sleep(2)
                
                # Try to find price in Google results
                price_patterns = [
                    "//div[contains(text(), '$')]",
                    "//span[contains(text(), '$')]",
                    "//*[contains(text(), '$') and contains(text(), '.')]"
                ]
                
                for pattern in price_patterns:
                    try:
                        elements = self.driver.find_elements("xpath", pattern)
                        for element in elements:
                            price_text = element.text
                            if price_text:
                                matches = re.findall(r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?', price_text)
                                if matches:
                                    print(f"Found price for {store}: {matches[0]}")
                                    return matches[0]
                    except:
                        continue
            
            print(f"No price found for {store}")
            return None
            
        except Exception as e:
            print(f"Price extraction error for {store}: {e}")
            return None

    def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
        except Exception as e:
            print(f"Browser cleanup error: {e}")

    def close_website(self, site_name):
        """Close specific website/tab"""
        try:
            if not self.driver:
                return "No browser windows open"
            
            site_name = site_name.lower()
            closed = False
            
            try:
                for handle in self.driver.window_handles:
                    try:
                        self.driver.switch_to.window(handle)
                        current_url = self.driver.current_url.lower()
                        
                        if site_name in current_url:
                            self.driver.close()
                            closed = True
                            if site_name in self.active_sites:
                                self.active_sites.remove(site_name)
                    except Exception as e:
                        print(f"Error with handle {handle}: {e}")
                        continue
                
                # Switch to first remaining tab if any
                if self.driver.window_handles:
                    self.driver.switch_to.window(self.driver.window_handles[0])
                
                return f"Closed {site_name}" if closed else "Could not find matching tab"
            except Exception as e:
                print(f"Browser error: {e}")
                self.cleanup()
                self.ensure_browser()
                return "Browser session expired, please try again"
        except Exception as e:
            print(f"Error closing website: {e}")
            return "Failed to close website"

    def close_all(self):
        """Close all browser windows"""
        try:
            print("Closing all browser windows...")
            if self.driver:
                # Close Chrome processes
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if proc.info['name'].lower() in ['chrome.exe', 'chromedriver.exe']:
                            proc.kill()
                    except:
                        continue
                
                self.driver.quit()
                self.driver = None
                self.active_sites.clear()
                print("All browser windows closed")
            return "Closed all browser windows"
        except Exception as e:
            print(f"Error closing browser: {e}")
            self.driver = None
            return f"Error closing browser: {str(e)}" 

    def stop_playback(self):
        """Stop any playing media"""
        try:
            if self.driver:
                self.driver.execute_script("""
                    var videos = document.getElementsByTagName('video');
                    var audios = document.getElementsByTagName('audio');
                    
                    for(var i = 0; i < videos.length; i++) {
                        videos[i].pause();
                    }
                    for(var i = 0; i < audios.length; i++) {
                        audios[i].pause();
                    }
                """)
            return "Stopped media playback"
        except:
            pass 

    def search_product(self, product):
        """Search product across shopping sites and get prices"""
        try:
            if not self.ensure_browser():
                return []
            
            prices = {
                'amazon': None,
                'bestbuy': None,
                'walmart': None
            }
            
            for site, base_url in self.shopping_sites.items():
                try:
                    search_url = f"{base_url}{product.replace(' ', '+')}"
                    self.driver.execute_script(f"window.open('{search_url}', '_blank');")
                    time.sleep(2)
                    
                    # Switch to new tab
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    
                    # Get price based on site
                    if site == 'amazon':
                        price_elem = self.driver.find_element('css selector', '.a-price-whole')
                        prices['amazon'] = price_elem.text if price_elem else "Not found"
                    elif site == 'bestbuy':
                        price_elem = self.driver.find_element('css selector', '.priceView-customer-price span')
                        prices['bestbuy'] = price_elem.text if price_elem else "Not found"
                    elif site == 'walmart':
                        price_elem = self.driver.find_element('css selector', '.price-main')
                        prices['walmart'] = price_elem.text if price_elem else "Not found"
                        
                except Exception as e:
                    print(f"Error searching {site}: {e}")
                    prices[site] = "Error retrieving price"
            
            return prices
            
        except Exception as e:
            print(f"Product search error: {e}")
            return {} 

    def search_flights(self, from_city, to_city):
        """Search flights using Google Flights"""
        try:
            if not self.ensure_browser():
                return {}
            
            # Format cities
            from_city = self.get_airport_code(from_city)
            to_city = self.get_airport_code(to_city)
            
            # Build Google Flights URL
            search_url = f"https://www.google.com/travel/flights?q=flights%20from%20{from_city}%20to%20{to_city}"
            
            # Open in new tab
            if not hasattr(self, 'driver') or not self.driver:
                self.initialize_driver()
            
            self.driver.get(search_url)
            time.sleep(2)  # Wait for prices to load
            
            try:
                # Get best flight price
                price_elem = self.driver.find_element(By.CSS_SELECTOR, 'div[aria-label*="price"]')
                best_price = price_elem.text if price_elem else "Not found"
                
                # Get flight details
                flight_elem = self.driver.find_element(By.CSS_SELECTOR, 'div[aria-label*="flight"]')
                flight_details = flight_elem.text if flight_elem else "Details not found"
                
                return {
                    'price': best_price,
                    'details': flight_details,
                    'url': search_url
                }
                
            except Exception as e:
                print(f"Error getting flight details: {e}")
                return {'price': "Not found", 'details': "Error retrieving details", 'url': search_url}
            
        except Exception as e:
            print(f"Flight search error: {e}")
            return {}

    def get_airport_code(self, city):
        """Convert city name to airport code"""
        # Add common airport codes
        codes = {
            'delhi': 'DEL',
            'dubai': 'DXB',
            'toronto': 'YTO',
            'new york': 'NYC',
            'london': 'LON',
            'paris': 'PAR'
        }
        return codes.get(city.lower(), city.upper())

    def search_youtube(self, query):
        """Search YouTube for a query"""
        try:
            print(f"\n🔍 Searching YouTube for: {query}")
            
            # Format search URL
            search_query = query.replace(' ', '+')
            youtube_search_url = f"https://www.youtube.com/results?search_query={search_query}"
            
            # Open Chrome if needed
            self.ensure_browser()
            time.sleep(1)
            
            # Open new tab
            pyautogui.hotkey('ctrl', 't')
            time.sleep(0.5)
            
            # Go to search URL
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.5)
            pyautogui.write(youtube_search_url)
            pyautogui.press('enter')
            time.sleep(2)
            
            return f"Searched YouTube for '{query}'"
            
        except Exception as e:
            print(f"❌ YouTube search error: {e}")
            return f"Error searching YouTube: {str(e)}"

    def search_google(self, query):
        """Search Google for a query"""
        try:
            print(f"\n🔍 Searching Google for: {query}")
            
            # Format search URL
            search_query = query.replace(' ', '+')
            google_search_url = f"https://www.google.com/search?q={search_query}"
            
            # Open Chrome if needed
            self.ensure_browser()
            time.sleep(1)
            
            # Open new tab
            pyautogui.hotkey('ctrl', 't')
            time.sleep(0.5)
            
            # Go to search URL
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.5)
            pyautogui.write(google_search_url)
            pyautogui.press('enter')
            time.sleep(2)
            
            return f"Searched Google for '{query}'"
            
        except Exception as e:
            print(f"❌ Google search error: {e}")
            return f"Error searching Google: {str(e)}"

    def open_browser(self):
        """Open Chrome browser"""
        try:
            os.startfile('chrome')
            time.sleep(2)  # Wait for browser to open
            return "Browser started successfully"
        except Exception as e:
            print(f"❌ Browser error: {e}")
            return "Error starting browser"

    def extract_stock_price(self, index_name):
        """Extract stock price from Google Finance"""
        try:
            # Wait for prices to load
            time.sleep(2)
            
            # Try different selectors for stock prices
            selectors = [
                f"//div[contains(text(), '{index_name}')]/following::span[contains(@class, 'price')]",
                f"//div[contains(text(), '{index_name}')]/following::span[1]",
                f"//span[contains(text(), '{index_name}')]/following::span[contains(@class, 'price')]",
                f"//span[contains(text(), '{index_name}')]/following::span[1]"
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element("xpath", selector)
                    if element and element.text:
                        return element.text.strip()
                except:
                    continue
            
            return "N/A"
            
        except Exception as e:
            print(f"Error extracting stock price: {e}")
            return "N/A"

    def handle_flight_search(self, text: str) -> str:
        """Interactive flight search with dynamic URL building"""
        try:
            print("\n✈️ Processing flight search request...")
            
            # Extract initial info if provided
            if 'from' in text.lower() and 'to' in text.lower():
                from_idx = text.lower().index('from') + 4
                to_idx = text.lower().index('to')
                self.flight_details['departure'] = text[from_idx:to_idx].strip()
                self.flight_details['arrival'] = text[to_idx + 2:].strip().split()[0]
                
                # Check for date info
                if 'next week' in text.lower():
                    self.flight_details['date_type'] = 'next_week'
                elif 'cheapest' in text.lower():
                    self.flight_details['date_type'] = 'cheapest'
                
                print(f"\n🔍 Found initial details:")
                print(f"From: {self.flight_details['departure']}")
                print(f"To: {self.flight_details['arrival']}")
                
                return "Would you like a one-way or round-trip ticket?"
            
            return "Where are you flying from? (city or airport code)"
            
        except Exception as e:
            print(f"Flight search error: {e}")
            return "Error processing flight search"

    def generate_skyscanner_url(self) -> str:
        """Generate Skyscanner URL based on collected details"""
        base_url = "https://www.skyscanner.ca/transport/flights/"
        
        # Handle date formatting
        if self.flight_details['date_type'] == 'cheapest':
            date_part = 'cheapest-day/'
        else:
            if 'next_week' in self.flight_details['date_type']:
                dep_date = (datetime.now() + timedelta(days=7)).strftime('%y%m%d')
            else:
                dep_date = datetime.strptime(self.flight_details['dep_date'], '%d/%m/%Y').strftime('%y%m%d')
            
            ret_date = dep_date
            if self.flight_details['trip_type'] == 'round-trip':
                ret_date = datetime.strptime(self.flight_details['return_date'], '%d/%m/%Y').strftime('%y%m%d')
            
            date_part = f"{dep_date}/{ret_date}/"
        
        # Build URL
        url = (f"{base_url}{self.flight_details['departure']}/{self.flight_details['arrival']}/"
               f"{date_part}?adultsv2={self.flight_details['adults']}"
               f"&cabinclass={self.flight_details['cabin_class']}"
               f"&childrenv2={self.flight_details.get('children', 0)}"
               f"&rtn={'1' if self.flight_details['trip_type'] == 'round-trip' else '0'}"
               f"&preferdirects={'true' if self.flight_details['direct_only'] else 'false'}")
        
        return url

    def process_flight_response(self, text: str) -> str:
        """Process user responses for flight search"""
        text = text.lower().strip()
        
        # Handle date inputs
        if re.match(r'\d{2}/\d{2}/\d{4}', text):
            if 'dep_date' not in self.flight_details:
                self.flight_details['dep_date'] = text
                if self.flight_details['trip_type'] == 'round-trip':
                    return "What's your return date?"
                return "What seat class do you prefer?"
            else:
                self.flight_details['return_date'] = text
                return "What seat class do you prefer?"
        
        # Handle trip type
        if text in ['one-way', 'round-trip']:
            self.flight_details['trip_type'] = text
            return "When would you like to fly? (specific date, next week, or cheapest within 7 days)"
        
        # Handle date type
        if 'next week' in text:
            self.flight_details['date_type'] = 'next_week'
            return "What seat class do you prefer?"
        elif 'cheapest' in text:
            self.flight_details['date_type'] = 'cheapest'
            return "What seat class do you prefer?"
        
        # Handle cabin class
        if text in ['economy', 'premiumeconomy', 'business', 'first']:
            self.flight_details['cabin_class'] = text
            return "How many adults are traveling?"
        
        # Handle numeric responses
        if text.isdigit():
            if 'adults' not in self.flight_details:
                self.flight_details['adults'] = int(text)
                return "How many children are traveling?"
            else:
                self.flight_details['children'] = int(text)
                return "Do you prefer only direct flights? (yes/no)"
        
        # Handle yes/no for direct flights
        if text in ['yes', 'no']:
            self.flight_details['direct_only'] = text == 'yes'
            return self.handle_flight_search("")
        
        return "I didn't understand that. Please try again." 