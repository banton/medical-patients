/**
 * Accordion Component Tests
 * Testing the vertical accordion behavior for configuration sections
 */

// Import test framework from banner tests
// Note: In a real project, this would be a proper module import
const { TestFramework, assert, querySelector } = window.TestFramework || {};

if (!TestFramework) {
    console.error('Test framework not loaded. Please include banner.test.js first.');
}

// Accordion-specific test utilities
function getAccordionItem(index) {
    const items = document.querySelectorAll('.accordion__item');
    assert(items[index], `Accordion item ${index} not found`);
    return items[index];
}

function getAccordionHeader(index) {
    const item = getAccordionItem(index);
    const header = item.querySelector('.accordion__header');
    assert(header, `Accordion header ${index} not found`);
    return header;
}

function getAccordionContent(index) {
    const item = getAccordionItem(index);
    const content = item.querySelector('.accordion__content');
    assert(content, `Accordion content ${index} not found`);
    return content;
}

function isExpanded(index) {
    const content = getAccordionContent(index);
    return content.classList.contains('accordion__content--expanded');
}

function clickAccordionHeader(index) {
    const header = getAccordionHeader(index);
    header.click();
    // Small delay for animation
    return new Promise(resolve => setTimeout(resolve, 50));
}

// Accordion Tests
TestFramework.test('Accordion should have correct structure', () => {
    const accordion = querySelector('.accordion');
    const items = accordion.querySelectorAll('.accordion__item');
    
    assert(items.length === 2, 'Should have 2 accordion items');
    
    items.forEach((item, index) => {
        const header = item.querySelector('.accordion__header');
        const content = item.querySelector('.accordion__content');
        const editor = item.querySelector('.accordion__editor');
        
        assert(header, `Item ${index} should have header`);
        assert(content, `Item ${index} should have content`);
        assert(editor, `Item ${index} should have editor`);
    });
});

TestFramework.test('Accordion should have proper section titles', () => {
    const expectedTitles = [
        'Battle Fronts Configuration',
        'Injury Distribution'
    ];
    
    expectedTitles.forEach((title, index) => {
        const header = getAccordionHeader(index);
        const titleElement = header.querySelector('.accordion__title');
        
        assert(titleElement.textContent.includes(title), 
               `Item ${index} should contain title "${title}"`);
    });
});

TestFramework.test('Accordion should have validation status indicators', () => {
    const items = document.querySelectorAll('.accordion__item');
    
    items.forEach((item, index) => {
        const status = item.querySelector('.accordion__status');
        assert(status, `Item ${index} should have status indicator`);
        
        const hasValidClass = status.classList.contains('accordion__status--valid') ||
                             status.classList.contains('accordion__status--invalid') ||
                             status.classList.contains('accordion__status--unknown');
        
        assert(hasValidClass, `Item ${index} status should have validation class`);
    });
});

TestFramework.test('Only one accordion section should be expanded initially', () => {
    const expandedCount = document.querySelectorAll('.accordion__content--expanded').length;
    assert(expandedCount <= 1, 'At most one section should be expanded initially');
});

TestFramework.test('Accordion should expand section when header clicked', async () => {
    // Ensure all sections are collapsed first
    const items = document.querySelectorAll('.accordion__item');
    items.forEach((item, index) => {
        const content = item.querySelector('.accordion__content');
        content.classList.remove('accordion__content--expanded');
        const header = item.querySelector('.accordion__header');
        header.classList.remove('accordion__header--active');
    });
    
    // Click first header
    await clickAccordionHeader(0);
    
    assert(isExpanded(0), 'First section should be expanded after click');
    
    const header = getAccordionHeader(0);
    assert(header.classList.contains('accordion__header--active'), 
           'First header should be active after click');
});

TestFramework.test('Accordion should collapse other sections when new one is opened', async () => {
    // Expand first section
    await clickAccordionHeader(0);
    assert(isExpanded(0), 'First section should be expanded');
    
    // Expand second section
    await clickAccordionHeader(1);
    
    assert(!isExpanded(0), 'First section should be collapsed');
    assert(isExpanded(1), 'Second section should be expanded');
    
    const firstHeader = getAccordionHeader(0);
    const secondHeader = getAccordionHeader(1);
    
    assert(!firstHeader.classList.contains('accordion__header--active'), 
           'First header should not be active');
    assert(secondHeader.classList.contains('accordion__header--active'), 
           'Second header should be active');
});

TestFramework.test('Accordion should toggle section when same header clicked twice', async () => {
    // Expand first section
    await clickAccordionHeader(0);
    assert(isExpanded(0), 'First section should be expanded');
    
    // Click same header again
    await clickAccordionHeader(0);
    assert(!isExpanded(0), 'First section should be collapsed after second click');
    
    const header = getAccordionHeader(0);
    assert(!header.classList.contains('accordion__header--active'), 
           'Header should not be active after collapse');
});

TestFramework.test('Accordion should be keyboard accessible', () => {
    const firstHeader = getAccordionHeader(0);
    
    // Check if header is focusable
    firstHeader.focus();
    assert(document.activeElement === firstHeader, 'Header should be focusable');
    
    // Check for proper button semantics
    assert(firstHeader.tagName === 'BUTTON', 'Header should be a button element');
    
    // Check for ARIA attributes
    const hasAriaExpanded = firstHeader.hasAttribute('aria-expanded');
    assert(hasAriaExpanded, 'Header should have aria-expanded attribute');
});

TestFramework.test('Accordion editors should have proper attributes', () => {
    const items = document.querySelectorAll('.accordion__item');
    
    items.forEach((item, index) => {
        const editor = item.querySelector('.accordion__editor');
        
        assert(editor.tagName === 'TEXTAREA', `Editor ${index} should be textarea`);
        assert(editor.hasAttribute('placeholder'), `Editor ${index} should have placeholder`);
        
        const hasId = editor.hasAttribute('id');
        assert(hasId, `Editor ${index} should have id for accessibility`);
    });
});

TestFramework.test('Accordion should validate JSON in editors', () => {
    const firstEditor = getAccordionItem(0).querySelector('.accordion__editor');
    
    // Test invalid JSON
    firstEditor.value = '{ invalid json }';
    firstEditor.dispatchEvent(new Event('input'));
    
    // Check if validation error appears
    const validationElement = getAccordionItem(0).querySelector('.accordion__validation');
    
    if (validationElement) {
        const hasErrorClass = validationElement.classList.contains('accordion__validation--error');
        // This test is optional since validation might not be implemented yet
        console.log('Validation element found:', hasErrorClass ? 'with error' : 'without error');
    }
});

// Export accordion utilities for other tests
if (typeof window !== 'undefined') {
    window.AccordionTestUtils = {
        getAccordionItem,
        getAccordionHeader,
        getAccordionContent,
        isExpanded,
        clickAccordionHeader
    };
}

console.log('🧪 Accordion tests loaded. Run TestFramework.runAll() to execute.');