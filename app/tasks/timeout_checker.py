"""
Buggy Call - Request Timeout Checker
Automatically marks unanswered requests after 1 hour
"""
from datetime import datetime, timedelta
from app import db
from app.models.request import BuggyRequest, RequestStatus
import logging

logger = logging.getLogger(__name__)

# Timeout duration (1 hour)
TIMEOUT_DURATION = timedelta(hours=1)


def check_and_timeout_requests():
    """
    Check for PENDING requests older than 1 hour and mark them as unanswered
    Returns: Number of requests timed out
    """
    try:
        # Calculate timeout threshold
        timeout_threshold = datetime.utcnow() - TIMEOUT_DURATION
        
        # Find PENDING requests older than 1 hour
        PENDING_requests = BuggyRequest.query.filter(
            BuggyRequest.status == RequestStatus.PENDING,
            BuggyRequest.requested_at <= timeout_threshold
        ).all()
        
        timeout_count = 0
        
        for request in PENDING_requests:
            # Mark as unanswered
            request.status = RequestStatus.UNANSWERED
            request.timeout_at = datetime.utcnow()
            
            # Calculate response time (negative to indicate timeout)
            if request.requested_at:
                elapsed = datetime.utcnow() - request.requested_at
                request.response_time = int(elapsed.total_seconds())
            
            timeout_count += 1
            
            logger.info(f"Request #{request.id} timed out after 1 hour (Location: {request.location.name if request.location else 'Unknown'})")
        
        # Commit changes
        if timeout_count > 0:
            db.session.commit()
            logger.info(f"✅ Marked {timeout_count} request(s) as unanswered")
        
        return timeout_count
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error checking request timeouts: {str(e)}")
        return 0


def get_timeout_statistics(hotel_id=None, days=30):
    """
    Get statistics about timed out requests
    
    Args:
        hotel_id: Filter by hotel (optional)
        days: Number of days to look back
    
    Returns:
        Dictionary with timeout statistics
    """
    try:
        # Calculate date range
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Build query
        query = BuggyRequest.query.filter(
            BuggyRequest.status == RequestStatus.UNANSWERED,
            BuggyRequest.requested_at >= start_date
        )
        
        if hotel_id:
            query = query.filter(BuggyRequest.hotel_id == hotel_id)
        
        # Get all unanswered requests
        unanswered_requests = query.all()
        
        # Calculate statistics
        total_unanswered = len(unanswered_requests)
        
        # Group by location
        by_location = {}
        for req in unanswered_requests:
            location_name = req.location.name if req.location else 'Unknown'
            if location_name not in by_location:
                by_location[location_name] = 0
            by_location[location_name] += 1
        
        # Group by hour of day
        by_hour = {}
        for req in unanswered_requests:
            if req.requested_at:
                hour = req.requested_at.hour
                if hour not in by_hour:
                    by_hour[hour] = 0
                by_hour[hour] += 1
        
        # Group by day of week
        by_day = {}
        for req in unanswered_requests:
            if req.requested_at:
                day = req.requested_at.strftime('%A')
                if day not in by_day:
                    by_day[day] = 0
                by_day[day] += 1
        
        return {
            'total_unanswered': total_unanswered,
            'by_location': by_location,
            'by_hour': by_hour,
            'by_day': by_day,
            'period_days': days
        }
        
    except Exception as e:
        logger.error(f"Error getting timeout statistics: {str(e)}")
        return {
            'total_unanswered': 0,
            'by_location': {},
            'by_hour': {},
            'by_day': {},
            'period_days': days
        }
