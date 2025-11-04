"""
Buggy Call - Audit Trail Routes
"""
from flask import Blueprint, jsonify, request, session
# from app import limiter  # Rate limiter removed
from app.services.audit_service import AuditService
from app.utils import APIResponse, require_login, require_role
from app.utils.exceptions import BuggyCallException
from datetime import datetime

audit_bp = Blueprint('audit', __name__)


@audit_bp.route('/audit', methods=['GET'])
# Rate limiter removed
@require_login
@require_role('admin')
def get_audit_trail():
    """Get audit trail (Admin only)"""
    try:
        from app.utils.helpers import RequestContext
        hotel_id = RequestContext.get_current_hotel_id()
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Build filters
        filters = {}
        if request.args.get('user_id'):
            filters['user_id'] = request.args.get('user_id', type=int)
        if request.args.get('action'):
            filters['action'] = request.args.get('action')
        if request.args.get('entity_type'):
            filters['entity_type'] = request.args.get('entity_type')
        if request.args.get('date_from'):
            filters['date_from'] = datetime.fromisoformat(request.args.get('date_from'))
        if request.args.get('date_to'):
            filters['date_to'] = datetime.fromisoformat(request.args.get('date_to'))
        
        # Get audit trail
        result = AuditService.get_audit_trail(
            hotel_id=hotel_id,
            filters=filters,
            page=page,
            per_page=per_page
        )
        
        return APIResponse.success(result)
        
    except BuggyCallException as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        return APIResponse.error(str(e), 500)


@audit_bp.route('/audit/stats', methods=['GET'])
# Rate limiter removed
@require_login
@require_role('admin')
def get_audit_stats():
    """Get audit trail statistics (Admin only)"""
    try:
        from app.utils.helpers import RequestContext
        from app.models.audit import AuditTrail
        from sqlalchemy import func
        
        hotel_id = RequestContext.get_current_hotel_id()
        
        # Get action counts
        action_counts = db.session.query(
            AuditTrail.action,
            func.count(AuditTrail.id).label('count')
        ).filter_by(hotel_id=hotel_id).group_by(AuditTrail.action).all()
        
        # Get entity type counts
        entity_counts = db.session.query(
            AuditTrail.entity_type,
            func.count(AuditTrail.id).label('count')
        ).filter_by(hotel_id=hotel_id).group_by(AuditTrail.entity_type).all()
        
        # Get recent activity count (last 24 hours)
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_count = AuditTrail.query.filter(
            AuditTrail.hotel_id == hotel_id,
            AuditTrail.created_at >= yesterday
        ).count()
        
        return APIResponse.success({
            'action_counts': {action: count for action, count in action_counts},
            'entity_counts': {entity: count for entity, count in entity_counts},
            'recent_activity_count': recent_count,
            'total_entries': sum(count for _, count in action_counts)
        })
        
    except BuggyCallException as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        return APIResponse.error(str(e), 500)



@audit_bp.route('/audit/<int:audit_id>', methods=['DELETE'])
# Rate limiter removed
@require_login
def delete_audit_log(audit_id):
    """
    Attempt to delete audit log - ALWAYS DENIED
    
    Audit logs are immutable and cannot be deleted to maintain system integrity.
    This endpoint exists to log deletion attempts as suspicious activity.
    """
    try:
        from app.utils.helpers import RequestContext
        from app.models.audit import AuditTrail
        
        user_id = session.get('user_id')
        hotel_id = RequestContext.get_current_hotel_id()
        
        # Log the deletion attempt as suspicious activity
        AuditService.log_action(
            action='audit_deletion_attempt',
            entity_type='audit_trail',
            entity_id=audit_id,
            user_id=user_id,
            hotel_id=hotel_id
        )
        
        # Always deny deletion
        return jsonify({
            'error': 'Forbidden',
            'message': 'Audit logs are immutable and cannot be deleted. This attempt has been logged.',
            'code': 'AUDIT_LOG_IMMUTABLE'
        }), 403
        
    except Exception as e:
        return APIResponse.error(str(e), 500)


@audit_bp.route('/audit/<int:audit_id>', methods=['PUT', 'PATCH'])
# Rate limiter removed
@require_login
def update_audit_log(audit_id):
    """
    Attempt to update audit log - ALWAYS DENIED
    
    Audit logs are immutable and cannot be modified to maintain system integrity.
    This endpoint exists to log modification attempts as suspicious activity.
    """
    try:
        from app.utils.helpers import RequestContext
        
        user_id = session.get('user_id')
        hotel_id = RequestContext.get_current_hotel_id()
        
        # Log the modification attempt as suspicious activity
        AuditService.log_action(
            action='audit_modification_attempt',
            entity_type='audit_trail',
            entity_id=audit_id,
            user_id=user_id,
            hotel_id=hotel_id
        )
        
        # Always deny modification
        return jsonify({
            'error': 'Forbidden',
            'message': 'Audit logs are immutable and cannot be modified. This attempt has been logged.',
            'code': 'AUDIT_LOG_IMMUTABLE'
        }), 403
        
    except Exception as e:
        return APIResponse.error(str(e), 500)


@audit_bp.route('/audit/suspicious-activity', methods=['GET'])
# Rate limiter removed
@require_login
@require_role('admin')
def get_suspicious_activity():
    """Get suspicious activity logs (Admin only)"""
    try:
        from app.utils.helpers import RequestContext
        from app.models.audit import AuditTrail
        
        hotel_id = RequestContext.get_current_hotel_id()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Get suspicious activities
        suspicious_actions = [
            'audit_deletion_attempt',
            'audit_modification_attempt',
            'login_failed',
            'unauthorized_access_attempt',
            'suspicious_bulk_operation'
        ]
        
        query = AuditTrail.query.filter(
            AuditTrail.hotel_id == hotel_id,
            AuditTrail.action.in_(suspicious_actions)
        ).order_by(AuditTrail.created_at.desc())
        
        total = query.count()
        items = query.limit(per_page).offset((page - 1) * per_page).all()
        
        return APIResponse.success({
            'items': [item.to_dict() for item in items],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        })
        
    except BuggyCallException as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        return APIResponse.error(str(e), 500)
