import time
from collections import deque
import json
import os

class ConversationManager:
    def __init__(self, ai_services):
        self.ai_services = ai_services
        # Context retention
        self.context = {
            'history': deque(maxlen=5),  # Last 5 interactions
            'current_topic': None,
            'user_preferences': {},
            'conversation_style': {
                'tone': 'friendly',
                'formality': 'casual',
                'engagement': 'high'
            }
        }
        
        # Intent patterns
        self.intents = {
            'music': ['play', 'pause', 'song', 'track', 'spotify'],
            'research': ['research', 'find', 'search', 'look up'],
            'camera': ['photo', 'picture', 'record', 'capture'],
            'price': ['price', 'cost', 'compare', 'cheaper'],
            'flight': ['flight', 'travel', 'trip', 'book'],
            'help': ['help', 'how to', 'what can', 'explain']
        }
        
        # Load conversation memory if exists
        self.memory_file = 'conversation_memory.json'
        self.load_memory()
        
        # Enhanced conversation patterns
        self.conversation_patterns = {
            'greetings': ['hi', 'hello', 'hey', 'good morning', 'good evening'],
            'farewells': ['bye', 'goodbye', 'see you', 'talk to you later'],
            'thanks': ['thank you', 'thanks', 'appreciate it'],
            'confirmations': ['yes', 'yeah', 'sure', 'okay', 'alright'],
            'negations': ['no', 'nope', 'not really', 'don\'t'],
            'clarifications': ['what do you mean', 'could you explain', 'i don\'t understand'],
            'preferences': ['i like', 'i prefer', 'i want', 'can you'],
            'follow_ups': ['and then', 'also', 'what about', 'how about'],
            'emotions': ['happy', 'sad', 'tired', 'excited', 'bored'],
            'casual_chat': ['how are you', 'what\'s up', 'how\'s it going'],
            'opinions': ['what do you think', 'do you like', 'is it good'],
            'personal': ['i feel', 'i think', 'i want to'],
            'jokes': ['tell me a joke', 'be funny', 'make me laugh'],
            'encouragement': ['can\'t do it', 'too hard', 'difficult']
        }
        
        # Response templates for natural conversation
        self.response_templates = {
            'greetings': [
                "Hey there! What's on your mind?",
                "Hi! What can I help you with today?",
                "Hey! What's up?"
            ],
            'farewells': [
                "Catch you later! Don't be a stranger!",
                "Take care! I'll be here when you need me!",
                "See ya! Come back anytime!"
            ],
            'thanks': [
                "No worries at all!",
                "Anytime! That's what I'm here for!",
                "You got it! Need anything else?"
            ],
            'music': [
                "Let's get some tunes going! {action}",
                "Good choice! {action}",
                "Coming right up! {action}"
            ],
            'research': [
                "I'm on it! Let me dig into that for you! {action}",
                "Let's find out more about that! {action}",
                "I'll check that out real quick! {action}"
            ],
            'camera': [
                "Say cheese! {action}",
                "Let's capture this moment! {action}",
                "Ready when you are! {action}"
            ],
            'emotions': {
                'happy': "That's great to hear! You're making me smile too!",
                'sad': "Hey, we all have those days. Wanna talk about it?",
                'tired': "Need a break? We could play some chill music!",
                'excited': "Your energy is contagious! Tell me more!",
                'bored': "Let's fix that! Want to try something fun?"
            },
            'casual_chat': [
                "Just hanging out, ready to help! What's new?",
                "All good here! What's on your mind?",
                "Ready to make your day easier! What do you need?"
            ],
            'encouragement': [
                "You've totally got this! Need a hand?",
                "Baby steps! What should we tackle first?",
                "Everyone starts somewhere! Let's figure this out together!"
            ]
        }

    def process_input(self, user_input):
        """Process user input with context awareness"""
        try:
            # Add to history
            self.context['history'].append({
                'user': user_input,
                'timestamp': time.time()
            })
            
            # Detect intent
            intent = self.detect_intent(user_input)
            
            # Handle specific intents
            if intent in ['search', 'research', 'price', 'flight']:
                return self.handle_intent(user_input, intent)
            
            # Generate contextual response
            response = self.generate_response(user_input, intent)
            
            # Update context
            self.update_context(user_input, intent, response)
            
            # Save memory periodically
            self.save_memory()
            
            return response
            
        except Exception as e:
            print(f"Conversation processing error: {e}")
            return self.get_fallback_response()

    def detect_intent(self, text):
        """Detect user intent from input"""
        text = text.lower()
        
        # Check against intent patterns
        for intent, patterns in self.intents.items():
            if any(pattern in text for pattern in patterns):
                return intent
                
        # Check context for ongoing conversation
        if self.context['current_topic']:
            return self.context['current_topic']
            
        return 'general'

    def generate_response(self, user_input, intent):
        """Generate more natural, engaging responses"""
        try:
            # Check emotional content first
            emotion = self.detect_emotion(user_input)
            if emotion:
                return self.respond_to_emotion(emotion)
            
            # Handle casual chat
            if any(p in user_input.lower() for p in self.conversation_patterns['casual_chat']):
                return self.get_random_response('casual_chat')
            
            # Check for basic conversation patterns first
            pattern = self.detect_conversation_pattern(user_input.lower())
            if pattern and pattern in self.response_templates:
                return self.get_random_response(pattern)
            
            # Handle follow-up questions
            if self.is_continuation():
                previous = self.get_last_interaction()
                
                # Handle clarifications
                if "what do you mean" in user_input.lower():
                    return self.generate_clarification(previous['topic'])
                
                # Handle preferences
                if any(p in user_input.lower() for p in self.conversation_patterns['preferences']):
                    return self.handle_preference(user_input, previous['topic'])
                
                # Handle follow-ups
                if any(p in user_input.lower() for p in self.conversation_patterns['follow_ups']):
                    return self.handle_follow_up(user_input, previous['topic'])
            
            # Get base response for main intents
            base_response = self.handle_intent(user_input, intent)
            
            # Make response more conversational
            if intent in self.response_templates:
                return self.get_random_response(intent).format(action=base_response)
            
            return base_response
            
        except Exception as e:
            print(f"Response generation error: {e}")
            return self.get_friendly_fallback()

    def handle_intent(self, user_input, intent):
        """Handle specific intents"""
        try:
            if intent == 'music':
                return self.ai_services.handle_spotify_command(user_input)
            elif intent == 'research':
                return self.ai_services.handle_research_task(user_input)
            elif intent == 'camera':
                return self.ai_services.handle_camera_command(user_input)
            elif intent == 'price':
                product = user_input.split('price')[-1].strip()
                return self.ai_services.handle_price_comparison(product)
            elif intent == 'help':
                return self.get_help_response()
            
            return self.ai_services.query_gemini(user_input)
            
        except Exception as e:
            print(f"Intent handling error: {e}")
            return self.get_fallback_response()

    def is_continuation(self):
        """Check if current input is continuation of conversation"""
        if not self.context['history']:
            return False
            
        last_interaction = self.get_last_interaction()
        if not last_interaction:
            return False
            
        # Check time gap (within 2 minutes)
        time_gap = time.time() - last_interaction['timestamp']
        return time_gap < 120

    def update_context(self, user_input, intent, response):
        """Update conversation context"""
        self.context['current_topic'] = intent
        
        # Update user preferences based on interaction
        if 'favorite' in user_input.lower():
            preference = user_input.split('favorite')[-1].strip()
            self.context['user_preferences'][intent] = preference

    def get_last_interaction(self):
        """Get last interaction from history"""
        return self.context['history'][-1] if self.context['history'] else None

    def get_fallback_response(self):
        """Get graceful fallback response"""
        fallbacks = [
            "I'm not quite sure about that. Could you rephrase it?",
            "I didn't catch that. Can you explain it differently?",
            "I'm still learning. Could you be more specific?",
            "I want to help, but I'm not sure what you're asking. Can you clarify?"
        ]
        return fallbacks[int(time.time()) % len(fallbacks)]

    def get_help_response(self):
        """Get help response based on context"""
        if self.context['current_topic']:
            return f"I can help you with {self.context['current_topic']}. What would you like to know?"
        return "I can help with music, research, photos, prices, and flights. What would you like to do?"

    def save_memory(self):
        """Save conversation memory"""
        try:
            memory = {
                'user_preferences': self.context['user_preferences'],
                'recent_topics': list(self.context['history'])
            }
            
            with open(self.memory_file, 'w') as f:
                json.dump(memory, f)
                
        except Exception as e:
            print(f"Memory save error: {e}")

    def load_memory(self):
        """Load conversation memory"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    memory = json.load(f)
                    self.context['user_preferences'] = memory.get('user_preferences', {})
                    
        except Exception as e:
            print(f"Memory load error: {e}") 

    def get_friendly_fallback(self):
        """Get engaging fallback responses"""
        fallbacks = [
            "I didn't quite catch that. Could you rephrase it?",
            "Hmm, I want to help but I'm not sure what you mean. Mind explaining it differently?",
            "I'm still learning! Could you help me understand what you're looking for?",
            "That's an interesting one! Could you break it down for me?"
        ]
        return fallbacks[int(time.time()) % len(fallbacks)] 

    def detect_conversation_pattern(self, text):
        """Detect conversation patterns in user input"""
        text = text.lower()
        
        for pattern_type, patterns in self.conversation_patterns.items():
            if any(p in text for p in patterns):
                return pattern_type
        return None

    def get_random_response(self, template_type):
        """Get random response from template"""
        import random
        templates = self.response_templates.get(template_type, [])
        return random.choice(templates) if templates else None

    def handle_preference(self, user_input, previous_topic):
        """Handle user preferences"""
        preference = user_input.lower()
        if "music" in previous_topic and "like" in preference:
            genre = preference.split("like")[-1].strip()
            self.context['user_preferences']['music'] = genre
            return f"I'll remember that you like {genre} music! Would you like me to play some?"
        return self.handle_intent(user_input, previous_topic)

    def handle_follow_up(self, user_input, previous_topic):
        """Handle follow-up questions"""
        if "and then" in user_input.lower():
            return f"Sure! After {previous_topic}, what would you like me to do?"
        elif "what about" in user_input.lower():
            new_query = user_input.split("what about")[-1].strip()
            return self.handle_intent(new_query, previous_topic)
        return self.handle_intent(user_input, previous_topic) 

    def detect_emotion(self, text):
        """Detect emotional content in user input"""
        text = text.lower()
        for emotion in self.response_templates['emotions']:
            if emotion in text:
                return emotion
        return None

    def respond_to_emotion(self, emotion):
        """Generate empathetic response to emotions"""
        return self.response_templates['emotions'].get(emotion, 
            "I hear you! Want to tell me more about how you're feeling? ") 