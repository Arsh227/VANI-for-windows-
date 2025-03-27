import os
from dotenv import load_dotenv

load_dotenv()

# Store all sensitive credentials with proper error handling
def get_env_var(var_name, default=None):
    value = os.getenv(var_name, default)
    if value is None:
        print(f"Warning: {var_name} not found in environment variables")
    return value

# Spotify credentials
SPOTIFY_CLIENT_ID = get_env_var('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = get_env_var('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"

# Email credentials
EMAIL_ADDRESS = get_env_var('EMAIL_ADDRESS')
EMAIL_PASSWORD = get_env_var('EMAIL_PASSWORD')

# File paths with OS-independent handling
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")

# Create necessary directories
for directory in [DATA_DIR, CACHE_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True) 