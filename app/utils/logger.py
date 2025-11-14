"""
Enhanced Logging Utilities
Comprehensive logging for FCM, WebSocket, and Request lifecycle
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps

# Configure logger
logger = logging.getLogger('buggycall')


def log_fcm_event(event_type: str, data: Dict[str, Any]):
    """
    Log FCM events with structured data
    
    Args:
        event_type: Type of FCM event (SDK_INITIALIZED, NOTIFICATION_SENT, etc.)
        data: Event data
    """
    logger.info(f"📱 FCM_EVENT: {event_type} | {json.dumps(data, default=str)}")


def log_websocket_event(event_type: str, data: Dict[str, Any]):
    """
    Log WebSocket events with structured data
    
    Args:
        event_type: Type of WebSocket event (CONNECTED, DISCONNECTED, etc.)
        data: Event data
    """
    logger.info(f"🔌 WS_EVENT: {event_type} | {json.dumps(data, default=str)}")


def log_request_lifecycle(stage: str, request_id: int, data: Dict[str, Any]):
    """
    Log request lifecycle events
    
    Args:
        stage: Lifecycle stage (CREATED, ACCEPTED, COMPLETED, etc.)
        request_id: Request ID
        data: Additional data
    """
    logger.info(f"📋 REQUEST_LIFECYCLE: {stage} | Request {request_id} | {json.dumps(data, default=str)}")


def log_error(error_type: str, message: str, context: Optional[Dict[str, Any]] = None):
    """
    Log errors with context
    
    Args:
        error_type: Type of error (FCM_INIT, WS_DISCONNECT, etc.)
        message: Error message
        context: Additional context
    """
    context_str = json.dumps(context, default=str) if context else "{}"
    logger.error(f"❌ ERROR: {error_type} | {message} | Context: {context_str}")


def log_performance(operation: str, duration_ms: float, context: Optional[Dict[str, Any]] = None):
    """
    Log performance metrics
    
    Args:
        operation: Operation name
        duration_ms: Duration in milliseconds
        context: Additional context
    """
    context_str = json.dumps(context, default=str) if context else "{}"
    
    # Warn if slow
    if duration_ms > 1000:
        logger.warning(f"⚠️ SLOW_OPERATION: {operation} took {duration_ms:.2f}ms | {context_str}")
    else:
        logger.debug(f"⏱️ PERFORMANCE: {operation} took {duration_ms:.2f}ms | {context_str}")


def log_with_context(func):
    """
    Decorator to log function execution with context
    
    Usage:
        @log_with_context
        def my_function(arg1, arg2):
            ...
    
    Args:
        func: Function to decorate
    
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        logger.debug(f"🔵 START: {func_name} | Args: {args[:2] if args else '()'} | Kwargs: {list(kwargs.keys())}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"✅ SUCCESS: {func_name}")
            return result
        except Exception as e:
            logger.error(f"❌ ERROR: {func_name} | Exception: {type(e).__name__}: {str(e)}")
            raise
    
    return wrapper


class RequestLifecycleLogger:
    """
    Context manager for logging request lifecycle
    
    Usage:
        with RequestLifecycleLogger('ACCEPT_REQUEST', request_id=123) as log:
            # ... do work ...
            log.add_data('driver_id', driver_id)
    """
    
    def __init__(self, stage: str, request_id: int):
        self.stage = stage
        self.request_id = request_id
        self.data = {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        logger.info(f"📋 REQUEST_LIFECYCLE: {self.stage} | Request {self.request_id} | START")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (datetime.utcnow() - self.start_time).total_seconds() * 1000
        
        if exc_type is None:
            # Success
            self.data['duration_ms'] = f"{duration_ms:.2f}"
            log_request_lifecycle(self.stage, self.request_id, self.data)
            logger.info(f"✅ REQUEST_LIFECYCLE: {self.stage} | Request {self.request_id} | SUCCESS ({duration_ms:.2f}ms)")
        else:
            # Error
            self.data['duration_ms'] = f"{duration_ms:.2f}"
            self.data['error'] = f"{exc_type.__name__}: {str(exc_val)}"
            log_request_lifecycle(self.stage, self.request_id, self.data)
            logger.error(f"❌ REQUEST_LIFECYCLE: {self.stage} | Request {self.request_id} | ERROR ({duration_ms:.2f}ms)")
    
    def add_data(self, key: str, value: Any):
        """Add data to log"""
        self.data[key] = value


class FCMDeliveryLogger:
    """
    Logger for FCM delivery tracking
    """
    
    @staticmethod
    def log_delivery_attempt(token: str, title: str, priority: str):
        """Log FCM delivery attempt"""
        logger.info(f"📤 FCM_DELIVERY: ATTEMPT | Token: {token[:20]}... | Title: {title} | Priority: {priority}")
    
    @staticmethod
    def log_delivery_success(token: str, title: str, response: str):
        """Log FCM delivery success"""
        logger.info(f"✅ FCM_DELIVERY: SUCCESS | Token: {token[:20]}... | Title: {title} | Response: {response}")
    
    @staticmethod
    def log_delivery_failure(token: str, title: str, error: str):
        """Log FCM delivery failure"""
        logger.error(f"❌ FCM_DELIVERY: FAILURE | Token: {token[:20]}... | Title: {title} | Error: {error}")
    
    @staticmethod
    def log_token_cleanup(token: str, reason: str):
        """Log token cleanup"""
        logger.warning(f"🗑️ FCM_TOKEN: CLEANUP | Token: {token[:20]}... | Reason: {reason}")


class WebSocketLogger:
    """
    Logger for WebSocket events
    """
    
    @staticmethod
    def log_connection(user_id: int, role: str):
        """Log WebSocket connection"""
        logger.info(f"🔌 WS_CONNECTION: CONNECTED | User: {user_id} | Role: {role}")
    
    @staticmethod
    def log_disconnection(user_id: int, reason: str = "unknown"):
        """Log WebSocket disconnection"""
        logger.info(f"🔌 WS_CONNECTION: DISCONNECTED | User: {user_id} | Reason: {reason}")
    
    @staticmethod
    def log_reconnection(user_id: int, attempt: int):
        """Log WebSocket reconnection attempt"""
        logger.info(f"🔄 WS_CONNECTION: RECONNECTING | User: {user_id} | Attempt: {attempt}")
    
    @staticmethod
    def log_event_emit(event_name: str, room: str, data_size: int):
        """Log WebSocket event emission"""
        logger.debug(f"📤 WS_EVENT: EMIT | Event: {event_name} | Room: {room} | Size: {data_size} bytes")
    
    @staticmethod
    def log_event_receive(event_name: str, user_id: int):
        """Log WebSocket event reception"""
        logger.debug(f"📥 WS_EVENT: RECEIVE | Event: {event_name} | User: {user_id}")
    
    @staticmethod
    def log_throttle(room: str, queued_count: int):
        """Log WebSocket throttling"""
        logger.warning(f"⏳ WS_THROTTLE: QUEUED | Room: {room} | Queued: {queued_count} events")
    
    @staticmethod
    def log_error(event_name: str, error: str, context: Dict[str, Any]):
        """Log WebSocket error"""
        logger.error(f"❌ WS_ERROR: {event_name} | Error: {error} | Context: {json.dumps(context, default=str)}")


def log_request_event(event_type: str, data: Dict[str, Any]):
    """
    Log request events (alias for log_request_lifecycle)
    
    Args:
        event_type: Event type
        data: Event data
    """
    request_id = data.get('request_id', 'unknown')
    logger.info(f"📋 REQUEST_EVENT: {event_type} | Request {request_id} | {json.dumps(data, default=str)}")


def log_driver_event(event_type: str, data: Dict[str, Any]):
    """
    Log driver events
    
    Args:
        event_type: Event type
        data: Event data
    """
    driver_id = data.get('driver_id', 'unknown')
    logger.info(f"👤 DRIVER_EVENT: {event_type} | Driver {driver_id} | {json.dumps(data, default=str)}")


def log_api_call(endpoint: str, method: str, data: Optional[Dict[str, Any]] = None):
    """
    Log API calls
    
    Args:
        endpoint: API endpoint
        method: HTTP method
        data: Request data
    """
    data_str = json.dumps(data, default=str) if data else "{}"
    logger.info(f"🌐 API_CALL: {method} {endpoint} | Data: {data_str}")


# Export all loggers
__all__ = [
    'logger',
    'log_fcm_event',
    'log_websocket_event',
    'log_request_lifecycle',
    'log_request_event',
    'log_driver_event',
    'log_api_call',
    'log_error',
    'log_performance',
    'log_with_context',
    'RequestLifecycleLogger',
    'FCMDeliveryLogger',
    'WebSocketLogger'
]
