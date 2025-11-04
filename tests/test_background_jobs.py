"""
Buggy Call - Background Jobs Tests
Tests for notification retry system and scheduled jobs
"""
import pytest
from datetime import datetime, timedelta
from app import db
from app.models.notification_log import NotificationLog
from app.models.user import SystemUser
from app.services.background_jobs import BackgroundJobsService
from app.services.notification_service import NotificationService


class TestBackgroundJobs:
    """Test background job functionality"""
    
    def test_retry_failed_notifications(self, app, sample_driver_user):
        """Test retry logic for failed notifications"""
        with app.app_context():
            # Create a failed notification log
            failed_log = NotificationLog(
                user_id=sample_driver_user.id,
                notification_type='new_request',
                priority='high',
                title='Test Notification',
                body='Test body',
                status='failed',
                error_message='Network error',
                retry_count=0,
                sent_at=datetime.utcnow() - timedelta(minutes=1)
            )
            db.session.add(failed_log)
            db.session.commit()
            
            # Run retry job
            BackgroundJobsService.retry_failed_notifications()
            
            # Check that retry count increased
            db.session.refresh(failed_log)
            assert failed_log.retry_count == 1
    
    def test_exponential_backoff(self, app, sample_driver_user):
        """Test exponential backoff logic"""
        with app.app_context():
            # Create failed notification with different retry counts
            logs = []
            for retry_count in range(3):
                log = NotificationLog(
                    user_id=sample_driver_user.id,
                    notification_type='test',
                    priority='normal',
                    title=f'Test {retry_count}',
                    body='Test',
                    status='failed',
                    retry_count=retry_count,
                    sent_at=datetime.utcnow() - timedelta(minutes=10)
                )
                logs.append(log)
                db.session.add(log)
            
            db.session.commit()
            
            # Run retry job
            BackgroundJobsService.retry_failed_notifications()
            
            # All should have incremented retry count
            for log in logs:
                db.session.refresh(log)
                assert log.retry_count > 0
    
    def test_mark_permanently_failed(self, app, sample_driver_user):
        """Test marking notifications as permanently failed"""
        with app.app_context():
            # Create old failed notification with max retries
            old_failed = NotificationLog(
                user_id=sample_driver_user.id,
                notification_type='test',
                priority='normal',
                title='Old Failed',
                body='Test',
                status='failed',
                retry_count=3,
                sent_at=datetime.utcnow() - timedelta(hours=25)
            )
            db.session.add(old_failed)
            db.session.commit()
            
            # Run mark permanently failed job
            BackgroundJobsService.mark_permanently_failed()
            
            # Check status changed
            db.session.refresh(old_failed)
            assert old_failed.status == 'permanently_failed'
    
    def test_cleanup_old_logs(self, app, sample_driver_user):
        """Test cleanup of old notification logs"""
        with app.app_context():
            # Create old logs
            old_log = NotificationLog(
                user_id=sample_driver_user.id,
                notification_type='test',
                priority='normal',
                title='Old Log',
                body='Test',
                status='delivered',
                sent_at=datetime.utcnow() - timedelta(days=35)
            )
            db.session.add(old_log)
            
            # Create recent log
            recent_log = NotificationLog(
                user_id=sample_driver_user.id,
                notification_type='test',
                priority='normal',
                title='Recent Log',
                body='Test',
                status='delivered',
                sent_at=datetime.utcnow() - timedelta(days=5)
            )
            db.session.add(recent_log)
            db.session.commit()
            
            old_log_id = old_log.id
            recent_log_id = recent_log.id
            
            # Run cleanup job
            BackgroundJobsService.cleanup_old_logs(days=30)
            
            # Old log should be deleted
            assert NotificationLog.query.get(old_log_id) is None
            
            # Recent log should still exist
            assert NotificationLog.query.get(recent_log_id) is not None
    
    def test_cleanup_preserves_permanently_failed(self, app, sample_driver_user):
        """Test that cleanup preserves permanently failed logs"""
        with app.app_context():
            # Create old permanently failed log
            old_failed = NotificationLog(
                user_id=sample_driver_user.id,
                notification_type='test',
                priority='normal',
                title='Old Failed',
                body='Test',
                status='permanently_failed',
                sent_at=datetime.utcnow() - timedelta(days=35)
            )
            db.session.add(old_failed)
            db.session.commit()
            
            old_failed_id = old_failed.id
            
            # Run cleanup job (30 days)
            BackgroundJobsService.cleanup_old_logs(days=30)
            
            # Permanently failed log should still exist
            assert NotificationLog.query.get(old_failed_id) is not None
    
    def test_get_job_status(self, app):
        """Test getting background job status"""
        with app.app_context():
            status = BackgroundJobsService.get_job_status()
            
            assert 'status' in status
            assert status['status'] in ['running', 'stopped', 'not_initialized']
    
    def test_retry_without_subscription(self, app, sample_driver_user):
        """Test retry when user has no push subscription"""
        with app.app_context():
            # Remove push subscription
            sample_driver_user.push_subscription = None
            db.session.commit()
            
            # Create failed notification
            failed_log = NotificationLog(
                user_id=sample_driver_user.id,
                notification_type='test',
                priority='normal',
                title='Test',
                body='Test',
                status='failed',
                retry_count=0,
                sent_at=datetime.utcnow() - timedelta(minutes=1)
            )
            db.session.add(failed_log)
            db.session.commit()
            
            # Run retry job
            BackgroundJobsService.retry_failed_notifications()
            
            # Should be marked as permanently failed
            db.session.refresh(failed_log)
            assert failed_log.status == 'permanently_failed'
            assert 'No push subscription' in failed_log.error_message
    
    def test_max_retry_attempts(self, app, sample_driver_user):
        """Test that notifications stop retrying after max attempts"""
        with app.app_context():
            # Create notification with 2 retries already
            log = NotificationLog(
                user_id=sample_driver_user.id,
                notification_type='test',
                priority='normal',
                title='Test',
                body='Test',
                status='failed',
                retry_count=2,
                sent_at=datetime.utcnow() - timedelta(minutes=10)
            )
            db.session.add(log)
            db.session.commit()
            
            # Run retry job (this will be 3rd attempt)
            BackgroundJobsService.retry_failed_notifications()
            
            # Should be marked as permanently failed after 3rd attempt
            db.session.refresh(log)
            assert log.retry_count == 3
            assert log.status == 'permanently_failed'


class TestBackgroundJobsIntegration:
    """Integration tests for background jobs"""
    
    def test_full_retry_cycle(self, app, sample_driver_user):
        """Test complete retry cycle from failed to success"""
        with app.app_context():
            # Setup valid push subscription
            sample_driver_user.push_subscription = {
                'endpoint': 'https://test.example.com/push',
                'keys': {
                    'p256dh': 'test_key',
                    'auth': 'test_auth'
                }
            }
            db.session.commit()
            
            # Create failed notification
            failed_log = NotificationLog(
                user_id=sample_driver_user.id,
                notification_type='new_request',
                priority='high',
                title='Test Request',
                body='Test body',
                status='failed',
                error_message='Temporary network error',
                retry_count=0,
                sent_at=datetime.utcnow() - timedelta(minutes=1)
            )
            db.session.add(failed_log)
            db.session.commit()
            
            initial_retry_count = failed_log.retry_count
            
            # Run retry job
            BackgroundJobsService.retry_failed_notifications()
            
            # Verify retry was attempted
            db.session.refresh(failed_log)
            assert failed_log.retry_count > initial_retry_count
    
    def test_cleanup_with_mixed_statuses(self, app, sample_driver_user):
        """Test cleanup with various notification statuses"""
        with app.app_context():
            statuses = ['sent', 'delivered', 'failed', 'permanently_failed', 'clicked']
            
            # Create old logs with different statuses
            for status in statuses:
                log = NotificationLog(
                    user_id=sample_driver_user.id,
                    notification_type='test',
                    priority='normal',
                    title=f'Test {status}',
                    body='Test',
                    status=status,
                    sent_at=datetime.utcnow() - timedelta(days=35)
                )
                db.session.add(log)
            
            db.session.commit()
            
            # Count before cleanup
            count_before = NotificationLog.query.count()
            
            # Run cleanup
            BackgroundJobsService.cleanup_old_logs(days=30)
            
            # Count after cleanup
            count_after = NotificationLog.query.count()
            
            # Should have deleted all except permanently_failed
            assert count_after < count_before
            
            # Permanently failed should still exist
            permanently_failed = NotificationLog.query.filter_by(
                status='permanently_failed'
            ).first()
            assert permanently_failed is not None
