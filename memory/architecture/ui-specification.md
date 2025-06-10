# Finalized UI Specification - Medical Patients Generator

## Overview
Single-page application optimized for 1080p military laptops with API-first promotion.

## Visual Layout

```
┌─────────────────────────────────────────────────────┐
│ 🔧 API Available! This tool can also be used       │
│ programmatically. Integrate patient generation      │
│ into your systems via our REST API.                │
│ [View API Documentation →]                          │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│          Military Patient Generator                 │
│   [Load Previous] [Generate Patients] [Reset All]   │
├─────────────────────────────────────────────────────┤
│ ▼ Demographics Configuration ✓                      │
│   ┌───────────────────────────────────────────┐    │
│   │ {                                         │    │
│   │   "nationalities": {                      │    │
│   │     "USA": 40,                           │    │
│   │     "GBR": 30,                           │    │
│   │     ...                                   │    │
│   │   }                                       │    │
│   └───────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────┤
│ ▶ Battle Fronts Configuration ✓                     │
├─────────────────────────────────────────────────────┤
│ ▶ Injury Distribution ✓                             │
└─────────────────────────────────────────────────────┘
```

## Key Components

### 1. API Banner (Always Visible)
- Light blue background (#e3f2fd)
- Fixed at top of page
- Text: "🔧 API Available! This tool can also be used programmatically. Integrate patient generation into your systems via our REST API."
- Button: "View API Documentation →" links to `/docs`
- No dismiss option - always visible

### 2. Header Section
- Title: "Military Patient Generator"
- Three action buttons:
  - **Load Previous**: Opens modal with generation history
  - **Generate Patients**: Primary action, disabled if JSON invalid
  - **Reset All**: Returns all editors to default state

### 3. Configuration Accordion
- Vertical stack of three sections
- Only one expanded at a time
- Each section shows validation status (✓ or ✗)
- Sections:
  1. Demographics Configuration
  2. Battle Fronts Configuration  
  3. Injury Distribution

### 4. JSON Editors
- Monaco-style text editor (but simpler)
- Monospace font (Consolas, 13px)
- Line numbers
- Basic syntax highlighting
- Real-time validation
- Height: 400px (300px on smaller screens)

### 5. Validation Features
- **Nationality codes**: Validated against hardcoded list
- **JSON syntax**: Real-time syntax checking
- **Inline errors**: Show below problematic lines
- Example: "Unknown nationality code 'XYZ'. Valid codes: USA, GBR, CAN..."

### 6. Load Previous Modal
```
┌─────────────────────────────────────┐
│ Previous Generations                │
├─────────────────────────────────────┤
│ ⏱ 2024-01-15 14:30 - 10,000 pts   │
│   UK: 40%, US: 30%, CA: 30%       │
│                                     │
│ ⏱ 2024-01-14 09:15 - 5,000 pts    │
│   US: 100% (Single nation test)    │
│                                     │
│ [Load Selected] [Cancel]            │
└─────────────────────────────────────┘
```

### 7. Progress Display
- Minimum duration: 2 seconds
- At least 4 distinct phases
- Smooth, linear progression
- Fun rotating messages

**Progress Phases:**
1. 0-15%: "Validating configurations..."
2. 15-30%: "Initializing patient generator..."
3. 30-85%: "Generating patients..." (with count)
4. 85-95%: "Finalizing medical records..."
5. 95-100%: "Creating downloadable archives..."

**Fun Messages Pool:**
- "Rolling dice for combat injuries..."
- "Consulting field medics for realistic injuries..."
- "Distributing casualties across battle fronts..."
- "Assigning triage categories..."
- "Creating believable medical histories..."
- "Randomizing arrival patterns..."
- "Double-checking NATO personnel IDs..."
- "Simulating evacuation priorities..."
- "Adding battlefield dust for authenticity..."
- "Generating convincing vital signs..."
- "Cross-referencing injury patterns..."

### 8. Error Handling
- Auto-retry 3 times with exponential backoff
- Developer-friendly error modal on final failure
- Copyable error report with:
  - Timestamp
  - Job ID
  - Configuration hash
  - Error details
  - Stack trace
  - Browser info

### 9. Results Display
- Summary: "Successfully generated 10,000 patients"
- Generation time
- File size
- Download button(s)

## Technical Requirements

### Responsive Design
- Max width: 1000px (comfortable on 1080p)
- Mobile-first CSS approach
- Adjust editor height on smaller screens

### Browser Support
- Chrome/Edge (modern versions)
- Firefox
- No IE11 support needed

### Performance
- Page load < 1 second
- Instant JSON validation
- Smooth progress animation

### Accessibility
- Keyboard navigation
- ARIA labels
- High contrast support
- Clear error messages

## Database Schema Addition

```sql
CREATE TABLE generation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    total_patients INTEGER NOT NULL,
    configuration JSONB NOT NULL,
    summary JSONB,
    user_label TEXT
);

CREATE INDEX idx_generation_history_created_at 
ON generation_history(created_at DESC);
```

## API Endpoints Needed

1. `GET /api/generation-history` - List previous generations
2. `GET /api/generation-history/{id}` - Get specific configuration
3. `GET /api/nationalities` - Valid nationality codes

## CSS Color Palette

```css
:root {
    --primary: #1976d2;
    --primary-dark: #1565c0;
    --success: #4caf50;
    --error: #f44336;
    --warning: #ff9800;
    --background: #f5f5f5;
    --surface: #ffffff;
    --text-primary: #212121;
    --text-secondary: #666666;
    --border: #dddddd;
    --api-banner-bg: #e3f2fd;
    --api-banner-border: #1976d2;
    --api-banner-text: #0d47a1;
}
```

## Implementation Priority

1. API banner (static HTML/CSS)
2. Accordion structure
3. Basic JSON editors
4. Validation logic
5. Load previous feature
6. Progress animation
7. Error handling
8. Polish and testing

---

*Finalized: Current session*
*Ready for: TDD implementation*
