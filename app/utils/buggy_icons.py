"""
Buggy Call - Buggy Icon Management
Provides icon set and selection logic for buggy visual identification
"""
from app import db
from app.models.buggy import Buggy

# 33 araç/taşıt temalı emoji icon seti
BUGGY_ICONS = [
    '🏎', '🚁', '✈', '💺', '🚂', '🚊', '🚉', '🚞', '🚆', '🚄',
    '🚅', '🚈', '🚇', '🚝', '🚋', '🚃', '🚎', '🚌', '🚍', '🚙',
    '🚘', '🚗', '🚕', '🚖', '🚛', '🚚', '🚨', '🚓', '🚔', '🚒',
    '🚑', '🚐', '🚜'
]

# Default icon (kullanılacak fallback)
DEFAULT_BUGGY_ICON = '🚗'


def assign_buggy_icon(hotel_id):
    """
    Assign a unique icon to a new buggy
    
    Logic:
    1. Get all used icons for this hotel
    2. Find unused icons from BUGGY_ICONS
    3. If unused icons exist, pick first one
    4. If all used, pick first icon from set
    
    Args:
        hotel_id (int): Hotel ID to check for used icons
        
    Returns:
        str: Selected emoji icon
    """
    try:
        # Get used icons for this hotel
        used_icons = db.session.query(Buggy.icon)\
            .filter(Buggy.hotel_id == hotel_id, Buggy.icon.isnot(None))\
            .all()
        used_icons_set = {icon[0] for icon in used_icons if icon[0]}
        
        # Find unused icons
        unused_icons = [icon for icon in BUGGY_ICONS if icon not in used_icons_set]
        
        # Return unused or fallback to first icon
        if unused_icons:
            return unused_icons[0]
        else:
            # All icons used, return first one
            return BUGGY_ICONS[0]
            
    except Exception as e:
        # On error, return default icon
        print(f"Error assigning buggy icon: {e}")
        return DEFAULT_BUGGY_ICON
