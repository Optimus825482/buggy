"""
Buggy Call - Background Jobs Service
Scheduled tasks for notification retry, cleanup, and maintenance
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from app import db
from app.models.notification_log import NotificationLog
from app.models.user import SystemUser
# FCM servisi kullanılacak (eski notification_service kaldırıldı)
# from app.services.notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)


class BackgroundJobsService:
    """Service for managing background scheduled jobs"""
    
    scheduler = None
    
    @staticmethod
    def init_scheduler(app):
        """Initialize the background scheduler"""
        if BackgroundJobsService.scheduler is not None:
            return BackgroundJobsService.scheduler
        
        BackgroundJobsService.scheduler = BackgroundScheduler(
            daemon=True,
            timezone='UTC'
        )
        
        # Add jobs
        BackgroundJobsService._add_jobs()
        
        # Start scheduler
        BackgroundJobsService.scheduler.start()
        logger.info("Background scheduler started successfully")
        
        return BackgroundJobsService.scheduler
    
    @staticmethod
    def _add_jobs():
        """Add all scheduled jobs"""
        
        # Job 1: Retry failed notifications every 5 minutes
        BackgroundJobsService.scheduler.add_job(
            func=BackgroundJobsService.retry_failed_notifications,
            trigger=IntervalTrigger(minutes=5),
            id='retry_failed_notifications',
            name='Retry Failed Notifications',
            replace_existing=True
        )
        
        # Job 2: Cleanup old logs daily at 2 AM
        BackgroundJobsService.scheduler.add_job(
            func=BackgroundJobsService.cleanup_old_logs,
            trigger=CronTrigger(hour=2, minute=0),
            id='cleanup_old_logs',
            name='Cleanup Old Notification Logs',
            replace_existing=True
        )
        
        # Job 3: Mark permanently failed notifications every hour
        BackgroundJobsService.scheduler.add_job(
            func=BackgroundJobsService.mark_permanently_failed,
            trigger=IntervalTrigger(hours=1),
            id='mark_permanently_failed',
            name='Mark Permanently Failed Notifications',
            replace_existing=True
        )
        
        # Job 4: Check and timeout unanswered requests every 10 minutes
        BackgroundJobsService.scheduler.add_job(
            func=BackgroundJobsService.check_request_timeouts,
            trigger=IntervalTrigger(minutes=10),
            id='check_request_timeouts',
            name='Check Request Timeouts (1 hour)',
            replace_existing=True
        )
        
        logger.info("All background jobs added to scheduler")
    
    @staticmethod
    def retry_failed_notifications():
        """
        Retry failed notifications with exponential backoff
        
        Logic:
        - Retry notifications that failed in last 24 hours
        - Use exponential backoff: 30s, 60s, 120s, 300s (max 5 min)
        - Max 3 retry attempts
        - Mark as permanently_failed after 3 attempts
        """
        try:
            from app import create_app
            app = create_app()
            
            # ✅ CRITICAL: Ensure proper session cleanup in background job
            with app.app_context():
                logger.info("Starting retry_failed_notifications job")

                # Get failed notifications from last 24 hours with retry count < 3
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                failed_notifications = NotificationLog.query.filter(
                    NotificationLog.status == 'failed',
                    NotificationLog.sent_at >= cutoff_time,
                    NotificationLog.retry_count < 3
                ).all()

                if not failed_notifications:
                    logger.info("No failed notifications to retry")
                    return

                logger.info(f"Found {len(failed_notifications)} failed notifications to process")

                retry_count = 0
                success_count = 0

                for log in failed_notifications:
                    try:
                        # Calculate exponential backoff delay
                        # retry_count 0: 30s, 1: 60s, 2: 120s, 3: 300s
                        delay_seconds = min(300, 30 * (2 ** log.retry_count))

                        # Check if enough time has passed since last attempt
                        time_since_sent = (datetime.utcnow() - log.sent_at).total_seconds()

                        if time_since_sent < delay_seconds:
                            logger.debug(f"Notification {log.id} not ready for retry (waiting {delay_seconds}s)")
                            continue

                        # Get user and check if subscription still exists
                        user = SystemUser.query.get(log.user_id)
                        if not user:
                            logger.warning(f"User {log.user_id} not found for notification {log.id}")
                            log.status = 'permanently_failed'
                            log.error_message = 'User not found'
                            db.session.commit()
                            continue

                        if not user.fcm_token:
                            logger.warning(f"User {log.user_id} has no FCM token")
                            log.status = 'permanently_failed'
                            log.error_message = 'No FCM token'
                            db.session.commit()
                            continue

                        # Retry sending notification (FCM)
                        logger.info(f"Retrying notification {log.id} (attempt {log.retry_count + 1}/3)")

                        # FCM ile retry
                        from app.services.fcm_notification_service import FCMNotificationService

                        if user.fcm_token:
                            success = FCMNotificationService.send_to_token(
                                token=user.fcm_token,
                                title=log.title,
                                body=log.body,
                                data={'user_id': user.id, 'retry': True, 'type': log.notification_type},
                                priority=log.priority
                            )
                        else:
                            logger.warning(f"User {log.user_id} has no FCM token")
                            success = False

                        # Update log based on result
                        log.retry_count += 1

                        if success:
                            log.status = 'sent'
                            log.error_message = None
                            success_count += 1
                            logger.info(f"Successfully retried notification {log.id}")
                        else:
                            if log.retry_count >= 3:
                                log.status = 'permanently_failed'
                                logger.warning(f"Notification {log.id} permanently failed after 3 attempts")
                            else:
                                logger.warning(f"Retry failed for notification {log.id}, will retry again")

                        db.session.commit()
                        retry_count += 1

                    except Exception as e:
                        logger.error(f"Error retrying notification {log.id}: {str(e)}")
                        db.session.rollback()
                        continue

                logger.info(f"Retry job completed: {retry_count} retried, {success_count} successful")
            
        except Exception as e:
            logger.error(f"Error in retry_failed_notifications job: {str(e)}")
            try:
                db.session.rollback()
            except:
                pass
    
    @staticmethod
    def mark_permanently_failed():
        """
        Mark notifications as permanently failed if they've exceeded retry limits
        
        Logic:
        - Find failed notifications older than 24 hours
        - Mark as permanently_failed if retry_count >= 3
        """
        try:
            from app import create_app
            app = create_app()
            
            # ✅ CRITICAL: Ensure proper session cleanup in background job
            with app.app_context():
                logger.info("Starting mark_permanently_failed job")
                
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            # Find old failed notifications with max retries
            old_failed = NotificationLog.query.filter(
                NotificationLog.status == 'failed',
                NotificationLog.sent_at < cutoff_time,
                NotificationLog.retry_count >= 3
            ).all()
            
            if not old_failed:
                logger.info("No notifications to mark as permanently failed")
                return
                
                logger.info(f"Marking {len(old_failed)} notifications as permanently failed")
                
                for log in old_failed:
                    log.status = 'permanently_failed'
                    if not log.error_message:
                        log.error_message = 'Max retry attempts exceeded'
                
                db.session.commit()
                logger.info(f"Marked {len(old_failed)} notifications as permanently failed")
            
        except Exception as e:
            logger.error(f"Error in mark_permanently_failed job: {str(e)}")
            try:
                db.session.rollback()
            except:
                pass
    
    @staticmethod
    def cleanup_old_logs(days=30):
        """
        Cleanup notification logs older than specified days
        
        Args:
            days: Number of days to keep logs (default: 30)
        
        Logic:
        - Delete logs older than 30 days
        - Keep permanently_failed logs for audit purposes
        """
        try:
            from app import create_app
            app = create_app()
            
            # ✅ CRITICAL: Ensure proper session cleanup in background job
            with app.app_context():
                logger.info(f"Starting cleanup_old_logs job (keeping last {days} days)")
                
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # Delete old logs except permanently_failed ones
                deleted_count = NotificationLog.query.filter(
                    NotificationLog.sent_at < cutoff_date,
                    NotificationLog.status != 'permanently_failed'
                ).delete(synchronize_session=False)
                
                db.session.commit()
                
                logger.info(f"Cleanup completed: {deleted_count} old logs deleted")
                
                # Also cleanup very old permanently_failed logs (90 days)
                very_old_cutoff = datetime.utcnow() - timedelta(days=90)
                very_old_deleted = NotificationLog.query.filter(
                    NotificationLog.sent_at < very_old_cutoff,
                    NotificationLog.status == 'permanently_failed'
                ).delete(synchronize_session=False)
                
                db.session.commit()
                
                if very_old_deleted > 0:
                    logger.info(f"Cleanup completed: {very_old_deleted} very old permanently_failed logs deleted")
            
        except Exception as e:
            logger.error(f"Error in cleanup_old_logs job: {str(e)}")
            try:
                db.session.rollback()
            except:
                pass
    
    @staticmethod
    def check_request_timeouts():
        """
        Check for PENDING requests older than 1 hour and mark as unanswered
        
        Logic:
        - Find PENDING requests older than 1 hour
        - Mark as UNANSWERED status
        - Record timeout timestamp
        - Calculate response time
        """
        try:
            from app import create_app
            app = create_app()
            
            with app.app_context():
                logger.info("Starting check_request_timeouts job")
                
                from app.tasks.timeout_checker import check_and_timeout_requests
                
                timeout_count = check_and_timeout_requests()
                
                if timeout_count > 0:
                    logger.info(f"✅ Timeout check completed: {timeout_count} request(s) marked as unanswered")
                else:
                    logger.info("No requests timed out")
            
        except Exception as e:
            logger.error(f"Error in check_request_timeouts job: {str(e)}")
            try:
                db.session.rollback()
            except:
                pass
    
    @staticmethod
    def shutdown_scheduler():
        """Shutdown the scheduler gracefully"""
        if BackgroundJobsService.scheduler:
            BackgroundJobsService.scheduler.shutdown(wait=True)
            logger.info("Background scheduler shut down")
    
    @staticmethod
    def get_job_status():
        """Get status of all scheduled jobs"""
        if not BackgroundJobsService.scheduler:
            return {'status': 'not_initialized'}
        
        jobs = BackgroundJobsService.scheduler.get_jobs()
        
        return {
            'status': 'running' if BackgroundJobsService.scheduler.running else 'stopped',
            'jobs': [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                }
                for job in jobs
            ]
        }
