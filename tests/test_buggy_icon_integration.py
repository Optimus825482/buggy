"""
Integration Test for Buggy Icon Feature
"""
import pytest
from app.models.buggy import Buggy
from app.utils.buggy_icons import BUGGY_ICONS
from app import db


class TestBuggyIconIntegration:
    """Integration tests for buggy icon feature"""
    
    def test_create_buggy_with_icon(self, app, test_hotel):
        """Test creating a buggy includes icon in to_dict()"""
        with app.app_context():
            buggy = Buggy(
                hotel_id=test_hotel.id,
                code='TEST-BUGGY',
                icon='🚗',
                status='offline'
            )
            db.session.add(buggy)
            db.session.commit()
            
            # Get buggy dict
            buggy_dict = buggy.to_dict()
            
            # Verify icon is included
            assert 'icon' in buggy_dict
            assert buggy_dict['icon'] == '🚗'
    
    def test_buggy_without_icon_returns_none(self, app, test_hotel):
        """Test that buggy without icon returns None in to_dict()"""
        with app.app_context():
            buggy = Buggy(
                hotel_id=test_hotel.id,
                code='NO-ICON-BUGGY',
                status='offline'
            )
            db.session.add(buggy)
            db.session.commit()
            
            buggy_dict = buggy.to_dict()
            
            # Icon should be None
            assert 'icon' in buggy_dict
            assert buggy_dict['icon'] is None
    
    def test_multiple_buggies_have_different_icons(self, app, test_hotel):
        """Test that multiple buggies can have different icons"""
        with app.app_context():
            buggies = []
            for i in range(5):
                buggy = Buggy(
                    hotel_id=test_hotel.id,
                    code=f'BUGGY-{i+1}',
                    icon=BUGGY_ICONS[i],
                    status='offline'
                )
                db.session.add(buggy)
                buggies.append(buggy)
            
            db.session.commit()
            
            # Verify all have different icons
            icons = [b.icon for b in buggies]
            assert len(icons) == len(set(icons))  # All unique
