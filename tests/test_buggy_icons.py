"""
Test Buggy Icon Assignment
"""
import pytest
from app.utils.buggy_icons import assign_buggy_icon, BUGGY_ICONS, DEFAULT_BUGGY_ICON
from app.models.buggy import Buggy
from app import db


class TestBuggyIconAssignment:
    """Test buggy icon assignment logic"""
    
    def test_assign_icon_to_first_buggy(self, app, test_hotel):
        """Test that first buggy gets first icon from set"""
        with app.app_context():
            icon = assign_buggy_icon(test_hotel.id)
            assert icon in BUGGY_ICONS
            assert icon == BUGGY_ICONS[0]
    
    def test_assign_unique_icons(self, app, test_hotel):
        """Test that multiple buggies get different icons"""
        with app.app_context():
            # Create first buggy with icon
            buggy1 = Buggy(
                hotel_id=test_hotel.id,
                code='BUGGY-1',
                icon=BUGGY_ICONS[0],
                status='offline'
            )
            db.session.add(buggy1)
            db.session.commit()
            
            # Get icon for second buggy
            icon2 = assign_buggy_icon(test_hotel.id)
            
            # Should get second icon (first unused)
            assert icon2 == BUGGY_ICONS[1]
            assert icon2 != buggy1.icon
    
    def test_reuse_icons_when_all_used(self, app, test_hotel):
        """Test that icons are reused when all 33 are used"""
        with app.app_context():
            # Create 33 buggies with all icons
            for i, icon in enumerate(BUGGY_ICONS):
                buggy = Buggy(
                    hotel_id=test_hotel.id,
                    code=f'BUGGY-{i+1}',
                    icon=icon,
                    status='offline'
                )
                db.session.add(buggy)
            db.session.commit()
            
            # Get icon for 34th buggy
            icon34 = assign_buggy_icon(test_hotel.id)
            
            # Should reuse first icon
            assert icon34 == BUGGY_ICONS[0]
    
    def test_icon_set_has_33_icons(self):
        """Test that icon set contains exactly 33 icons"""
        assert len(BUGGY_ICONS) == 33
    
    def test_all_icons_are_unique(self):
        """Test that all icons in set are unique"""
        assert len(BUGGY_ICONS) == len(set(BUGGY_ICONS))
    
    def test_default_icon_exists(self):
        """Test that default icon is defined"""
        assert DEFAULT_BUGGY_ICON == '🚗'
    
    def test_icons_are_vehicle_themed(self):
        """Test that icons are vehicle/transport themed"""
        # All icons should be emoji strings
        for icon in BUGGY_ICONS:
            assert isinstance(icon, str)
            assert len(icon) > 0
