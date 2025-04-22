import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Application configuration
CONFIG = {
    # ADK samples repository settings
    'ADK_SAMPLES_REPO': 'https://github.com/google/adk-samples.git',
    'ADK_SAMPLES_PATH': os.path.join(os.getcwd(), 'adk-samples'),
    
    # Application settings
    'FLASK_PORT': 5000,
    'FLASK_HOST': '0.0.0.0',
    'DEBUG': True,
    
    # UI settings
    'APP_NAME': 'Google ADK Training Environment',
    'THEME': 'dark',  # 'dark' or 'light'
    
    # Timeouts and limits
    'SAMPLE_EXECUTION_TIMEOUT': 60,  # seconds
    'MAX_OUTPUT_SIZE': 100000,  # characters
}

# Function to get a configuration value
def get_config(key, default=None):
    """
    Get a configuration value from the CONFIG dictionary.
    
    Args:
        key (str): The configuration key
        default: Default value if the key is not found
        
    Returns:
        The configuration value or the default
    """
    return CONFIG.get(key, default)
