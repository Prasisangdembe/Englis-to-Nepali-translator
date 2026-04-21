import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Application settings
    APP_NAME = "Limbu Translation System"
    VERSION = "1.0.0"
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # API settings
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 5000))
    API_KEY = os.getenv('API_KEY', 'your-secret-key')
    
    # Database settings
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/limbu_db')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # ML settings
    MODEL_PATH = os.getenv('MODEL_PATH', './models/saved')
    MLFLOW_URI = os.getenv('MLFLOW_URI', 'http://localhost:5001')
    
    # Translation settings
    MAX_TRANSLATION_LENGTH = 512
    BATCH_SIZE = 32
    
    # Feedback settings
    MIN_VALIDATORS = 3
    CONSENSUS_THRESHOLD = 0.66
    TRUST_SCORE_THRESHOLD = 0.5
    
    # Security settings
    RATE_LIMIT_PER_MINUTE = 60
    MAX_FEEDBACK_PER_USER_PER_DAY = 100
    
    # Limbu specific
    LIMBU_UNICODE_RANGE = (0x1900, 0x194F)
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'limbu_translation.log')

config = Config()