"""
Logging configuration for the healthcare diagnostic backend
"""

import logging
import sys
from typing import Dict, Any
import json
from datetime import datetime

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "levelname", "levelno", "pathname", 
                          "filename", "module", "exc_info", "exc_text", "stack_info",
                          "lineno", "funcName", "created", "msecs", "relativeCreated",
                          "thread", "threadName", "processName", "process", "getMessage"]:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class HealthcareLogger:
    """Centralized logging configuration"""
    
    def __init__(self):
        self.logger = logging.getLogger("healthcare_diagnostic")
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # Use JSON formatter in production, simple formatter in development
        if settings.ENVIRONMENT == "production":
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(settings.LOG_FORMAT)
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Prevent duplicate logs
        self.logger.propagate = False
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """Get logger instance"""
        if name:
            return logging.getLogger(f"healthcare_diagnostic.{name}")
        return self.logger


# Global logger instance
healthcare_logger = HealthcareLogger()
logger = healthcare_logger.get_logger()


def log_api_request(
    method: str,
    path: str,
    user_id: str = None,
    request_id: str = None,
    **kwargs
):
    """Log API request details"""
    logger.info(
        "API Request",
        extra={
            "type": "api_request",
            "method": method,
            "path": path,
            "user_id": user_id,
            "request_id": request_id,
            **kwargs
        }
    )


def log_api_response(
    method: str,
    path: str,
    status_code: int,
    response_time_ms: float,
    user_id: str = None,
    request_id: str = None,
    **kwargs
):
    """Log API response details"""
    logger.info(
        "API Response",
        extra={
            "type": "api_response",
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "user_id": user_id,
            "request_id": request_id,
            **kwargs
        }
    )


def log_error(
    error: Exception,
    context: Dict[str, Any] = None,
    user_id: str = None,
    request_id: str = None
):
    """Log error with context"""
    logger.error(
        f"Error occurred: {str(error)}",
        exc_info=True,
        extra={
            "type": "error",
            "error_type": type(error).__name__,
            "context": context or {},
            "user_id": user_id,
            "request_id": request_id,
        }
    )


def log_security_event(
    event_type: str,
    details: Dict[str, Any],
    user_id: str = None,
    ip_address: str = None
):
    """Log security-related events"""
    logger.warning(
        f"Security event: {event_type}",
        extra={
            "type": "security_event",
            "event_type": event_type,
            "details": details,
            "user_id": user_id,
            "ip_address": ip_address,
        }
    )


def log_medical_event(
    event_type: str,
    details: Dict[str, Any],
    user_id: str = None,
    chat_id: str = None
):
    """Log medical-related events"""
    logger.info(
        f"Medical event: {event_type}",
        extra={
            "type": "medical_event",
            "event_type": event_type,
            "details": details,
            "user_id": user_id,
            "chat_id": chat_id,
        }
    )
