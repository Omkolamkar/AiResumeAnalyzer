# utils.py - Enhanced Utilities with Error Handling and Validation
import os
import time
import hashlib
import tempfile
import functools
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging
import streamlit as st
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class ProcessingError(Exception):
    """Custom exception for processing errors"""
    pass

def retry_with_exponential_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retrying functions with exponential backoff"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Function {func.__name__} failed after {max_retries} attempts: {str(e)}")
                        raise e
                    
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. Retrying in {delay}s...")
                    time.sleep(delay)
        return wrapper
    return decorator

def validate_file(uploaded_file, max_size_mb: int = 10, allowed_types: List[str] = None) -> bool:
    """
    Validate uploaded file
    Args:
        uploaded_file: Streamlit uploaded file object
        max_size_mb: Maximum file size in MB
        allowed_types: List of allowed file extensions
    Returns:
        bool: True if valid
    Raises:
        ValidationError: If file is invalid
    """
    if not uploaded_file:
        raise ValidationError("No file uploaded")
    
    # Check file size
    if uploaded_file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"File size exceeds {max_size_mb}MB limit")
    
    # Check file type
    if allowed_types:
        file_extension = uploaded_file.name.lower().split('.')[-1]
        if file_extension not in allowed_types:
            raise ValidationError(f"File type '{file_extension}' not allowed. Allowed types: {', '.join(allowed_types)}")
    
    # Check if file is actually a PDF (basic check)
    if uploaded_file.name.lower().endswith('.pdf'):
        # Read first few bytes to check PDF signature
        uploaded_file.seek(0)
        header = uploaded_file.read(4)
        uploaded_file.seek(0)
        if header != b'%PDF':
            raise ValidationError("Invalid PDF file format")
    
    logger.info(f"File validation passed for: {uploaded_file.name}")
    return True

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent security issues"""
    # Remove path traversal attempts
    filename = os.path.basename(filename)
    # Remove or replace dangerous characters
    dangerous_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    return filename

def generate_file_hash(file_content: bytes) -> str:
    """Generate hash for file content for caching purposes"""
    return hashlib.md5(file_content).hexdigest()

@contextmanager
def temporary_file(suffix: str = None):
    """Context manager for temporary files"""
    temp_file = None
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        yield temp_file
    finally:
        if temp_file:
            temp_file.close()
            try:
                os.unlink(temp_file.name)
            except OSError:
                pass

def safe_execute(func, *args, default=None, error_msg="Operation failed", **kwargs):
    """
    Safely execute a function with error handling
    Args:
        func: Function to execute
        *args: Function arguments
        default: Default value to return on error
        error_msg: Error message prefix
        **kwargs: Function keyword arguments
    Returns:
        Function result or default value
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"{error_msg}: {str(e)}")
        if default is not None:
            return default
        raise ProcessingError(f"{error_msg}: {str(e)}")

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    size_index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and size_index < len(size_names) - 1:
        size /= 1024.0
        size_index += 1
    
    return f"{size:.1f} {size_names[size_index]}"

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    # Remove special characters that might cause issues
    text = text.encode('ascii', 'ignore').decode('ascii')
    return text.strip()

def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Basic phone number validation"""
    import re
    # Remove common formatting characters
    phone = re.sub(r'[\s\-\(\)\+]', '', phone)
    # Check if it contains only digits and is reasonable length
    return phone.isdigit() and 10 <= len(phone) <= 15

def cache_key_generator(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()

def display_error(error_msg: str, error_type: str = "error"):
    """Display error message in Streamlit with appropriate styling"""
    if error_type == "error":
        st.error(f"❌ {error_msg}")
    elif error_type == "warning":
        st.warning(f"⚠️ {error_msg}")
    elif error_type == "info":
        st.info(f"ℹ️ {error_msg}")
    
    logger.error(f"UI Error displayed: {error_msg}")

def display_success(success_msg: str):
    """Display success message in Streamlit"""
    st.success(f"✅ {success_msg}")
    logger.info(f"UI Success displayed: {success_msg}")

def create_progress_tracker(total_steps: int, description: str = "Processing"):
    """Create a progress tracker for long-running operations"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    class ProgressTracker:
        def __init__(self):
            self.current_step = 0
            self.total = total_steps
            
        def update(self, step_description: str = ""):
            self.current_step += 1
            progress = self.current_step / self.total
            progress_bar.progress(progress)
            
            if step_description:
                status_text.text(f"{description}: {step_description} ({self.current_step}/{self.total})")
            else:
                status_text.text(f"{description}: {self.current_step}/{self.total}")
        
        def complete(self, message: str = "Complete!"):
            progress_bar.progress(1.0)
            status_text.text(message)
            time.sleep(1)  # Brief pause to show completion
            progress_bar.empty()
            status_text.empty()
    
    return ProgressTracker()

def log_user_action(action: str, details: Dict[str, Any] = None):
    """Log user actions for analytics and debugging"""
    log_entry = {
        "timestamp": time.time(),
        "action": action,
        "session_id": st.session_state.get("session_id", "unknown"),
        "details": details or {}
    }
    logger.info(f"User Action: {log_entry}")

def handle_streamlit_error(func):
    """Decorator to handle errors in Streamlit functions gracefully"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"Error in {func.__name__}: {str(e)}"
            logger.error(error_msg)
            display_error(error_msg)
            return None
    return wrapper