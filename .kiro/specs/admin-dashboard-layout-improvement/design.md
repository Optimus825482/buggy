# Design Document

## Overview

Admin dashboard'un layout'unu yeniden düzenleyerek kullanıcı deneyimini iyileştiriyoruz. Öncelikli bilgiler (aktif talepler ve buggy durumu) üstte, özet istatistikler altta konumlandırılacak. Ayrıca her buggy için benzersiz icon sistemi eklenecek.

## Architecture

### Frontend Changes
- **Template**: `templates/admin/dashboard.html` - Layout sıralaması değiştirilecek
- **JavaScript**: `app/static/js/admin.js` - Buggy listesi render fonksiyonu güncellenecek
- **CSS**: Inline style'lar korunacak, responsive tasarım sağlanacak

### Backend Changes
- **Model**: `app/models/buggy.py` - `icon` field eklenecek
- **Migration**: Yeni `icon` column için migration oluşturulacak
- **Service**: Icon atama logic'i eklenecek

## Components and Interfaces

### 1. Database Schema Changes

**Buggy Model'e Yeni Field:**
```python
# app/models/buggy.py
icon = Column(String(10), nullable=True)  # Emoji/icon storage
```

**Migration:**
```python
# migrations/versions/add_buggy_icon.py
def upgrade():
    op.add_column('buggies', sa.Column('icon', sa.String(10), nullable=True))

def downgrade():
    op.drop_column('buggies', 'icon')
```

### 2. Icon Selection Service

**Icon Set:**
```python
BUGGY_ICONS = [
    '🏎', '🚁', '✈', '💺', '🚂', '🚊', '🚉', '🚞', '🚆', '🚄',
    '🚅', '🚈', '🚇', '🚝', '🚋', '🚃', '🚎', '🚌', '🚍', '🚙',
    '🚘', '🚗', '🚕', '🚖', '🚛', '🚚', '🚨', '🚓', '🚔', '🚒',
    '🚑', '🚐', '🚜'
]
```

**Selection Logic:**
```python
def assign_buggy_icon(hotel_id):
    """
    Assign a unique icon to a new buggy
    
    Logic:
    1. Get all used icons for this hotel
    2. Find unused icons from BUGGY_ICONS
    3. If unused icons exist, pick first one
    4. If all used, pick any icon from set
    
    Returns:
        str: Selected emoji icon
    """
    from app.models.buggy import Buggy
    
    # Get used icons
    used_icons = db.session.query(Buggy.icon)\
        .filter(Buggy.hotel_id == hotel_id, Buggy.icon.isnot(None))\
        .all()
    used_icons_set = {icon[0] for icon in used_icons}
    
    # Find unused
    unused_icons = [icon for icon in BUGGY_ICONS if icon not in used_icons_set]
    
    # Return unused or any
    if unused_icons:
        return unused_icons[0]
    else:
        return BUGGY_ICONS[0]  # Fallback to first icon
```

### 3. Template Layout Changes

**New Layout Order:**
```html
<div class="container">
    <!-- 1. Welcome Message (5 seconds) -->
    <div class="welcome-message">...</div>
    
    <!-- 2. Active Requests & Buggy Status (Main Content) -->
    <div class="grid grid-2">
        <div class="card">Aktif Talepler</div>
        <div class="card">Buggy Durumu</div>
    </div>
    
    <!-- 3. Stats Cards (Moved to bottom) -->
    <div class="grid grid-4">
        <div class="stat-card">Aktif Buggy</div>
        <div class="stat-card">Bekleyen Talepler</div>
        <div class="stat-card">Bugün Tamamlanan</div>
        <div class="stat-card">Toplam Lokasyon</div>
    </div>
</div>
```

### 4. Buggy List Rendering

**JavaScript Update:**
```javascript
// app/static/js/admin.js - updateBuggyStatus function
function renderBuggyItem(buggy) {
    const icon = buggy.icon || '🚗';  // Default icon
    const statusClass = getStatusClass(buggy.status);
    const statusText = getStatusText(buggy.status);
    
    return `
        <div class="list-item">
            <div class="buggy-icon">${icon}</div>
            <div class="buggy-info">
                <strong>${buggy.code}</strong>
                <span class="badge ${statusClass}">${statusText}</span>
            </div>
            <div class="buggy-details">
                ${buggy.driver_name || 'Sürücü Yok'}
                ${buggy.current_location?.name || '-'}
            </div>
        </div>
    `;
}
```

## Data Models

### Updated Buggy Model

```python
class Buggy(db.Model, BaseModel):
    __tablename__ = 'buggies'
    
    id = Column(Integer, primary_key=True)
    hotel_id = Column(Integer, ForeignKey('hotels.id'), nullable=False)
    code = Column(String(50), nullable=False, unique=True)
    icon = Column(String(10), nullable=True)  # NEW FIELD
    status = Column(Enum(BuggyStatus), default=BuggyStatus.AVAILABLE)
    # ... other fields
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'icon': self.icon,  # Include in API response
            'status': self.status.value,
            # ... other fields
        }
```

## Error Handling

### Icon Assignment Errors
- **Scenario**: Database query fails during icon selection
- **Handling**: Use default icon '🚗' and log error
- **User Impact**: Buggy created successfully with default icon

### Migration Errors
- **Scenario**: Icon column already exists
- **Handling**: Migration checks for column existence
- **Rollback**: Drop column if downgrade needed

### Display Errors
- **Scenario**: Icon field is NULL or invalid
- **Handling**: JavaScript uses default icon '🚗'
- **User Impact**: No visual disruption

## Testing Strategy

### Unit Tests
1. **Icon Selection Logic**
   - Test unused icon selection
   - Test all icons used scenario
   - Test empty database scenario

2. **Model Changes**
   - Test icon field storage
   - Test to_dict() includes icon
   - Test NULL icon handling

### Integration Tests
1. **Buggy Creation**
   - Create buggy and verify icon assigned
   - Create multiple buggies, verify unique icons
   - Create 34th buggy, verify icon reuse

2. **Dashboard Display**
   - Load dashboard, verify layout order
   - Verify buggy icons displayed
   - Verify responsive behavior

### Manual Testing
1. **Layout Verification**
   - Check lists appear before widgets
   - Verify mobile responsive design
   - Test scroll behavior

2. **Icon Display**
   - Create new buggy, verify icon assigned
   - Check icon appears in buggy list
   - Verify icon size and alignment

## Implementation Notes

### Migration Strategy
1. Create migration file
2. Add icon column (nullable)
3. Run migration on dev/staging
4. Verify existing buggies work
5. Deploy to production

### Backward Compatibility
- Icon field is nullable
- Existing buggies without icons will show default '🚗'
- No breaking changes to API

### Performance Considerations
- Icon selection query is simple (single table, indexed hotel_id)
- No impact on dashboard load time
- Icon stored as text (2-4 bytes per emoji)

## CSS Styling

### Buggy Icon Styling
```css
.buggy-icon {
    font-size: 1.5rem;
    margin-right: 0.75rem;
    display: inline-block;
    vertical-align: middle;
}

.list-item {
    display: flex;
    align-items: center;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid #e5e7eb;
}

.buggy-info {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
```

### Responsive Layout
```css
/* Desktop: 2 columns for lists, 4 columns for widgets */
@media (min-width: 768px) {
    .grid-2 { grid-template-columns: repeat(2, 1fr); }
    .grid-4 { grid-template-columns: repeat(4, 1fr); }
}

/* Mobile: 1 column for all */
@media (max-width: 767px) {
    .grid-2, .grid-4 { grid-template-columns: 1fr; }
}
```
