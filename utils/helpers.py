import os
import json
import logging
from datetime import datetime

def ensure_dir(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def setup_logging():
    """Setup logging configuration"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"assistant_{datetime.now().strftime('%Y%m%d')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def safe_save_json(data, filepath):
    """Safely save JSON data"""
    try:
        directory = os.path.dirname(filepath)
        ensure_dir(directory)
        with open(filepath, 'w') as f:
            json.dump(data, f)
        return True
    except Exception as e:
        logging.error(f"Error saving JSON: {str(e)}")
        return False

def safe_load_json(filepath):
    """Safely load JSON data"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logging.error(f"Error loading JSON: {str(e)}")
        return {}

def safe_request(func):
    """Decorator for safe API requests"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in {func.__name__}: {str(e)}")
            return None
    return wrapper 