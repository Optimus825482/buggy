"""Test enum status"""
from app import create_app, db
from app.models.request import BuggyRequest, RequestStatus

app = create_app()

with app.app_context():
    print('Testing enum...')
    
    # Get first request
    req = BuggyRequest.query.first()
    
    if req:
        print(f'Request ID: {req.id}')
        print(f'Status: {req.status}')
        print(f'Status type: {type(req.status)}')
        print(f'Status value: {req.status.value if hasattr(req.status, "value") else req.status}')
        print(f'Is enum: {isinstance(req.status, RequestStatus)}')
    else:
        print('No requests found')
    
    # Test enum values
    print('\nEnum values:')
    for status in RequestStatus:
        print(f'  {status.name} = {status.value}')
