# API Banner Component Specification

## Purpose
Always-visible banner promoting the REST API for programmatic access.

## Implementation Details

### HTML Structure
```html
<div id="api-banner" class="api-banner">
    <span class="api-banner-text">
        🔧 API Available! This tool can also be used programmatically. 
        Integrate patient generation into your systems via our REST API.
    </span>
    <a href="/docs" class="api-banner-link">View API Documentation →</a>
</div>
```

### JavaScript Component
```javascript
class ApiBanner {
    constructor() {
        this.element = document.getElementById('api-banner');
        this.link = this.element.querySelector('.api-banner-link');
        this.init();
    }
    
    init() {
        // Track API documentation clicks
        this.link.addEventListener('click', (e) => {
            this.trackClick();
            // Let default link behavior continue
        });
    }
    
    trackClick() {
        // Log for analytics
        console.log('API documentation accessed from banner');
        
        // Could send to analytics service
        if (window.analytics) {
            window.analytics.track('api_docs_clicked', {
                source: 'ui_banner',
                timestamp: new Date().toISOString()
            });
        }
    }
}
```

### CSS Styling
```css
.api-banner {
    background: #e3f2fd;
    border: 1px solid #1976d2;
    border-radius: 4px;
    padding: 12px 20px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 14px;
}

.api-banner-text {
    flex: 1;
    color: #0d47a1;
    line-height: 1.4;
}

.api-banner-link {
    background: #1976d2;
    color: white;
    padding: 8px 16px;
    border-radius: 4px;
    text-decoration: none;
    white-space: nowrap;
    font-weight: 500;
    margin-left: 20px;
    transition: background-color 0.2s;
}

.api-banner-link:hover {
    background: #1565c0;
}

/* Responsive */
@media (max-width: 768px) {
    .api-banner {
        flex-direction: column;
        text-align: center;
    }
    
    .api-banner-link {
        margin-left: 0;
        margin-top: 10px;
        display: inline-block;
    }
}
```

### Tests
```javascript
describe('ApiBanner', () => {
    let banner;
    
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="api-banner" class="api-banner">
                <span class="api-banner-text">
                    🔧 API Available! This tool can also be used programmatically. 
                    Integrate patient generation into your systems via our REST API.
                </span>
                <a href="/docs" class="api-banner-link">View API Documentation →</a>
            </div>
        `;
        banner = new ApiBanner();
    });
    
    test('should display promotional text', () => {
        const text = document.querySelector('.api-banner-text').textContent;
        expect(text).toContain('API Available');
        expect(text).toContain('programmatically');
    });
    
    test('should link to /docs', () => {
        const link = document.querySelector('.api-banner-link');
        expect(link.href).toContain('/docs');
    });
    
    test('should always be visible', () => {
        const element = document.getElementById('api-banner');
        expect(element.style.display).not.toBe('none');
        expect(element).toBeVisible();
    });
    
    test('should track clicks for analytics', () => {
        const consoleSpy = jest.spyOn(console, 'log');
        const link = document.querySelector('.api-banner-link');
        
        link.click();
        
        expect(consoleSpy).toHaveBeenCalledWith(
            'API documentation accessed from banner'
        );
    });
});
```

## Integration Notes

1. Banner should be the first element after `<body>`
2. Always visible - no dismiss option
3. Links to internal `/docs` endpoint
4. Responsive design for smaller screens
5. Click tracking for usage analytics

---

*Component Status: Ready for TDD implementation*
