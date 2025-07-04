import logging
import os
import sys
from typing import Optional

# Define log levels
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

# Define a global logger instance
logger = None

def setup_logger(name: str = "project_oracle", 
                level: int = logging.INFO, 
                log_file: Optional[str] = None,
                console_output: bool = True) -> logging.Logger:
    """
    Configure and return a logger with the specified settings.
    
    Args:
        name: The name for the logger instance
        level: The minimum log level to record
        log_file: Optional path to a log file
        console_output: Whether to output logs to console
    
    Returns:
        A configured logger instance
    """
    global logger
    
    if logger is not None:
        return logger
        
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:  
        logger.removeHandler(handler)
    
    # Create console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
    
    # Create file handler if a log file was specified
    if log_file:
        # Ensure the directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger() -> logging.Logger:
    """
    Get the global logger instance, initializing it if necessary.
    
    Returns:
        The global logger instance
    """
    global logger
    if logger is None:
        # Default initialization with INFO level if not already set up
        logger = setup_logger()
    return logger

# Helper functions for different log levels
def debug(message: str, *args, **kwargs) -> None:
    get_logger().debug(message, *args, **kwargs)

def info(message: str, *args, **kwargs) -> None:
    get_logger().info(message, *args, **kwargs)

def warning(message: str, *args, **kwargs) -> None:
    get_logger().warning(message, *args, **kwargs)

def error(message: str, *args, **kwargs) -> None:
    get_logger().error(message, *args, **kwargs)

def critical(message: str, *args, **kwargs) -> None:
    get_logger().critical(message, *args, **kwargs)
