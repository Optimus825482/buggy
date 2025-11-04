# Design Document

## Overview

Bu tasarım dokümanı, misafir QR kod okuttuktan sonraki buggy talep sayfasının (call_premium.html) görsel ve kullanıcı deneyimi iyileştirmelerini detaylandırır. Mevcut sayfa temel işlevselliğe sahip ancak modern, premium ve mobil-first bir tasarıma ihtiyaç duyuyor.

### Design Goals

1. **Premium Görünüm**: Lüks otel standartlarına uygun, modern ve profesyonel arayüz
2. **Mobil-First**: Öncelikle mobil cihazlar için optimize edilmiş deneyim
3. **Kullanıcı Dostu**: Sezgisel, kolay anlaşılır ve hızlı etkileşim
4. **Performans**: Hızlı yükleme ve akıcı animasyonlar
5. **Erişilebilirlik**: WCAG AA standartlarına uygun tasarım

### Current State Analysis

**Mevcut Sayfa Yapısı:**
- Hero section (logo, başlık, alt başlık)
- QR Scanner Card (QR kod okutma butonu)
- Room Number Card (oda numarası girişi - gizli)
- Hotel name ve powered by footer

**Mevcut Sorunlar:**
- Basit ve sade görünüm, premium hissi vermiyor
- Butonlar yeterince dikkat çekici değil
- Mobil dokunma alanları optimize değil
- Animasyonlar ve geçişler eksik
- Görsel hiyerarşi zayıf
- Loading ve success state'leri yetersiz


## Architecture

### Component Hierarchy

```
Guest Request Page (call_premium.html)
├── Hero Section
│   ├── Logo Container (animated)
│   ├── Title (gradient text)
│   └── Subtitle (dynamic)
├── QR Scanner Card (conditional)
│   ├── Icon Container (pulsing animation)
│   ├── Title & Description
│   └── Scan Button (gradient, ripple effect)
├── Room Number Card (conditional)
│   ├── Header (icon + title)
│   ├── Input Field (enhanced styling)
│   └── Submit Button (gradient, ripple effect)
└── Footer Section
    ├── Hotel Name
    └── Powered By

Modals & Overlays
├── QR Scanner Modal
│   ├── Camera View
│   └── Close Button
├── Confirmation Modal (custom)
│   ├── Icon (animated)
│   ├── Details
│   └── Action Buttons
└── Success Notification (custom)
    ├── Icon (animated)
    ├── Message
    └── Warning Text
```

### State Management

**Page States:**
1. **Initial State**: QR Scanner Card visible, Room Number Card hidden
2. **Location Selected**: QR Scanner Card hidden, Room Number Card visible
3. **Loading State**: Overlay with spinner and message
4. **Confirmation State**: Custom modal with request details
5. **Success State**: Custom notification with 5-second warning
6. **Error State**: Toast notification with error message


## Components and Interfaces

### 1. Hero Section

**Design Specifications:**
- Container: max-width 500px, centered, padding 40px 0
- Logo: 120x120px, gradient background (#1BA5A8 to #5BC0C3), border-radius 30px
- Logo Animation: Float effect (3s ease-in-out infinite)
- Title: 32px, font-weight 800, gradient text (#1BA5A8 to #F28C38)
- Subtitle: 16px, color #6B7280, font-weight 500

**CSS Classes:**
```css
.guest-hero {
  text-align: center;
  padding: 40px 0;
  margin-bottom: 32px;
}

.guest-logo {
  width: 120px;
  height: 120px;
  margin: 0 auto 24px;
  background: linear-gradient(135deg, #1BA5A8, #5BC0C3);
  border-radius: 30px;
  box-shadow: 0 20px 60px rgba(27, 165, 168, 0.3);
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}
```

### 2. QR Scanner Card

**Design Specifications:**
- Background: white
- Border-radius: 24px
- Padding: 32px 24px
- Box-shadow: 0 8px 40px rgba(0, 0, 0, 0.08)
- Icon Container: 100x100px, gradient background, dashed border, pulsing animation
- Button: Full width, 56px height, gradient background, ripple effect

**Interactive States:**
- Default: Gradient background, shadow
- Hover: Transform translateY(-4px), increased shadow
- Active: Transform translateY(-2px), ripple effect
- Focus: Outline with primary color

**CSS Classes:**
```css
.qr-scanner-card {
  background: white;
  border-radius: 24px;
  padding: 32px 24px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.08);
  text-align: center;
}

.qr-scanner-icon {
  width: 100px;
  height: 100px;
  margin: 0 auto 24px;
  background: linear-gradient(135deg, rgba(27, 165, 168, 0.1), rgba(242, 140, 56, 0.1));
  border-radius: 24px;
  border: 3px dashed rgba(27, 165, 168, 0.3);
  animation: scanner-pulse 2s ease-in-out infinite;
}

@keyframes scanner-pulse {
  0%, 100% {
    border-color: rgba(27, 165, 168, 0.3);
    transform: scale(1);
  }
  50% {
    border-color: rgba(27, 165, 168, 0.6);
    transform: scale(1.05);
  }
}
```


### 3. Room Number Card

**Design Specifications:**
- Background: white
- Border-radius: 24px
- Padding: 24px
- Box-shadow: 0 8px 40px rgba(0, 0, 0, 0.08)
- Header: Icon (48x48px) + Title (18px, font-weight 700)
- Input: Enhanced styling with focus states
- Button: Full width, 56px height, gradient background

**Input Field Styling:**
- Height: 48px
- Border: 2px solid #E5E7EB
- Border-radius: 12px
- Font-size: 16px (prevent zoom on iOS)
- Padding: 12px 16px
- Focus: Border color #1BA5A8, box-shadow

**CSS Classes:**
```css
.glass-card {
  background: white;
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.icon-primary {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(27, 165, 168, 0.1), rgba(27, 165, 168, 0.05));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1BA5A8;
  font-size: 24px;
  border: 1px solid rgba(27, 165, 168, 0.2);
}

.form-control {
  height: 48px;
  border: 2px solid #E5E7EB;
  border-radius: 12px;
  font-size: 16px;
  padding: 12px 16px;
  transition: all 0.3s ease;
}

.form-control:focus {
  border-color: #1BA5A8;
  box-shadow: 0 0 0 4px rgba(27, 165, 168, 0.1);
  outline: none;
}
```

### 4. Buttons

**Primary Button (Scan QR / Call Buggy):**
- Width: 100%
- Height: 56px (mobil için minimum dokunma alanı)
- Background: linear-gradient(135deg, #1BA5A8, #5BC0C3)
- Color: white
- Border-radius: 16px
- Font-size: 18px
- Font-weight: 700
- Box-shadow: 0 8px 24px rgba(27, 165, 168, 0.3)

**Button States:**
- Hover: translateY(-4px), increased shadow
- Active: translateY(-2px), ripple effect
- Disabled: opacity 0.5, cursor not-allowed
- Loading: spinner icon, disabled state

**Ripple Effect Implementation:**
```css
.ripple-effect {
  position: relative;
  overflow: hidden;
}

.ripple-effect::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.5);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}

.ripple-effect:active::after {
  width: 300px;
  height: 300px;
}
```


### 5. Confirmation Modal

**Design Specifications:**
- Overlay: Fixed position, rgba(0, 0, 0, 0.7) background
- Modal: White background, border-radius 16px, max-width 500px
- Icon: 100x100px circle, gradient background, pulsing animation
- Details Section: Gradient background, border-radius 12px, border 2px solid #1BA5A8
- Buttons: Flex layout, gap 1rem

**Animation:**
- Overlay: fadeIn 0.3s ease
- Modal: slideUp 0.3s ease
- Icon: questionPulse 2s infinite

**Structure:**
```html
<div class="custom-confirmation-overlay">
  <div class="modal">
    <div class="icon-container">
      <i class="fas fa-question"></i>
    </div>
    <h3>Buggy Çağırmak İstiyor musunuz?</h3>
    <p>Talebinizi onaylayın</p>
    <div class="details-section">
      <div class="detail-item">
        <i class="fas fa-map-marker-alt"></i>
        <span>Lokasyon: ...</span>
      </div>
      <!-- More details -->
    </div>
    <div class="button-group">
      <button class="btn-cancel">İptal</button>
      <button class="btn-confirm">Evet, Çağır</button>
    </div>
  </div>
</div>
```

### 6. Success Notification

**Design Specifications:**
- Similar structure to confirmation modal
- Icon: Check mark, green gradient background
- Warning section: Yellow background (#fef3c7), amber border
- Auto-close: 5 seconds
- Animation: slideUp on enter, fadeOut on exit

**Key Features:**
- Prominent success icon with pulse animation
- Clear success message
- 5-second warning with icon
- Non-dismissible (auto-close only)


## Data Models

### Page State Model

```javascript
{
  selectedLocationId: number | null,
  roomNumber: string,
  isLoading: boolean,
  showQRScanner: boolean,
  showRoomNumberCard: boolean,
  locationInfo: {
    id: number,
    name: string,
    description: string
  } | null
}
```

### Request Model

```javascript
{
  location_id: number,
  room_number: string | null,
  hotel_id: number
}
```

### Response Model

```javascript
{
  success: boolean,
  request: {
    id: number,
    location_id: number,
    room_number: string | null,
    status: string,
    created_at: string
  },
  error?: string
}
```

## Error Handling

### Error Types

1. **QR Code Errors**
   - Invalid format
   - Location not found
   - Camera permission denied

2. **Network Errors**
   - API request failed
   - Timeout
   - Connection lost

3. **Validation Errors**
   - No location selected
   - Invalid room number format

### Error Display Strategy

**Toast Notifications:**
- Position: Top center
- Duration: 3-5 seconds
- Types: error, warning, info, success
- Animation: Slide down from top

**Error Messages:**
- User-friendly language (Turkish)
- Clear action items
- Retry options when applicable

**Example Error Handling:**
```javascript
try {
  // API call
} catch (error) {
  if (error.type === 'network') {
    Utils.showToast('Bağlantı hatası. Lütfen tekrar deneyin.', 'error');
  } else if (error.type === 'validation') {
    Utils.showToast('Lütfen tüm alanları doldurun.', 'warning');
  } else {
    Utils.showToast('Bir hata oluştu. Lütfen tekrar deneyin.', 'error');
  }
}
```


## Testing Strategy

### Visual Testing

1. **Cross-Browser Testing**
   - Chrome (latest)
   - Safari (iOS)
   - Firefox (latest)
   - Edge (latest)

2. **Device Testing**
   - iPhone (various sizes)
   - Android phones (various sizes)
   - Tablets
   - Desktop (various resolutions)

3. **Responsive Breakpoints**
   - Mobile: < 768px
   - Tablet: 768px - 1024px
   - Desktop: > 1024px

### Functional Testing

1. **QR Code Scanning**
   - Valid QR code (URL format)
   - Valid QR code (LOC format)
   - Invalid QR code
   - Camera permission denied
   - Multiple scans

2. **Form Submission**
   - With room number
   - Without room number
   - Invalid room number
   - Network error during submission
   - Successful submission

3. **State Transitions**
   - Initial load
   - QR code scanned
   - Location selected
   - Form submitted
   - Success state
   - Error state

### Performance Testing

1. **Load Time Metrics**
   - First Contentful Paint < 2s
   - Time to Interactive < 3s
   - Total page load < 5s

2. **Animation Performance**
   - 60 FPS for all animations
   - No jank during transitions
   - Smooth scroll behavior

3. **Network Performance**
   - API response time < 1s
   - Optimized image loading
   - Minimal CSS/JS bundle size

### Accessibility Testing

1. **Keyboard Navigation**
   - Tab order logical
   - Focus indicators visible
   - All interactive elements accessible

2. **Screen Reader Testing**
   - Proper ARIA labels
   - Semantic HTML structure
   - Meaningful alt text

3. **Color Contrast**
   - WCAG AA compliance
   - Text readable on all backgrounds
   - Focus indicators visible


## Design System

### Color Palette

**Primary Colors:**
- Primary Turquoise: #1BA5A8
- Primary Turquoise Light: #5BC0C3
- Primary Turquoise Dark: #158B8E
- Accent Orange: #F28C38
- Accent Orange Dark: #D97826

**Semantic Colors:**
- Success: #10B981
- Error: #E74C3C
- Warning: #F59E0B
- Info: #3498DB

**Neutral Colors:**
- Dark Gray: #111827
- Medium Gray: #6B7280
- Light Gray: #9CA3AF
- Very Light Gray: #F9FAFB
- White: #FFFFFF

### Typography

**Font Family:**
- Primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
- Monospace: 'SF Mono', Monaco, Consolas, monospace

**Font Sizes:**
- xs: 12px
- sm: 14px
- base: 16px
- lg: 18px
- xl: 20px
- 2xl: 24px
- 3xl: 32px

**Font Weights:**
- Normal: 400
- Medium: 500
- Semibold: 600
- Bold: 700
- Extrabold: 800

### Spacing Scale

- xs: 4px
- sm: 8px
- md: 16px
- lg: 24px
- xl: 32px
- 2xl: 48px

### Border Radius

- sm: 8px
- md: 12px
- lg: 16px
- xl: 20px
- 2xl: 24px
- full: 9999px (circular)

### Shadows

**Elevation Levels:**
- sm: 0 1px 2px rgba(0, 0, 0, 0.05)
- md: 0 4px 6px rgba(0, 0, 0, 0.1)
- lg: 0 8px 16px rgba(0, 0, 0, 0.1)
- xl: 0 12px 24px rgba(0, 0, 0, 0.12)
- 2xl: 0 20px 40px rgba(0, 0, 0, 0.15)

**Colored Shadows:**
- Primary: 0 8px 24px rgba(27, 165, 168, 0.3)
- Secondary: 0 8px 24px rgba(242, 140, 56, 0.3)
- Success: 0 8px 24px rgba(16, 185, 129, 0.3)

### Animations

**Timing Functions:**
- Fast: 150ms cubic-bezier(0.4, 0, 0.2, 1)
- Base: 250ms cubic-bezier(0.4, 0, 0.2, 1)
- Slow: 350ms cubic-bezier(0.4, 0, 0.2, 1)
- Bounce: 500ms cubic-bezier(0.68, -0.55, 0.265, 1.55)

**Common Animations:**
- fadeIn: opacity 0 to 1
- slideUp: translateY(50px) to 0
- float: translateY oscillation
- pulse: scale oscillation
- ripple: expanding circle


## Mobile-First Responsive Design

### Breakpoints

```css
/* Mobile First Approach */
/* Base styles: Mobile (< 768px) */

/* Tablet */
@media (min-width: 768px) {
  /* Tablet specific styles */
}

/* Desktop */
@media (min-width: 1024px) {
  /* Desktop specific styles */
}
```

### Mobile Optimizations

**Touch Targets:**
- Minimum size: 44x44px (iOS) / 48x48px (Android)
- Spacing between targets: minimum 8px
- Button height: 56px for primary actions

**Font Sizes:**
- Minimum 16px for inputs (prevents iOS zoom)
- Body text: 16px
- Headings: Scale appropriately

**Viewport Settings:**
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
```

**Safe Areas (iOS):**
```css
padding-bottom: env(safe-area-inset-bottom);
padding-left: env(safe-area-inset-left);
padding-right: env(safe-area-inset-right);
```

### Performance Optimizations

**CSS:**
- Use CSS transforms for animations (GPU accelerated)
- Minimize repaints and reflows
- Use will-change for animated elements
- Lazy load non-critical CSS

**JavaScript:**
- Debounce scroll and resize events
- Use passive event listeners
- Minimize DOM manipulations
- Use requestAnimationFrame for animations

**Images:**
- Optimize image sizes
- Use appropriate formats (WebP with fallback)
- Lazy load images below the fold
- Use srcset for responsive images

**Loading Strategy:**
- Critical CSS inline
- Defer non-critical JavaScript
- Preload key resources
- Use service worker for caching


## Implementation Notes

### CSS Architecture

**File Structure:**
```
app/static/css/
├── variables.css (already exists - design tokens)
├── modern.css (already exists - modern components)
├── professional.css (already exists - premium styles)
└── guest-premium.css (new - guest-specific styles)
```

**Naming Convention:**
- BEM methodology for component classes
- Utility classes for common patterns
- Semantic class names

**Example:**
```css
/* Component */
.qr-scanner-card { }
.qr-scanner-card__icon { }
.qr-scanner-card__title { }
.qr-scanner-card__button { }

/* Modifiers */
.qr-scanner-card--loading { }
.qr-scanner-card--error { }

/* Utilities */
.u-text-center { }
.u-mb-lg { }
```

### JavaScript Architecture

**Module Pattern:**
```javascript
const GuestPage = {
  state: {
    locationId: null,
    isLoading: false
  },
  
  init() {
    this.setupEventListeners();
    this.checkURLParams();
  },
  
  setupEventListeners() {
    // Event bindings
  },
  
  handleQRScan(data) {
    // QR scan logic
  },
  
  submitRequest() {
    // Form submission
  }
};
```

### Accessibility Considerations

**ARIA Labels:**
```html
<button aria-label="QR kod okut" class="btn-scan-qr">
  <i class="fas fa-camera" aria-hidden="true"></i>
  QR Kod Okut
</button>

<input 
  type="text" 
  id="room-number"
  aria-label="Oda numaranız"
  aria-describedby="room-number-help"
>
<span id="room-number-help" class="sr-only">
  Oda numaranızı girin (opsiyonel)
</span>
```

**Focus Management:**
- Trap focus in modals
- Return focus after modal close
- Visible focus indicators
- Logical tab order

**Screen Reader Support:**
- Semantic HTML elements
- ARIA live regions for dynamic content
- Descriptive link text
- Alt text for images


## Design Decisions and Rationale

### 1. Gradient Backgrounds

**Decision:** Use gradient backgrounds for primary elements (logo, buttons, text)

**Rationale:**
- Creates premium, modern look
- Matches brand colors (#1BA5A8 and #F28C38)
- Adds depth and visual interest
- Industry standard for luxury apps

### 2. Glass Morphism

**Decision:** Use glass morphism effect for cards

**Rationale:**
- Modern design trend
- Creates depth hierarchy
- Lightweight, elegant appearance
- Works well with gradients

### 3. Large Touch Targets

**Decision:** Minimum 56px height for buttons on mobile

**Rationale:**
- Exceeds iOS (44px) and Android (48px) guidelines
- Reduces tap errors
- Better accessibility
- Easier for users with motor impairments

### 4. Custom Modals

**Decision:** Create custom modals instead of using browser alerts

**Rationale:**
- Better brand consistency
- More control over styling
- Enhanced user experience
- Animated transitions
- Mobile-friendly

### 5. Pulsing Animations

**Decision:** Add pulsing animations to key elements (QR icon, status indicators)

**Rationale:**
- Draws attention to important actions
- Indicates interactivity
- Creates sense of life/activity
- Subtle, not distracting

### 6. 5-Second Warning

**Decision:** Show non-dismissible 5-second warning after request submission

**Rationale:**
- Prevents premature page close
- Ensures user sees success message
- Allows time for backend processing
- Reduces support requests

### 7. Ripple Effect

**Decision:** Add ripple effect to buttons

**Rationale:**
- Material Design pattern
- Provides tactile feedback
- Confirms user interaction
- Modern, polished feel

### 8. Gradient Text

**Decision:** Use gradient text for titles and branding

**Rationale:**
- Eye-catching
- Premium appearance
- Brand color integration
- Differentiates from body text


## Visual Mockup Descriptions

### Initial State (QR Scanner Visible)

```
┌─────────────────────────────────────┐
│                                     │
│         [Floating Logo]             │
│       🏌️ Buggy Call                 │
│     Your Ride, On Demand            │
│                                     │
├─────────────────────────────────────┤
│                                     │
│  ┌───────────────────────────────┐ │
│  │   [Pulsing QR Icon]           │ │
│  │                               │ │
│  │   QR Kod Okutun               │ │
│  │   Bulunduğunuz lokasyondaki   │ │
│  │   QR kodu okutarak...         │ │
│  │                               │ │
│  │  [📷 QR Kod Okut Button]     │ │
│  │   (Gradient, Full Width)      │ │
│  └───────────────────────────────┘ │
│                                     │
├─────────────────────────────────────┤
│                                     │
│        Hotel Name                   │
│      Powered by Erkan ERDEM         │
│                                     │
└─────────────────────────────────────┘
```

### Location Selected State (Room Number Card Visible)

```
┌─────────────────────────────────────┐
│                                     │
│         [Floating Logo]             │
│       🏌️ Buggy Call                 │
│   Lokasyon: Pool Area               │
│                                     │
├─────────────────────────────────────┤
│                                     │
│  ┌───────────────────────────────┐ │
│  │  [🚪 Icon] Oda Numaranız      │ │
│  │           (Opsiyonel)         │ │
│  │                               │ │
│  │  ┌─────────────────────────┐ │ │
│  │  │ Örn: A-101              │ │ │
│  │  └─────────────────────────┘ │ │
│  │                               │ │
│  │  [✈️ Buggy Çağır Button]     │ │
│  │   (Gradient, Full Width)      │ │
│  └───────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘
```

### Confirmation Modal

```
┌─────────────────────────────────────┐
│  [Dark Overlay - 70% opacity]       │
│                                     │
│  ┌───────────────────────────────┐ │
│  │                               │ │
│  │    [❓ Pulsing Icon]          │ │
│  │                               │ │
│  │  Buggy Çağırmak İstiyor       │ │
│  │      musunuz?                 │ │
│  │                               │ │
│  │  Talebinizi onaylayın         │ │
│  │                               │ │
│  │  ┌─────────────────────────┐ │ │
│  │  │ 📍 Lokasyon: Pool Area  │ │ │
│  │  │ 🚪 Oda: A-101           │ │ │
│  │  └─────────────────────────┘ │ │
│  │                               │ │
│  │  [İptal]  [Evet, Çağır]      │ │
│  │                               │ │
│  └───────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘
```

### Success Notification

```
┌─────────────────────────────────────┐
│  [Dark Overlay - 70% opacity]       │
│                                     │
│  ┌───────────────────────────────┐ │
│  │                               │ │
│  │    [✅ Pulsing Icon]          │ │
│  │                               │ │
│  │   ✅ Talebiniz Alındı!        │ │
│  │                               │ │
│  │  Buggy çağrınız başarıyla     │ │
│  │  gönderildi. Durumunu         │ │
│  │  takip edebilirsiniz.         │ │
│  │                               │ │
│  │  ┌─────────────────────────┐ │ │
│  │  │ ⚠️ Bu pencereyi 5       │ │ │
│  │  │ saniye boyunca          │ │ │
│  │  │ kapatmayın!             │ │ │
│  │  └─────────────────────────┘ │ │
│  │                               │ │
│  │  (Auto-closes in 5s)          │ │
│  │                               │ │
│  └───────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘
```

## Summary

Bu tasarım dokümanı, misafir buggy talep sayfası için modern, premium ve mobil-first bir yaklaşım sunuyor. Temel odak noktaları:

1. **Premium Görünüm**: Gradient'ler, glass morphism, animasyonlar
2. **Mobil Optimizasyon**: Büyük dokunma alanları, responsive tasarım
3. **Kullanıcı Deneyimi**: Net geri bildirimler, custom modal'lar, smooth animasyonlar
4. **Performans**: Optimize edilmiş yükleme, 60 FPS animasyonlar
5. **Erişilebilirlik**: WCAG AA uyumlu, klavye navigasyonu, screen reader desteği

Tasarım, mevcut CSS framework'ünü (variables.css, modern.css, professional.css) kullanarak tutarlılığı korurken, guest-specific iyileştirmeler ekliyor.
