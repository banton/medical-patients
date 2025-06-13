/**
 * API Banner Component Tests
 * Testing the always-visible API promotion banner
 */

/* eslint no-console: "off" */

// Simple test framework for frontend components
const TestFramework = {
    tests: [],

    test(description, testFn) {
        this.tests.push({ description, testFn });
    },

    async runAll() {
        console.log('🧪 Running API Banner Tests...\n');
        let passed = 0;
        let failed = 0;

        for (const { description, testFn } of this.tests) {
            try {
                await testFn();
                console.log(`✅ ${description}`);
                passed++;
            } catch (error) {
                console.log(`❌ ${description}`);
                console.log(`   Error: ${error.message}`);
                failed++;
            }
        }

        console.log(`\n📊 Results: ${passed} passed, ${failed} failed`);
        return { passed, failed };
    }
};

// Test utilities
function assert(condition, message) {
    if (!condition) {
        throw new Error(message || 'Assertion failed');
    }
}

function querySelector(selector) {
    const element = document.querySelector(selector);
    assert(element, `Element not found: ${selector}`);
    return element;
}

// API Banner Tests
TestFramework.test('API banner should be visible on page load', () => {
    const banner = querySelector('.api-banner');
    const style = getComputedStyle(banner);

    assert(style.display !== 'none', 'Banner should not be hidden');
    assert(banner.offsetHeight > 0, 'Banner should have height');
    assert(banner.offsetWidth > 0, 'Banner should have width');
});

TestFramework.test('API banner should contain required elements', () => {
    const banner = querySelector('.api-banner');
    const content = querySelector('.api-banner__content');
    const text = querySelector('.api-banner__text');
    const link = querySelector('.api-banner__link');

    assert(banner.contains(content), 'Banner should contain content wrapper');
    assert(content.contains(text), 'Content should contain text');
    assert(content.contains(link), 'Content should contain link');
});

TestFramework.test('API banner should have correct text content', () => {
    const text = querySelector('.api-banner__text');
    const expectedText = 'Temporal API Available';

    assert(text.textContent.includes(expectedText), `Banner text should include: "${expectedText}"`);
});

TestFramework.test('API banner link should point to documentation', () => {
    const link = querySelector('.api-banner__link');

    assert(link.getAttribute('href') === '/docs', 'Link should point to /docs');
    assert(link.textContent.includes('View Documentation'), 'Link should contain documentation text');
});

TestFramework.test('API banner should have proper styling classes', () => {
    const banner = querySelector('.api-banner');
    const content = querySelector('.api-banner__content');
    const text = querySelector('.api-banner__text');
    const link = querySelector('.api-banner__link');

    assert(banner.classList.contains('api-banner'), 'Banner should have api-banner class');
    assert(content.classList.contains('api-banner__content'), 'Content should have api-banner__content class');
    assert(text.classList.contains('api-banner__text'), 'Text should have api-banner__text class');
    assert(link.classList.contains('api-banner__link'), 'Link should have api-banner__link class');
});

TestFramework.test('API banner should be accessible', () => {
    const link = querySelector('.api-banner__link');

    // Check link is focusable
    link.focus();
    assert(document.activeElement === link, 'Link should be focusable');

    // Check for proper ARIA attributes (if any)
    const banner = querySelector('.api-banner');
    // No specific ARIA requirements for this banner, but check it's not hidden
    assert(banner.getAttribute('aria-hidden') !== 'true', 'Banner should not be hidden from screen readers');
});

TestFramework.test('API banner link should open in same tab', () => {
    const link = querySelector('.api-banner__link');

    // Should not have target="_blank" since it's internal documentation
    assert(link.getAttribute('target') !== '_blank', 'Internal documentation link should open in same tab');
});

TestFramework.test('API banner should persist on page interactions', () => {
    const banner = querySelector('.api-banner');
    const initialDisplay = getComputedStyle(banner).display;

    // Simulate user interactions that shouldn't hide the banner
    document.body.click();
    window.dispatchEvent(new Event('scroll'));

    const afterDisplay = getComputedStyle(banner).display;
    assert(initialDisplay === afterDisplay, 'Banner should remain visible after user interactions');
});

// Export for use in other test files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TestFramework, assert, querySelector };
}

// Export to window for other test files
if (typeof window !== 'undefined') {
    window.TestFramework = TestFramework;
    window.TestFramework.assert = assert;
    window.TestFramework.querySelector = querySelector;
}

// Auto-run tests if this file is loaded directly
if (typeof window !== 'undefined' && document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // Small delay to ensure styles are loaded
        setTimeout(() => TestFramework.runAll(), 100);
    });
} else if (typeof window !== 'undefined') {
    // Document already loaded
    setTimeout(() => TestFramework.runAll(), 100);
}
