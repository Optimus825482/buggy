"""
Performance Monitoring Utilities
Tracks and logs performance metrics for optimization
"""
import time
import logging
from functools import wraps
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Performance monitoring utility
    Tracks execution times, query counts, and other metrics
    """
    
    # Thread-safe metrics storage
    _metrics = defaultdict(lambda: {
        'count': 0,
        'total_time': 0.0,
        'min_time': float('inf'),
        'max_time': 0.0,
        'avg_time': 0.0
    })
    _lock = Lock()
    
    @classmethod
    def track(cls, operation_name):
        """
        Decorator to track operation performance
        
        Usage:
            @PerformanceMonitor.track('get_pending_requests')
            def get_pending_requests(hotel_id):
                ...
        
        Args:
            operation_name: Name of the operation to track
        
        Returns:
            Decorated function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    elapsed_time = time.time() - start_time
                    cls._record_metric(operation_name, elapsed_time)
                    
                    # Log slow operations (> 1 second)
                    if elapsed_time > 1.0:
                        logger.warning(
                            f"⚠️ Slow operation: {operation_name} took {elapsed_time:.3f}s"
                        )
            
            return wrapper
        return decorator
    
    @classmethod
    def _record_metric(cls, operation_name, elapsed_time):
        """
        Record a metric
        
        Args:
            operation_name: Name of the operation
            elapsed_time: Time taken in seconds
        """
        with cls._lock:
            metric = cls._metrics[operation_name]
            metric['count'] += 1
            metric['total_time'] += elapsed_time
            metric['min_time'] = min(metric['min_time'], elapsed_time)
            metric['max_time'] = max(metric['max_time'], elapsed_time)
            metric['avg_time'] = metric['total_time'] / metric['count']
    
    @classmethod
    def get_metrics(cls, operation_name=None):
        """
        Get performance metrics
        
        Args:
            operation_name: Specific operation name (optional)
        
        Returns:
            dict: Metrics for the operation or all operations
        """
        with cls._lock:
            if operation_name:
                return dict(cls._metrics.get(operation_name, {}))
            return {k: dict(v) for k, v in cls._metrics.items()}
    
    @classmethod
    def reset_metrics(cls, operation_name=None):
        """
        Reset metrics
        
        Args:
            operation_name: Specific operation name (optional)
        """
        with cls._lock:
            if operation_name:
                if operation_name in cls._metrics:
                    del cls._metrics[operation_name]
            else:
                cls._metrics.clear()
    
    @classmethod
    def log_metrics(cls):
        """Log all metrics to console"""
        with cls._lock:
            if not cls._metrics:
                logger.info("📊 No performance metrics recorded")
                return
            
            logger.info("📊 Performance Metrics:")
            logger.info("-" * 80)
            
            for operation, metric in sorted(cls._metrics.items()):
                logger.info(
                    f"  {operation}:\n"
                    f"    Count: {metric['count']}\n"
                    f"    Avg: {metric['avg_time']:.3f}s\n"
                    f"    Min: {metric['min_time']:.3f}s\n"
                    f"    Max: {metric['max_time']:.3f}s\n"
                    f"    Total: {metric['total_time']:.3f}s"
                )
            
            logger.info("-" * 80)


class QueryCounter:
    """
    Database query counter
    Tracks number of queries executed
    """
    
    _query_count = 0
    _lock = Lock()
    
    @classmethod
    def increment(cls):
        """Increment query count"""
        with cls._lock:
            cls._query_count += 1
    
    @classmethod
    def get_count(cls):
        """Get current query count"""
        with cls._lock:
            return cls._query_count
    
    @classmethod
    def reset(cls):
        """Reset query count"""
        with cls._lock:
            cls._query_count = 0
    
    @classmethod
    def track_queries(cls, func):
        """
        Decorator to track queries in a function
        
        Usage:
            @QueryCounter.track_queries
            def get_data():
                ...
        
        Args:
            func: Function to track
        
        Returns:
            Decorated function
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            cls.reset()
            result = func(*args, **kwargs)
            count = cls.get_count()
            
            if count > 10:
                logger.warning(
                    f"⚠️ High query count: {func.__name__} executed {count} queries"
                )
            else:
                logger.debug(f"📊 {func.__name__} executed {count} queries")
            
            return result
        
        return wrapper


def measure_time(operation_name):
    """
    Context manager to measure execution time
    
    Usage:
        with measure_time('complex_operation'):
            # ... code ...
    
    Args:
        operation_name: Name of the operation
    """
    class TimeMeasurer:
        def __init__(self, name):
            self.name = name
            self.start_time = None
        
        def __enter__(self):
            self.start_time = time.time()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            elapsed = time.time() - self.start_time
            logger.debug(f"⏱️ {self.name} took {elapsed:.3f}s")
            
            if elapsed > 1.0:
                logger.warning(f"⚠️ Slow operation: {self.name} took {elapsed:.3f}s")
    
    return TimeMeasurer(operation_name)


# Example usage in request service:
"""
from app.utils.performance_monitor import PerformanceMonitor

class RequestService:
    
    @staticmethod
    @PerformanceMonitor.track('get_pending_requests')
    def get_PENDING_requests(hotel_id):
        # ... implementation ...
        pass
"""
