"""
Buggy Call - Reports Routes
Powered by Erkan ERDEM
"""
from flask import Blueprint, jsonify, request, session
from functools import wraps
from datetime import datetime, timedelta
from app.models.user import SystemUser
from app.services.report_service import ReportService
from app.models.request import RequestStatus

reports_bp = Blueprint('reports', __name__)


def api_login_required(fn):
    """Decorator for API authentication"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized', 'message': 'Lütfen giriş yapın'}), 401
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    """Decorator to ensure user is admin"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        user = SystemUser.query.get(session['user_id'])
        if not user or user.role != 'admin':
            return jsonify({'error': 'Forbidden', 'message': 'Admin yetkisi gerekli'}), 403

        return fn(*args, **kwargs)
    return wrapper


# ==================== Daily Summary ====================
@reports_bp.route('/daily-summary', methods=['GET'])
@api_login_required
def get_daily_summary():
    """Get daily summary report"""
    try:
        user = SystemUser.query.get(session['user_id'])

        # Get date from query params (defaults to today)
        date_str = request.args.get('date')
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        else:
            date = datetime.utcnow()

        report = ReportService.get_daily_summary(user.hotel_id, date)

        return jsonify({
            'success': True,
            'report': report
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Buggy Performance ====================
@reports_bp.route('/buggy-performance', methods=['GET'])
@api_login_required
def get_buggy_performance():
    """Get buggy performance report"""
    try:
        user = SystemUser.query.get(session['user_id'])

        # Get optional parameters
        buggy_id = request.args.get('buggy_id', type=int)

        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        start_date = None
        end_date = None

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400

        report = ReportService.get_buggy_performance(
            user.hotel_id,
            buggy_id,
            start_date,
            end_date
        )

        return jsonify({
            'success': True,
            'report': report
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Location Analytics ====================
@reports_bp.route('/location-analytics', methods=['GET'])
@api_login_required
def get_location_analytics():
    """Get location analytics report"""
    try:
        user = SystemUser.query.get(session['user_id'])

        # Get optional date range
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        start_date = None
        end_date = None

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400

        report = ReportService.get_location_analytics(
            user.hotel_id,
            start_date,
            end_date
        )

        return jsonify({
            'success': True,
            'report': report
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Request Details ====================
@reports_bp.route('/request-details', methods=['GET'])
@api_login_required
def get_request_details():
    """Get detailed request list"""
    try:
        user = SystemUser.query.get(session['user_id'])

        # Get optional parameters
        status_str = request.args.get('status')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        limit = request.args.get('limit', 100, type=int)

        # Parse status
        status = None
        if status_str:
            try:
                status = RequestStatus(status_str)
            except ValueError:
                return jsonify({'error': f'Invalid status. Must be one of: {[s.value for s in RequestStatus]}'}), 400

        # Parse dates
        start_date = None
        end_date = None

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400

        report = ReportService.get_request_details(
            user.hotel_id,
            status,
            start_date,
            end_date,
            limit
        )

        return jsonify({
            'success': True,
            'total': len(report),
            'requests': report
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Dashboard Stats ====================
@reports_bp.route('/dashboard-stats', methods=['GET'])
@api_login_required
def get_dashboard_stats():
    """Get real-time dashboard statistics"""
    try:
        from app.models.buggy import Buggy, BuggyStatus
        from app.models.request import BuggyRequest, RequestStatus
        from sqlalchemy import func

        user = SystemUser.query.get(session['user_id'])
        hotel_id = user.hotel_id

        # Active buggies count
        active_buggies = Buggy.query.filter_by(
            hotel_id=hotel_id,
            status=BuggyStatus.AVAILABLE
        ).count()

        # Pending requests count
        pending_requests = BuggyRequest.query.filter_by(
            hotel_id=hotel_id,
            status=RequestStatus.PENDING
        ).count()

        # Today's completed requests
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_completed = BuggyRequest.query.filter(
            BuggyRequest.hotel_id == hotel_id,
            BuggyRequest.status == RequestStatus.COMPLETED,
            BuggyRequest.completed_at >= today_start
        ).count()

        # Average response time today
        today_requests = BuggyRequest.query.filter(
            BuggyRequest.hotel_id == hotel_id,
            BuggyRequest.status == RequestStatus.COMPLETED,
            BuggyRequest.requested_at >= today_start,
            BuggyRequest.accepted_at.isnot(None)
        ).all()

        avg_response_time = 0
        if today_requests:
            total_response = sum([
                (req.accepted_at - req.requested_at).total_seconds()
                for req in today_requests
            ])
            avg_response_time = round(total_response / len(today_requests) / 60, 2)  # in minutes

        return jsonify({
            'success': True,
            'stats': {
                'active_buggies': active_buggies,
                'pending_requests': pending_requests,
                'today_completed': today_completed,
                'avg_response_time_minutes': avg_response_time
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# ==================== Export to Excel ====================
@reports_bp.route('/export/excel/<report_type>', methods=['GET'])
@api_login_required
def export_excel(report_type):
    """Export report to Excel"""
    try:
        from flask import send_file
        from io import BytesIO
        
        user = SystemUser.query.get(session['user_id'])
        
        # Get report data based on type
        if report_type == 'daily-summary':
            date_str = request.args.get('date')
            date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.utcnow()
            report_data = ReportService.get_daily_summary(user.hotel_id, date)
            data = [report_data]  # Convert dict to list
            filename = f'daily_summary_{date.strftime("%Y%m%d")}.xlsx'
            
        elif report_type == 'buggy-performance':
            buggy_id = request.args.get('buggy_id', type=int)
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d') if request.args.get('start_date') else None
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d') if request.args.get('end_date') else None
            data = ReportService.get_buggy_performance(user.hotel_id, buggy_id, start_date, end_date)
            filename = 'buggy_performance.xlsx'
            
        elif report_type == 'location-analytics':
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d') if request.args.get('start_date') else None
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d') if request.args.get('end_date') else None
            data = ReportService.get_location_analytics(user.hotel_id, start_date, end_date)
            filename = 'location_analytics.xlsx'
            
        elif report_type == 'request-details':
            status_str = request.args.get('status')
            status = RequestStatus(status_str) if status_str else None
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d') if request.args.get('start_date') else None
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d') if request.args.get('end_date') else None
            limit = request.args.get('limit', 1000, type=int)
            data = ReportService.get_request_details(user.hotel_id, status, start_date, end_date, limit)
            filename = 'request_details.xlsx'
            
        else:
            return jsonify({'error': 'Invalid report type'}), 400
        
        # Export to Excel
        excel_bytes = ReportService.export_to_excel(data, filename, sheet_name=report_type.replace('-', ' ').title())
        
        # Log export operation
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='report_exported',
            entity_type='report',
            new_values={
                'report_type': report_type,
                'format': 'excel',
                'filename': filename,
                'record_count': len(data)
            },
            user_id=session.get('user_id'),
            hotel_id=user.hotel_id
        )
        
        return send_file(
            BytesIO(excel_bytes),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Export to PDF ====================
@reports_bp.route('/export/pdf/<report_type>', methods=['GET'])
@api_login_required
def export_pdf(report_type):
    """Export report to PDF"""
    try:
        from flask import send_file
        from io import BytesIO
        
        user = SystemUser.query.get(session['user_id'])
        
        # Get report data based on type
        if report_type == 'daily-summary':
            date_str = request.args.get('date')
            date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.utcnow()
            report_data = ReportService.get_daily_summary(user.hotel_id, date)
            data = [report_data]
            title = f'Daily Summary - {date.strftime("%Y-%m-%d")}'
            filename = f'daily_summary_{date.strftime("%Y%m%d")}.pdf'
            
        elif report_type == 'buggy-performance':
            buggy_id = request.args.get('buggy_id', type=int)
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d') if request.args.get('start_date') else None
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d') if request.args.get('end_date') else None
            data = ReportService.get_buggy_performance(user.hotel_id, buggy_id, start_date, end_date)
            title = 'Buggy Performance Report'
            filename = 'buggy_performance.pdf'
            
        elif report_type == 'location-analytics':
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d') if request.args.get('start_date') else None
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d') if request.args.get('end_date') else None
            data = ReportService.get_location_analytics(user.hotel_id, start_date, end_date)
            title = 'Location Analytics Report'
            filename = 'location_analytics.pdf'
            
        elif report_type == 'request-details':
            status_str = request.args.get('status')
            status = RequestStatus(status_str) if status_str else None
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d') if request.args.get('start_date') else None
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d') if request.args.get('end_date') else None
            limit = request.args.get('limit', 1000, type=int)
            data = ReportService.get_request_details(user.hotel_id, status, start_date, end_date, limit)
            title = 'Request Details Report'
            filename = 'request_details.pdf'
            
        else:
            return jsonify({'error': 'Invalid report type'}), 400
        
        # Export to PDF
        pdf_bytes = ReportService.export_to_pdf(data, title, filename)
        
        # Log export operation
        from app.services.audit_service import AuditService
        AuditService.log_action(
            action='report_exported',
            entity_type='report',
            new_values={
                'report_type': report_type,
                'format': 'pdf',
                'filename': filename,
                'record_count': len(data)
            },
            user_id=session.get('user_id'),
            hotel_id=user.hotel_id
        )
        
        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
