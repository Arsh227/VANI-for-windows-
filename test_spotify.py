from features.spotify_control import SpotifyControl
import time

def test_spotify():
    spotify = SpotifyControl()
    
    # Test playing a song
    print("\nTesting play...")
    result = spotify.play_music("Shape of You")
    print(result)
    
    # Wait a bit
    time.sleep(5)
    
    # Test pause
    print("\nTesting pause...")
    result = spotify.pause_music()
    print(result)

if __name__ == "__main__":
    test_spotify() 