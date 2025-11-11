"""
Buggy Call - Authentication Service
"""
from app import db
from app.models.user import SystemUser, UserRole
from app.models.hotel import Hotel
from app.services.audit_service import AuditService
from app.utils.exceptions import UnauthorizedException, ResourceNotFoundException, ValidationException
from datetime import datetime
from flask import session


class AuthService:
    """Service for authentication operations"""
    
    @staticmethod
    def login(username, password):
        """
        Authenticate user and create session
        
        Args:
            username: Username
            password: Password
        
        Returns:
            User object
        
        Raises:
            UnauthorizedException: If credentials are invalid
        """
        # Find user
        user = SystemUser.query.filter_by(username=username).first()
        
        if not user:
            # Log failed attempt
            AuditService.log_action(
                action='login_failed',
                entity_type='user',
                entity_id=None,
                new_values={'username': username, 'reason': 'user_not_found'}
            )
            
            # Track failed login for brute force detection
            from app.middleware.suspicious_activity import track_failed_login
            from flask import request
            track_failed_login(username, request.remote_addr if request else 'unknown')
            
            raise UnauthorizedException('Geçersiz kullanıcı adı veya şifre')
        
        # Check password
        if not user.check_password(password):
            # Log failed attempt
            AuditService.log_login(user.id, user.hotel_id, success=False)
            
            # Track failed login for brute force detection
            from app.middleware.suspicious_activity import track_failed_login
            from flask import request
            track_failed_login(username, request.remote_addr if request else 'unknown')
            
            raise UnauthorizedException('Geçersiz kullanıcı adı veya şifre')
        
        # Check if user is active
        if not user.is_active:
            raise UnauthorizedException('Hesabınız aktif değil. Lütfen yöneticinizle iletişime geçin.')
        
        # Update last login
        user.last_login = datetime.utcnow()
        
        # Create session
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role.value if hasattr(user.role, 'value') else str(user.role)
        session['hotel_id'] = user.hotel_id
        
        # Initialize notification permission tracking
        session['notification_permission_asked'] = False
        session['notification_permission_status'] = 'default'
        
        # Import models for driver-specific logic
        from app.models.buggy import Buggy, BuggyStatus
        from app.models.buggy_driver import BuggyDriver
        
        # For drivers: Make session expire when browser closes
        # For admins: Keep 24-hour session (from config)
        if user.role == UserRole.DRIVER:
            session.permanent = False  # Session expires when browser closes
            print(f'[LOGIN] Driver session set to non-permanent (expires on browser close)')
        else:
            session.permanent = True  # Use PERMANENT_SESSION_LIFETIME from config
            print(f'[LOGIN] Admin session set to permanent (24 hours)')
        
        # For drivers: Check if they need to set initial location
        
        if user.role == UserRole.DRIVER:
            # Get all buggies assigned to this driver
            driver_associations = BuggyDriver.query.filter_by(driver_id=user.id).all()
            
            for assoc in driver_associations:
                buggy = Buggy.query.get(assoc.buggy_id)
                if not buggy:
                    continue
                
                # Deactivate all other drivers on this buggy
                other_drivers = BuggyDriver.query.filter(
                    BuggyDriver.buggy_id == buggy.id,
                    BuggyDriver.driver_id != user.id,
                    BuggyDriver.is_active == True
                ).all()
                
                for other_assoc in other_drivers:
                    other_assoc.is_active = False
                    # Emit WebSocket event for other driver logout
                    try:
                        from app import socketio
                        socketio.emit('driver_logged_out', {
                            'buggy_id': buggy.id,
                            'buggy_code': buggy.code,
                            'driver_id': other_assoc.driver_id
                        }, room=f'hotel_{user.hotel_id}_admin')
                    except:
                        pass
                
                # Activate this driver on this buggy
                assoc.is_active = True
                assoc.last_active_at = datetime.utcnow()
                
                # Driver must always select location on login
                # (location is cleared on logout/disconnect)
                session['needs_location_setup'] = True
                # Buggy stays offline until location is set
                
                # Emit WebSocket event for driver login
                try:
                    from app import socketio
                    socketio.emit('driver_logged_in', {
                        'buggy_id': buggy.id,
                        'buggy_code': buggy.code,
                        'driver_id': user.id,
                        'driver_name': user.full_name if user.full_name else user.username,
                        'status': buggy.status.value
                    }, room=f'hotel_{user.hotel_id}_admin')
                except:
                    pass
                
                # Emit buggy status update for real-time dashboard
                try:
                    from app.services.buggy_service import BuggyService
                    BuggyService.emit_buggy_status_update(buggy.id, user.hotel_id)
                except:
                    pass
        
        db.session.commit()
        
        # Log successful login
        AuditService.log_login(user.id, user.hotel_id, success=True)
        
        return user
    
    @staticmethod
    def logout():
        """
        ✅ PERFORMANS OPTİMİZE: Hızlı logout - ağır işlemler async
        Kullanıcı anında çıkış yapar, cleanup background'da olur
        """
        user_id = session.get('user_id')
        hotel_id = session.get('hotel_id')
        
        print(f'[LOGOUT] Starting logout for user_id={user_id}, hotel_id={hotel_id}')
        
        # ✅ Session'ı hemen temizle (kullanıcı beklemez)
        session.clear()
        
        # ✅ User cache'ini temizle
        if user_id:
            try:
                from app.utils.decorators import invalidate_user_cache
                invalidate_user_cache(user_id)
            except:
                pass
        
        # ✅ Ağır işlemleri background'da yap
        if user_id and hotel_id:
            from threading import Thread
            Thread(target=AuthService._cleanup_driver_session, 
                   args=(user_id, hotel_id), 
                   daemon=True).start()
        
        print(f'[LOGOUT] Session cleared, cleanup started in background')
    
    @staticmethod
    def _cleanup_driver_session(user_id, hotel_id):
        """
        Background'da driver cleanup işlemleri
        Bu fonksiyon async çalışır, kullanıcı beklemez
        """
        try:
            from app import create_app
            app = create_app()
            
            with app.app_context():
                user = SystemUser.query.get(user_id)
                if not user or user.role != UserRole.DRIVER:
                    print(f'[LOGOUT_CLEANUP] User {user_id} is not a driver, skipping')
                    return
                
                print(f'[LOGOUT_CLEANUP] Processing driver cleanup: {user.username}')
                
                from app.models.buggy import Buggy, BuggyStatus
                from app.models.buggy_driver import BuggyDriver
                
                # Get all active associations for this driver
                active_associations = BuggyDriver.query.filter_by(
                    driver_id=user_id,
                    is_active=True
                ).all()
                
                print(f'[LOGOUT_CLEANUP] Found {len(active_associations)} active buggy associations')
                
                for assoc in active_associations:
                    # Deactivate driver
                    assoc.is_active = False
                    print(f'[LOGOUT_CLEANUP] Deactivated association for buggy_id={assoc.buggy_id}')
                    
                    # Set buggy to offline and clear location
                    buggy = Buggy.query.get(assoc.buggy_id)
                    if buggy:
                        old_status = buggy.status
                        buggy.status = BuggyStatus.OFFLINE
                        buggy.current_location_id = None  # Clear location on logout
                        print(f'[LOGOUT_CLEANUP] Set buggy {buggy.code} status from {old_status} to OFFLINE')
                        
                        # Emit WebSocket event for driver logout
                        try:
                            from app import socketio
                            socketio.emit('buggy_status_changed', {
                                'buggy_id': buggy.id,
                                'buggy_code': buggy.code,
                                'buggy_icon': buggy.icon,
                                'driver_id': None,
                                'driver_name': None,
                                'location_name': None,
                                'status': 'offline',
                                'reason': 'driver_logout'
                            }, room=f'hotel_{hotel_id}_admin')
                            print(f'[LOGOUT_CLEANUP] Emitted buggy_status_changed event')
                        except Exception as e:
                            print(f'[LOGOUT_CLEANUP] Error emitting buggy_status_changed: {e}')
                        
                        # Emit buggy status update
                        try:
                            from app.services.buggy_service import BuggyService
                            BuggyService.emit_buggy_status_update(buggy.id, hotel_id)
                        except Exception as e:
                            print(f'[LOGOUT_CLEANUP] Error emitting buggy status: {e}')
                
                db.session.commit()
                print(f'[LOGOUT_CLEANUP] Database changes committed')
                
                # Log logout
                AuditService.log_logout(user_id, hotel_id)
                print(f'[LOGOUT_CLEANUP] Cleanup completed for user {user_id}')
                
        except Exception as e:
            print(f'[LOGOUT_CLEANUP] Error in cleanup: {str(e)}')
            import traceback
            traceback.print_exc()
            try:
                db.session.rollback()
            except:
                pass
    
    @staticmethod
    def change_password(user_id, current_password, new_password):
        """
        Change user password
        
        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password
        
        Raises:
            ResourceNotFoundException: If user not found
            UnauthorizedException: If current password is wrong
        """
        user = SystemUser.query.get(user_id)
        if not user:
            raise ResourceNotFoundException('User', user_id)
        
        # Verify current password
        if not user.check_password(current_password):
            raise UnauthorizedException('Mevcut şifre yanlış')
        
        # Set new password
        old_hash = user.password_hash
        user.set_password(new_password)
        db.session.commit()
        
        # ✅ Cache'i temizle (şifre değişti)
        try:
            from app.utils.decorators import invalidate_user_cache
            invalidate_user_cache(user_id)
        except:
            pass
        
        # Log password change
        AuditService.log_action(
            action='password_changed',
            entity_type='user',
            entity_id=user.id,
            old_values={'password_hash': old_hash[:20] + '...'},
            new_values={'password_hash': user.password_hash[:20] + '...'},
            user_id=user.id,
            hotel_id=user.hotel_id
        )
    
    @staticmethod
    def create_user(hotel_id, username, password, role, full_name, email=None, phone=None):
        """
        Create new user
        
        Args:
            hotel_id: Hotel ID
            username: Username (unique)
            password: Password
            role: User role ('admin' or 'driver')
            full_name: Full name
            email: Email (optional)
            phone: Phone (optional)
        
        Returns:
            Created user
        
        Raises:
            ValidationException: If username already exists
            ResourceNotFoundException: If hotel not found
        """
        # Check if hotel exists
        hotel = Hotel.query.get(hotel_id)
        if not hotel:
            raise ResourceNotFoundException('Hotel', hotel_id)
        
        # Check if username already exists
        existing_user = SystemUser.query.filter_by(username=username).first()
        if existing_user:
            raise ValidationException(f'Kullanıcı adı "{username}" zaten kullanılıyor')
        
        # Create user
        user = SystemUser(
            hotel_id=hotel_id,
            username=username,
            role=UserRole[role.upper()],
            full_name=full_name,
            email=email,
            phone=phone,
            is_active=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Log user creation
        AuditService.log_create(
            entity_type='user',
            entity_id=user.id,
            new_values=user.to_dict(),
            hotel_id=hotel_id
        )
        
        return user
    
    @staticmethod
    def update_user(user_id, **kwargs):
        """
        Update user information
        
        Args:
            user_id: User ID
            **kwargs: Fields to update
        
        Returns:
            Updated user
        
        Raises:
            ResourceNotFoundException: If user not found
        """
        user = SystemUser.query.get(user_id)
        if not user:
            raise ResourceNotFoundException('User', user_id)
        
        # Store old values for audit
        old_values = user.to_dict()
        
        # Update allowed fields
        allowed_fields = ['full_name', 'email', 'phone', 'is_active']
        for field in allowed_fields:
            if field in kwargs:
                setattr(user, field, kwargs[field])
        
        db.session.commit()
        
        # ✅ Cache'i temizle (user güncellendi)
        try:
            from app.utils.decorators import invalidate_user_cache
            invalidate_user_cache(user_id)
        except:
            pass
        
        # Log update
        AuditService.log_update(
            entity_type='user',
            entity_id=user.id,
            old_values=old_values,
            new_values=user.to_dict(),
            hotel_id=user.hotel_id
        )
        
        return user
    
    @staticmethod
    def get_current_user():
        """Get current logged-in user"""
        user_id = session.get('user_id')
        if user_id:
            return SystemUser.query.get(user_id)
        return None
    
    @staticmethod
    def require_role(*roles):
        """
        Check if current user has required role
        
        Args:
            *roles: Required roles
        
        Raises:
            UnauthorizedException: If not logged in
            ForbiddenException: If role not allowed
        """
        from app.utils.exceptions import ForbiddenException
        
        if 'role' not in session:
            raise UnauthorizedException('Giriş yapmanız gerekiyor')
        
        user_role = session.get('role')
        if user_role not in roles:
            raise ForbiddenException('Bu işlem için yetkiniz yok')
