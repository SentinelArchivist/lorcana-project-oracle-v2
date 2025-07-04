from functools import wraps
import traceback
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

from src.utils.logger import get_logger

logger = get_logger()

# Type variables for better type hints
T = TypeVar('T')
R = TypeVar('R')

def log_and_raise(exception: Exception, message: str) -> None:
    """
    Log an error message and raise the provided exception.
    
    Args:
        exception: The exception to raise
        message: The error message to log
    """
    logger.error(message)
    raise exception

def safe_operation(default_return: Optional[T] = None, 
                  log_level: str = 'error',
                  raise_exception: bool = False) -> Callable:
    """
    Decorator for safely executing operations with standardized error handling.
    
    Args:
        default_return: The default value to return if an exception occurs and raise_exception is False
        log_level: The logging level to use ('debug', 'info', 'warning', 'error', 'critical')
        raise_exception: Whether to re-raise the caught exception
    
    Returns:
        A decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get the function name for better error messages
                func_name = func.__name__
                
                # Format the error message
                error_message = f"Error in {func_name}: {str(e)}"
                
                # Log the error with the appropriate level
                if log_level == 'debug':
                    logger.debug(error_message)
                elif log_level == 'info':
                    logger.info(error_message)
                elif log_level == 'warning':
                    logger.warning(error_message)
                elif log_level == 'critical':
                    logger.critical(error_message)
                else:  # Default to error
                    logger.error(error_message)
                    
                # Add debug information if debug level
                if log_level == 'debug':
                    logger.debug(f"Exception details: {traceback.format_exc()}")
                
                # Decide whether to re-raise the exception
                if raise_exception:
                    raise
                    
                return default_return
        return wrapper
    return decorator

def handle_file_operations(func: Callable) -> Callable:
    """
    Decorator specifically for file operations with standardized error handling.
    
    Args:
        func: The function to decorate
    
    Returns:
        A decorated function
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            path = kwargs.get('path', '') or next((arg for arg in args if isinstance(arg, str) and '/' in arg), 'unknown file')
            logger.error(f"File not found: {path} - {str(e)}")
            raise
        except PermissionError as e:
            path = kwargs.get('path', '') or next((arg for arg in args if isinstance(arg, str) and '/' in arg), 'unknown file')
            logger.error(f"Permission denied for file: {path} - {str(e)}")
            raise
        except IOError as e:
            logger.error(f"I/O error in file operation: {str(e)}")
            raise
    return wrapper
