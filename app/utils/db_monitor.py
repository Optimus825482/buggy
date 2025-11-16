"""
Buggy Call - Database Connection Pool Monitor
MySQL bağlantı havuzu izleme ve raporlama
"""
from app import db
from flask import current_app
import logging

logger = logging.getLogger(__name__)


class DBConnectionMonitor:
    """MySQL connection pool monitoring utility"""
    
    @staticmethod
    def get_pool_status():
        """
        Get current connection pool status
        
        Returns:
            dict: Pool statistics including size, checked out, overflow
        """
        try:
            engine = db.engine
            pool = engine.pool
            
            status = {
                'pool_size': pool.size(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'checked_in': pool.checkedin(),
                'total_connections': pool.size() + pool.overflow(),
                'available': pool.size() - pool.checkedout(),
                'status': 'healthy'
            }
            
            # Check for potential issues
            if pool.checkedout() >= pool.size() * 0.9:
                status['status'] = 'warning'
                status['message'] = 'Pool nearing capacity'
            
            if pool.overflow() > 0:
                status['status'] = 'warning'
                status['message'] = 'Using overflow connections'
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting pool status: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    @staticmethod
    def log_pool_status():
        """Log current pool status to application log"""
        try:
            status = DBConnectionMonitor.get_pool_status()
            
            logger.info("="*60)
            logger.info("MySQL Connection Pool Status")
            logger.info(f"  Pool Size: {status.get('pool_size', 'N/A')}")
            logger.info(f"  Checked Out: {status.get('checked_out', 'N/A')}")
            logger.info(f"  Checked In: {status.get('checked_in', 'N/A')}")
            logger.info(f"  Overflow: {status.get('overflow', 'N/A')}")
            logger.info(f"  Available: {status.get('available', 'N/A')}")
            logger.info(f"  Status: {status.get('status', 'unknown')}")
            if 'message' in status:
                logger.info(f"  Message: {status['message']}")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Error logging pool status: {e}")
    
    @staticmethod
    def check_pool_health():
        """
        Check pool health and return warnings if needed
        
        Returns:
            tuple: (is_healthy: bool, warnings: list)
        """
        try:
            status = DBConnectionMonitor.get_pool_status()
            warnings = []
            
            # Check for high usage
            if status['checked_out'] >= status['pool_size'] * 0.8:
                warnings.append(
                    f"High pool usage: {status['checked_out']}/{status['pool_size']} "
                    f"({status['checked_out']/status['pool_size']*100:.1f}%)"
                )
            
            # Check for overflow usage
            if status['overflow'] > 0:
                warnings.append(
                    f"Using overflow connections: {status['overflow']}"
                )
            
            # Check for no available connections
            if status['available'] == 0:
                warnings.append("No available connections in pool!")
            
            is_healthy = len(warnings) == 0
            
            return is_healthy, warnings
            
        except Exception as e:
            logger.error(f"Error checking pool health: {e}")
            return False, [f"Error checking pool: {str(e)}"]
    
    @staticmethod
    def get_connection_info():
        """
        Get detailed connection information
        
        Returns:
            dict: Detailed connection statistics
        """
        try:
            engine = db.engine
            
            # Get pool info
            pool_status = DBConnectionMonitor.get_pool_status()
            
            # Get engine info
            info = {
                'pool': pool_status,
                'engine': {
                    'driver': engine.driver,
                    'url': str(engine.url).replace(engine.url.password or '', '***'),
                    'pool_class': engine.pool.__class__.__name__,
                    'echo': engine.echo,
                    'pool_pre_ping': engine.pool._pre_ping if hasattr(engine.pool, '_pre_ping') else None,
                    'pool_recycle': engine.pool._recycle if hasattr(engine.pool, '_recycle') else None,
                }
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting connection info: {e}")
            return {
                'error': str(e)
            }
