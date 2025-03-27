import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import os
from dotenv import load_dotenv
import platform

class SpotifyControl:
    def __init__(self):
        load_dotenv()
        self.sp = None
        self.device_id = None
        self.setup_spotify()
        
    def setup_spotify(self):
        """Initialize Spotify client"""
        try:
            auth_manager = SpotifyOAuth(
                client_id=os.getenv('SPOTIFY_CLIENT_ID'),
                client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
                redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
                scope='user-modify-playback-state user-read-playback-state'
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            self.ensure_active_device()
        except Exception as e:
            print(f"Spotify setup error: {e}")
            
    def ensure_active_device(self):
        """Make sure there's an active Spotify device"""
        try:
            devices = self.sp.devices()
            if not devices['devices']:
                print("\n🎵 No active Spotify devices found. Opening Spotify...")
                # Launch Spotify app
                if platform.system() == 'Windows':
                    os.system('start spotify:')
                elif platform.system() == 'Darwin':  # macOS
                    os.system('open -a Spotify')
                elif platform.system() == 'Linux':
                    os.system('spotify')
                
                # Wait for device to become active
                time.sleep(5)
                devices = self.sp.devices()
            
            if devices['devices']:
                self.device_id = devices['devices'][0]['id']
                print(f"Using Spotify device: {devices['devices'][0]['name']}")
                return True
            else:
                print("Please open Spotify and ensure music is playing")
                return False
                
        except Exception as e:
            print(f"Device check error: {e}")
            return False
            
    def play_music(self, query: str) -> str:
        """Search and play music on Spotify with improved accuracy"""
        try:
            if not self.sp:
                return "Spotify not initialized"
            
            # Ensure active device before playing
            if not self.ensure_active_device():
                return "Please open Spotify and start playing music first"
            
            # Try exact match first
            results = self.sp.search(q=f'"{query}"', limit=5, type='track')
            
            # If no exact match, try with additional search terms
            if not results['tracks']['items']:
                # Try with song/track keyword
                results = self.sp.search(q=f'track:"{query}"', limit=5, type='track')
                
            if not results['tracks']['items']:
                # Try broader search
                results = self.sp.search(q=query, limit=5, type='track')
            
            if results['tracks']['items']:
                # Find best matching track
                best_match = None
                query_lower = query.lower()
                
                for track in results['tracks']['items']:
                    track_name = track['name'].lower()
                    if track_name == query_lower:
                        best_match = track
                        break
                    elif query_lower in track_name:
                        best_match = track
                        break
                
                if best_match:
                    track_uri = best_match['uri']
                    track_name = best_match['name']
                    artist_name = best_match['artists'][0]['name']
                    
                    # Try to play on specific device
                    try:
                        if self.device_id:
                            self.sp.start_playback(device_id=self.device_id, uris=[track_uri])
                        else:
                            self.sp.start_playback(uris=[track_uri])
                        return f"Playing '{track_name}' by {artist_name}"
                    except Exception as e:
                        print(f"Playback error: {e}")
                        return "Please make sure Spotify is open and playing"
                
            return f"Could not find '{query}' on Spotify"
            
        except Exception as e:
            print(f"Spotify playback error: {e}")
            return "Error playing music"

    def pause_music(self):
        """Pause current playback"""
        try:
            self.sp.pause_playback()
            return "Music paused"
        except Exception as e:
            print(f"Pause error: {e}")
            return "Error pausing music"

    def next_track(self):
        """Skip to next track"""
        try:
            self.sp.next_track()
            time.sleep(1)  # Wait for track change
            current = self.sp.current_playback()
            if current and current['item']:
                return f"Playing next track: {current['item']['name']}"
            return "Skipped to next track"
        except Exception as e:
            print(f"Next track error: {e}")
            return "Error skipping track"

    def previous_track(self):
        """Go back to previous track"""
        try:
            self.sp.previous_track()
            time.sleep(1)  # Wait for track change
            current = self.sp.current_playback()
            if current and current['item']:
                return f"Playing previous track: {current['item']['name']}"
            return "Playing previous track"
        except Exception as e:
            print(f"Previous track error: {e}")
            return "Error playing previous track"

    def cleanup(self):
        """Clean up Spotify resources properly"""
        try:
            if hasattr(self, 'sp') and self.sp:
                # Clear the auth manager
                if hasattr(self.sp, 'auth_manager'):
                    self.sp.auth_manager = None
                
                # Clear the client session
                if hasattr(self.sp, '_session'):
                    self.sp._session = None
                
                # Clear the Spotify instance
                self.sp = None
                
        except Exception as e:
            print(f"Spotify cleanup warning: {e}")

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup() 