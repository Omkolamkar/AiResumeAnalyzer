# config.py - Centralized Configuration Management
import os
import logging
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class APIConfig:
    """API Configuration settings"""
    google_api_key: Optional[str] = None
    adzuna_app_id: Optional[str] = None
    adzuna_app_key: Optional[str] = None
    rapidapi_key: Optional[str] = None
    
    def __post_init__(self):
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.adzuna_app_id = os.getenv("ADZUNA_APP_ID")
        self.adzuna_app_key = os.getenv("ADZUNA_APP_KEY")
        self.rapidapi_key = os.getenv("RAPIDAPI_KEY")

@dataclass
class AppConfig:
    """Application Configuration settings"""
    app_title: str = "🤖 AI Resume Analyzer & Job Matcher"
    max_file_size_mb: int = 10
    allowed_file_types: list = None
    log_level: str = "INFO"
    cache_ttl: int = 3600  # Cache TTL in seconds
    max_jobs_per_search: int = 50
    api_timeout: int = 30
    retry_attempts: int = 3
    
    def __post_init__(self):
        if self.allowed_file_types is None:
            self.allowed_file_types = ["pdf"]
        
        # Override with environment variables if available
        self.max_file_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", self.max_file_size_mb))
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
        self.cache_ttl = int(os.getenv("CACHE_TTL", self.cache_ttl))

@dataclass
class UIConfig:
    """UI Configuration settings"""
    theme_options: dict = None
    sidebar_width: int = 300
    main_container_width: str = "wide"
    
    def __post_init__(self):
        if self.theme_options is None:
            self.theme_options = {
                "light": {
                    "background_color": "#FFFFFF",
                    "text_color": "#000000",
                    "primary_color": "#FF6B6B",
                    "accent_color": "#4ECDC4"
                },
                "dark": {
                    "background_color": "#0E1117",
                    "text_color": "#FFFFFF", 
                    "primary_color": "#FF6B6B",
                    "accent_color": "#4ECDC4"
                }
            }

# Global configuration instances
api_config = APIConfig()
app_config = AppConfig()
ui_config = UIConfig()

def setup_logging():
    """Setup application logging"""
    logging.basicConfig(
        level=getattr(logging, app_config.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def validate_api_keys():
    """Validate that required API keys are present"""
    missing_keys = []
    
    if not api_config.google_api_key:
        missing_keys.append("GOOGLE_API_KEY")
    
    if missing_keys:
        raise ValueError(f"Missing required API keys: {', '.join(missing_keys)}")
    
    return True

def get_file_size_limit_bytes():
    """Get file size limit in bytes"""
    return app_config.max_file_size_mb * 1024 * 1024