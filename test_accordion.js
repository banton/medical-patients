// Quick test script to validate accordion logic
const frontsContent = `{
  "front_configs": [
    {
      "id": "poland",
      "name": "Poland Front",
      "casualty_rate": 0.6,
      "nationality_distribution": [
        { "nationality_code": "POL", "percentage": 50.0 },
        { "nationality_code": "LTU", "percentage": 25.0 },
        { "nationality_code": "NLD", "percentage": 20.0 },
        { "nationality_code": "ESP", "percentage": 5.0 }
      ]
    },
    {
      "id": "estonia",
      "name": "Estonia Front",
      "casualty_rate": 0.3,
      "nationality_distribution": [
        { "nationality_code": "EST", "percentage": 50.0 },
        { "nationality_code": "GBR", "percentage": 50.0 }
      ]
    },
    {
      "id": "finland",
      "name": "Finland Front",
      "casualty_rate": 0.1,
      "nationality_distribution": [
        { "nationality_code": "FIN", "percentage": 50.0 },
        { "nationality_code": "USA", "percentage": 50.0 }
      ]
    }
  ]
}`;

const injuriesContent = `{
  "injury_distribution": {
    "Disease": 0.52,
    "Non-Battle Injury": 0.33,
    "Battle Injury": 0.15
  },
  "total_patients": 1440
}`;

// Test validation functions
function validateBattleFronts(content) {
    if (!content) {
        return { valid: false, message: 'Battle fronts configuration is required' };
    }
    
    try {
        const config = JSON.parse(content);
        
        if (!Array.isArray(config.front_configs)) {
            return { valid: false, message: 'Missing or invalid "front_configs" array' };
        }
        
        if (config.front_configs.length === 0) {
            return { valid: false, message: 'At least one battle front must be configured' };
        }
        
        // Validate each front
        for (const front of config.front_configs) {
            if (!front.id || !front.name) {
                return { valid: false, message: 'Each front must have "id" and "name"' };
            }
            
            if (!front.nationality_distribution || !Array.isArray(front.nationality_distribution)) {
                return { valid: false, message: `Front "${front.name}" missing nationality distribution` };
            }
        }
        
        return { valid: true, message: `${config.front_configs.length} battle fronts configured` };
        
    } catch (e) {
        return { valid: false, message: `JSON syntax error: ${e.message}` };
    }
}

function validateInjuries(content) {
    if (!content) {
        return { valid: false, message: 'Injury distribution is required' };
    }
    
    try {
        const config = JSON.parse(content);
        
        if (!config.injury_distribution || typeof config.injury_distribution !== 'object') {
            return { valid: false, message: 'Missing or invalid "injury_distribution" object' };
        }
        
        // Check for required injury types
        const requiredTypes = ['Disease', 'Non-Battle Injury', 'Battle Injury'];
        const missing = requiredTypes.filter(type => !(type in config.injury_distribution));
        
        if (missing.length > 0) {
            return { valid: false, message: `Missing injury types: ${missing.join(', ')}` };
        }
        
        // Check if percentages are valid
        const total = Object.values(config.injury_distribution).reduce((sum, val) => sum + (val || 0), 0);
        if (Math.abs(total - 1) > 0.01) {
            return { valid: false, message: `Injury percentages should sum to 1.0 (currently ${total.toFixed(2)})` };
        }
        
        return { valid: true, message: 'Injury distribution is properly configured' };
        
    } catch (e) {
        return { valid: false, message: `JSON syntax error: ${e.message}` };
    }
}

// Test the validation
console.log('Testing default fronts content:');
const frontsResult = validateBattleFronts(frontsContent);
console.log('Fronts validation:', frontsResult);

console.log('\nTesting default injuries content:');
const injuriesResult = validateInjuries(injuriesContent);
console.log('Injuries validation:', injuriesResult);

console.log('\nBoth valid?', frontsResult.valid && injuriesResult.valid);