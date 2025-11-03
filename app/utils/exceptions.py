"""
Buggy Call - Custom Exceptions
"""


class BuggyCallException(Exception):
    """Base exception for Buggy Call application"""
    status_code = 400
    
    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        rv['success'] = False
        return rv


class ValidationException(BuggyCallException):
    """Exception for validation errors"""
    status_code = 400


class ResourceNotFoundException(BuggyCallException):
    """Exception for resource not found"""
    status_code = 404
    
    def __init__(self, resource_type='Resource', resource_id=None):
        message = f"{resource_type} not found"
        if resource_id:
            message = f"{resource_type} with ID {resource_id} not found"
        super().__init__(message, status_code=404)


class UnauthorizedException(BuggyCallException):
    """Exception for unauthorized access"""
    status_code = 401
    
    def __init__(self, message='Unauthorized'):
        super().__init__(message, status_code=401)


class ForbiddenException(BuggyCallException):
    """Exception for forbidden access"""
    status_code = 403
    
    def __init__(self, message='Forbidden'):
        super().__init__(message, status_code=403)


class ConflictException(BuggyCallException):
    """Exception for resource conflicts"""
    status_code = 409
    
    def __init__(self, message='Resource conflict'):
        super().__init__(message, status_code=409)


class BusinessLogicException(BuggyCallException):
    """Exception for business logic violations"""
    status_code = 422
    
    def __init__(self, message):
        super().__init__(message, status_code=422)
