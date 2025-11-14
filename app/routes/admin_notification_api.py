"""
Buggy Call - Admin Notification Monitoring API
Provides endpoints for monitoring notification delivery and performance
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.notification_log import NotificationLog
from app.models.user import SystemUser
from datetime import datetime, timedelta
from sqlalchemy import func, and_

admin_notification_api = Blueprint('admin_notification_api', __name__)


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.value != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@admin_notification_api.route('/api/admin/notifications/stats', methods=['GET'])
@login_required
@admin_required
def get_notification_stats():
    """Get notification delivery statistics"""
    try:
        # Get time range from query params (default: last 24 hours)
        hours = request.args.get('hours', 24, type=int)
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Basic stats
        total_sent = NotificationLog.query.filter(
            NotificationLog.sent_at >= since
        ).count()
        
        total_delivered = NotificationLog.query.filter(
            NotificationLog.status == 'sent',
            NotificationLog.sent_at >= since
        ).count()
        
        total_failed = NotificationLog.query.filter(
            NotificationLog.status == 'failed',
            NotificationLog.sent_at >= since
        ).count()
        
        total_clicked = NotificationLog.query.filter(
            NotificationLog.clicked_at.isnot(None),
            NotificationLog.sent_at >= since
        ).count()
        
        # Calculate delivery rate
        delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
        
        # Calculate click-through rate
        click_through_rate = (total_clicked / total_delivered * 100) if total_delivered > 0 else 0
        
        # Average delivery time
        avg_delivery_time = calculate_avg_delivery_time(since)
        
        # Stats by priority
        by_priority = get_stats_by_priority(since)
        
        # Stats by type
        by_type = get_stats_by_type(since)
        
        # Recent failures
        recent_failures = get_recent_failures(limit=10, since=since)
        
        # FCM specific stats
        fcm_stats = get_fcm_stats(since)
        
        stats = {
            'time_range_hours': hours,
            'total_sent': total_sent,
            'total_delivered': total_delivered,
            'total_failed': total_failed,
            'total_clicked': total_clicked,
            'delivery_rate': round(delivery_rate, 2),
            'click_through_rate': round(click_through_rate, 2),
            'avg_delivery_time_seconds': avg_delivery_time,
            'by_priority': by_priority,
            'by_type': by_type,
            'recent_failures': recent_failures,
            'fcm': fcm_stats
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_notification_api.route('/api/admin/notifications/active-subscriptions', methods=['GET'])
@login_required
@admin_required
def get_active_subscriptions():
    """Get list of active push subscriptions"""
    try:
        users = SystemUser.query.filter(
            SystemUser.push_subscription.isnot(None),
            SystemUser.is_active == True
        ).all()
        
        subscriptions = []
        for user in users:
            # Get last notification time
            last_notification = NotificationLog.query.filter_by(
                user_id=user.id
            ).order_by(NotificationLog.sent_at.desc()).first()
            
            subscriptions.append({
                'user_id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role.value,
                'subscribed_at': user.push_subscription_date.isoformat() if user.push_subscription_date else None,
                'last_notification': last_notification.sent_at.isoformat() if last_notification else None,
                'notification_preferences': user.get_notification_preferences()
            })
        
        return jsonify({
            'total_subscriptions': len(subscriptions),
            'subscriptions': subscriptions
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_notification_api.route('/api/admin/notifications/metrics/realtime', methods=['GET'])
@login_required
@admin_required
def get_realtime_metrics():
    """Get real-time notification metrics"""
    try:
        # Last hour stats
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        # Notifications sent in last hour
        notifications_last_hour = NotificationLog.query.filter(
            NotificationLog.sent_at >= one_hour_ago
        ).count()
        
        # Active subscriptions
        active_subscriptions = SystemUser.query.filter(
            SystemUser.push_subscription.isnot(None),
            SystemUser.is_active == True
        ).count()
        
        # Error rate
        error_rate = calculate_error_rate(one_hour_ago)
        
        # Delivery rate
        delivered_last_hour = NotificationLog.query.filter(
            NotificationLog.status == 'delivered',
            NotificationLog.sent_at >= one_hour_ago
        ).count()
        
        delivery_rate = (delivered_last_hour / notifications_last_hour * 100) if notifications_last_hour > 0 else 0
        
        # Average delivery time
        avg_delivery_time = calculate_avg_delivery_time(one_hour_ago)
        
        # Click-through rate
        clicked_last_hour = NotificationLog.query.filter(
            NotificationLog.clicked_at.isnot(None),
            NotificationLog.sent_at >= one_hour_ago
        ).count()
        
        click_through_rate = (clicked_last_hour / delivered_last_hour * 100) if delivered_last_hour > 0 else 0
        
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'notifications_sent_last_hour': notifications_last_hour,
            'active_subscriptions': active_subscriptions,
            'delivery_rate': round(delivery_rate, 2),
            'avg_delivery_time_seconds': avg_delivery_time,
            'click_through_rate': round(click_through_rate, 2),
            'error_rate': round(error_rate, 2)
        }
        
        return jsonify(metrics), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_notification_api.route('/api/admin/notifications/stats/timeline', methods=['GET'])
@login_required
@admin_required
def get_notification_timeline_stats():
    """Get notification statistics over time (daily/weekly/monthly)"""
    try:
        # Get period from query params (default: daily)
        period = request.args.get('period', 'daily')  # daily, weekly, monthly
        days = request.args.get('days', 7, type=int)  # Number of days to look back
        
        since = datetime.utcnow() - timedelta(days=days)
        
        # Group by date
        if period == 'daily':
            date_format = '%Y-%m-%d'
            group_by = func.date(NotificationLog.sent_at)
        elif period == 'weekly':
            date_format = '%Y-W%W'
            group_by = func.strftime('%Y-W%W', NotificationLog.sent_at)
        else:  # monthly
            date_format = '%Y-%m'
            group_by = func.strftime('%Y-%m', NotificationLog.sent_at)
        
        # Query stats grouped by date
        results = db.session.query(
            group_by.label('date'),
            func.count(NotificationLog.id).label('total'),
            func.sum(func.if_(NotificationLog.status == 'sent', 1, 0)).label('delivered'),
            func.sum(func.if_(NotificationLog.status == 'failed', 1, 0)).label('failed'),
            func.sum(func.if_(NotificationLog.clicked_at.isnot(None), 1, 0)).label('clicked')
        ).filter(
            NotificationLog.sent_at >= since
        ).group_by(group_by).order_by(group_by).all()
        
        timeline = []
        for row in results:
            total = row.total
            delivered = row.delivered
            failed = row.failed
            clicked = row.clicked
            
            timeline.append({
                'date': str(row.date),
                'total': total,
                'delivered': delivered,
                'failed': failed,
                'clicked': clicked,
                'delivery_rate': round((delivered / total * 100) if total > 0 else 0, 2),
                'click_through_rate': round((clicked / delivered * 100) if delivered > 0 else 0, 2)
            })
        
        return jsonify({
            'period': period,
            'days': days,
            'timeline': timeline
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_notification_api.route('/api/admin/notifications/background-jobs', methods=['GET'])
@login_required
@admin_required
def get_background_jobs_status():
    """Get status of background notification jobs"""
    try:
        from app.services.background_jobs import BackgroundJobsService
        
        status = BackgroundJobsService.get_job_status()
        
        # Add additional stats
        if status['status'] == 'running':
            # Count PENDING retries
            one_day_ago = datetime.utcnow() - timedelta(hours=24)
            PENDING_retries = NotificationLog.query.filter(
                NotificationLog.status == 'failed',
                NotificationLog.sent_at >= one_day_ago,
                NotificationLog.retry_count < 3
            ).count()
            
            # Count permanently failed
            permanently_failed = NotificationLog.query.filter(
                NotificationLog.status == 'permanently_failed'
            ).count()
            
            # Count old logs (> 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            old_logs = NotificationLog.query.filter(
                NotificationLog.sent_at < thirty_days_ago,
                NotificationLog.status != 'permanently_failed'
            ).count()
            
            status['stats'] = {
                'PENDING_retries': PENDING_retries,
                'permanently_failed': permanently_failed,
                'old_logs_to_cleanup': old_logs
            }
        
        return jsonify(status), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_notification_api.route('/api/notifications/log-batch', methods=['POST'])
def log_batch_notifications():
    """Batch logging endpoint for client-side notification events"""
    try:
        data = request.get_json()
        logs = data.get('logs', [])
        
        if not logs:
            return jsonify({'error': 'No logs provided'}), 400
        
        # Process each log entry
        for log_entry in logs:
            notification_id = log_entry.get('notification_id')
            status = log_entry.get('status')
            timestamp = log_entry.get('timestamp')
            
            if notification_id and status:
                # Find the notification log
                log = NotificationLog.query.get(notification_id)
                if log:
                    # Update status
                    if status == 'delivered' and not log.delivered_at:
                        log.status = 'delivered'
                        log.delivered_at = datetime.fromtimestamp(timestamp / 1000) if timestamp else datetime.utcnow()
                    elif status == 'clicked' and not log.clicked_at:
                        log.clicked_at = datetime.fromtimestamp(timestamp / 1000) if timestamp else datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'processed': len(logs)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Helper functions

def calculate_avg_delivery_time(since=None):
    """Calculate average delivery time in seconds"""
    query = NotificationLog.query.filter(
        NotificationLog.delivered_at.isnot(None)
    )
    
    if since:
        query = query.filter(NotificationLog.sent_at >= since)
    
    logs = query.all()
    
    if not logs:
        return 0
    
    total_time = sum([
        (log.delivered_at - log.sent_at).total_seconds()
        for log in logs
        if log.delivered_at and log.sent_at
    ])
    
    return round(total_time / len(logs), 2) if logs else 0


def get_stats_by_priority(since=None):
    """Get statistics grouped by priority"""
    query = db.session.query(
        NotificationLog.priority,
        func.count(NotificationLog.id).label('count'),
        func.sum(func.if_(NotificationLog.status == 'delivered', 1, 0)).label('delivered'),
        func.sum(func.if_(NotificationLog.status == 'failed', 1, 0)).label('failed')
    ).group_by(NotificationLog.priority)
    
    if since:
        query = query.filter(NotificationLog.sent_at >= since)
    
    results = query.all()
    
    stats = {}
    for row in results:
        priority = row.priority or 'normal'
        stats[priority] = {
            'total': row.count,
            'delivered': row.delivered,
            'failed': row.failed,
            'delivery_rate': round((row.delivered / row.count * 100) if row.count > 0 else 0, 2)
        }
    
    return stats


def get_stats_by_type(since=None):
    """Get statistics grouped by notification type"""
    query = db.session.query(
        NotificationLog.notification_type,
        func.count(NotificationLog.id).label('count'),
        func.sum(func.if_(NotificationLog.status == 'delivered', 1, 0)).label('delivered'),
        func.sum(func.if_(NotificationLog.status == 'failed', 1, 0)).label('failed')
    ).group_by(NotificationLog.notification_type)
    
    if since:
        query = query.filter(NotificationLog.sent_at >= since)
    
    results = query.all()
    
    stats = {}
    for row in results:
        stats[row.notification_type] = {
            'total': row.count,
            'delivered': row.delivered,
            'failed': row.failed,
            'delivery_rate': round((row.delivered / row.count * 100) if row.count > 0 else 0, 2)
        }
    
    return stats


def get_recent_failures(limit=10, since=None):
    """Get recent failed notifications"""
    query = NotificationLog.query.filter(
        NotificationLog.status == 'failed'
    )
    
    if since:
        query = query.filter(NotificationLog.sent_at >= since)
    
    failures = query.order_by(NotificationLog.sent_at.desc()).limit(limit).all()
    
    return [
        {
            'id': f.id,
            'user_id': f.user_id,
            'notification_type': f.notification_type,
            'priority': f.priority,
            'title': f.title,
            'error_message': f.error_message,
            'sent_at': f.sent_at.isoformat(),
            'retry_count': f.retry_count
        }
        for f in failures
    ]


def calculate_error_rate(since=None):
    """Calculate error rate percentage"""
    query_total = NotificationLog.query
    query_failed = NotificationLog.query.filter(NotificationLog.status == 'failed')
    
    if since:
        query_total = query_total.filter(NotificationLog.sent_at >= since)
        query_failed = query_failed.filter(NotificationLog.sent_at >= since)
    
    total = query_total.count()
    failed = query_failed.count()
    
    return (failed / total * 100) if total > 0 else 0


def get_fcm_stats(since=None):
    """Get FCM specific statistics"""
    # FCM token stats
    total_fcm_tokens = SystemUser.query.filter(
        SystemUser.fcm_token.isnot(None)
    ).count()
    
    # Active FCM tokens (updated in last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    active_fcm_tokens = SystemUser.query.filter(
        SystemUser.fcm_token.isnot(None),
        SystemUser.fcm_token_date >= seven_days_ago
    ).count()
    
    # FCM notifications sent
    query = NotificationLog.query.filter(
        NotificationLog.notification_type == 'fcm'
    )
    
    if since:
        query = query.filter(NotificationLog.sent_at >= since)
    
    fcm_sent = query.count()
    fcm_delivered = query.filter(NotificationLog.status == 'sent').count()
    fcm_failed = query.filter(NotificationLog.status == 'failed').count()
    
    # FCM delivery rate
    fcm_delivery_rate = (fcm_delivered / fcm_sent * 100) if fcm_sent > 0 else 0
    
    # FCM by priority
    fcm_by_priority = {}
    for priority in ['high', 'normal', 'low']:
        count = query.filter(NotificationLog.priority == priority).count()
        if count > 0:
            fcm_by_priority[priority] = count
    
    # Driver vs Guest tokens
    driver_tokens = SystemUser.query.filter(
        SystemUser.fcm_token.isnot(None),
        SystemUser.role == 'driver'
    ).count()
    
    guest_tokens_count = db.session.execute(
        db.text("SELECT COUNT(DISTINCT request_id) FROM guest_fcm_tokens")
    ).scalar() if db.engine.dialect.has_table(db.engine, 'guest_fcm_tokens') else 0
    
    return {
        'total_tokens': total_fcm_tokens,
        'active_tokens': active_fcm_tokens,
        'driver_tokens': driver_tokens,
        'guest_tokens': guest_tokens_count,
        'notifications_sent': fcm_sent,
        'notifications_delivered': fcm_delivered,
        'notifications_failed': fcm_failed,
        'delivery_rate': round(fcm_delivery_rate, 2),
        'by_priority': fcm_by_priority
    }
