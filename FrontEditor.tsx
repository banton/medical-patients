{/* FrontEditor.tsx */}
import React, { useEffect, useState } from 'react';

// Represents a single item in the nationality distribution list
interface NationalityDistributionItemState {
    id: string; // Unique client-side ID for React keys
    nationality_code: string; // ISO code, e.g., "USA"
    percentage: number;
}

// Updated FrontConfigUI to use the new nationality distribution structure
interface FrontConfigUI {
    id: string; // This is the front's actual ID from the backend or a temporary one for new fronts
    name: string;
    description?: string;
    nationality_distribution: NationalityDistributionItemState[];
    casualty_rate?: number;
}

interface FrontEditorProps {
    front: FrontConfigUI;
    onUpdate: (updatedFront: FrontConfigUI) => void;
    onDelete: () => void;
    availableNationalities: { code: string; name: string }[];
}

const FrontEditor: React.FC<FrontEditorProps> = ({ front, onUpdate, onDelete, availableNationalities }) => {
    // Local state to manage the front being edited, ensuring nationality_distribution is always an array
    const [editableFront, setEditableFront] = useState<FrontConfigUI>(() => {
        // Ensure nationality_distribution is initialized correctly
        const initialDistribution = front.nationality_distribution && front.nationality_distribution.length > 0
            ? front.nationality_distribution
            : [{ id: `nat-${Date.now()}`, nationality_code: availableNationalities[0]?.code || '', percentage: 100 }];
        return { ...front, nationality_distribution: initialDistribution };
    });

    // Effect to update local state if the parent 'front' prop changes
    useEffect(() => {
        const currentDistribution = front.nationality_distribution && front.nationality_distribution.length > 0
            ? front.nationality_distribution
            : [{ id: `nat-${Date.now()}`, nationality_code: availableNationalities[0]?.code || '', percentage: 100 }];
        setEditableFront({ ...front, nationality_distribution: currentDistribution });
    }, [front, availableNationalities]);


    const handleInputChange = (field: keyof Omit<FrontConfigUI, 'nationality_distribution'>, value: any) => {
        const updatedFront = { ...editableFront, [field]: value };
        setEditableFront(updatedFront);
        onUpdate(updatedFront);
    };

    const handleNatDistChange = (itemId: string, field: 'nationality_code' | 'percentage', value: string | number) => {
        let newPercentage = typeof value === 'number' ? value : parseFloat(value as string);

        const newDistribution = editableFront.nationality_distribution.map(item => {
            if (item.id === itemId) {
                if (field === 'nationality_code') {
                    // Check for duplicates
                    const isDuplicate = editableFront.nationality_distribution.some(
                        existingItem => existingItem.id !== itemId && existingItem.nationality_code === value
                    );
                    if (isDuplicate) {
                        alert(`Nationality ${value} is already selected. Please choose a different one.`);
                        return item; // Return original item if duplicate
                    }
                    return { ...item, nationality_code: value as string };
                } else if (field === 'percentage') {
                    if (!isNaN(newPercentage) && newPercentage >= 0 && newPercentage <= 100) {
                        return { ...item, percentage: newPercentage };
                    } else if (value === "") {
                         return { ...item, percentage: 0 }; // Treat empty as 0 for calculation
                    }
                }
            }
            return item;
        });
        const updatedFront = { ...editableFront, nationality_distribution: newDistribution };
        setEditableFront(updatedFront);
        onUpdate(updatedFront);
    };

    const addNationalityEntry = () => {
        // Find first available nationality not already in the list
        const currentNatCodes = editableFront.nationality_distribution.map(item => item.nationality_code);
        const firstAvailable = availableNationalities.find(n => !currentNatCodes.includes(n.code));

        const newEntry: NationalityDistributionItemState = {
            id: `nat-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`, // More unique ID
            nationality_code: firstAvailable ? firstAvailable.code : '', // Default to first available or empty
            percentage: 0,
        };
        const updatedFront = {
            ...editableFront,
            nationality_distribution: [...editableFront.nationality_distribution, newEntry],
        };
        setEditableFront(updatedFront);
        onUpdate(updatedFront);
    };

    const removeNationalityEntry = (itemId: string) => {
        if (editableFront.nationality_distribution.length <= 1) {
            alert("At least one nationality must be present in the distribution.");
            return;
        }
        const newDistribution = editableFront.nationality_distribution.filter(item => item.id !== itemId);
        const updatedFront = { ...editableFront, nationality_distribution: newDistribution };
        setEditableFront(updatedFront);
        onUpdate(updatedFront);
    };
    
    const totalPercentage = editableFront.nationality_distribution.reduce((sum, item) => sum + (item.percentage || 0), 0);

    return (
        <div style={{ border: '1px solid #e0e0e0', padding: '15px', marginBottom: '15px', borderRadius: '5px', backgroundColor: '#f9f9f9' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h5 style={{ margin: 0 }}>Edit Front: {editableFront.name || '(New Front)'}</h5>
                <button onClick={onDelete} style={{ backgroundColor: '#dc3545', color: 'white', border: 'none', padding: '5px 10px', borderRadius: '4px', cursor: 'pointer' }}>Delete Front</button>
            </div>
            <hr />
            <div style={{ marginBottom: '10px' }}>
                <label htmlFor={`frontName-${editableFront.id}`} style={{ display: 'block', marginBottom: '5px' }}>Name:</label>
                <input
                    type="text"
                    id={`frontName-${editableFront.id}`}
                    value={editableFront.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    placeholder="Front Name"
                    style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                />
            </div>
            <div style={{ marginBottom: '10px' }}>
                <label htmlFor={`frontDesc-${editableFront.id}`} style={{ display: 'block', marginBottom: '5px' }}>Description:</label>
                <textarea
                    id={`frontDesc-${editableFront.id}`}
                    value={editableFront.description || ''}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    placeholder="Optional Description"
                    style={{ width: '100%', padding: '8px', minHeight: '60px', boxSizing: 'border-box' }}
                />
            </div>
            <div style={{ marginBottom: '10px' }}>
                <label htmlFor={`frontCasualtyRate-${editableFront.id}`} style={{ display: 'block', marginBottom: '5px' }}>Casualty Rate (0.0 - 1.0):</label>
                <input
                    type="number"
                    id={`frontCasualtyRate-${editableFront.id}`}
                    value={editableFront.casualty_rate === undefined ? '' : editableFront.casualty_rate}
                    onChange={(e) => handleInputChange('casualty_rate', e.target.value === '' ? undefined : parseFloat(e.target.value))}
                    placeholder="e.g., 0.1 for 10%"
                    step="0.01" min="0" max="1"
                    style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                />
            </div>
            <div>
                <h6>Nationality Distribution (%)</h6>
                {editableFront.nationality_distribution.map((item) => (
                    <div key={item.id} style={{ display: 'flex', alignItems: 'center', marginBottom: '8px', padding: '5px', border: '1px solid #eee', borderRadius: '4px' }}>
                        <select
                            value={item.nationality_code}
                            onChange={(e) => handleNatDistChange(item.id, 'nationality_code', e.target.value)}
                            style={{ flexGrow: 1, padding: '8px', marginRight: '10px', minWidth: '150px' }}
                        >
                            <option value="">-- Select Nationality --</option>
                            {availableNationalities.map(nat => (
                                <option key={nat.code} value={nat.code}>
                                    {nat.name} ({nat.code})
                                </option>
                            ))}
                        </select>
                        <input
                            type="number"
                            value={item.percentage}
                            onChange={(e) => handleNatDistChange(item.id, 'percentage', e.target.value)}
                            placeholder="%"
                            min="0" max="100" step="0.1"
                            style={{ width: '80px', padding: '8px', marginRight: '10px' }}
                        />
                        <button 
                            onClick={() => removeNationalityEntry(item.id)}
                            disabled={editableFront.nationality_distribution.length <= 1}
                            style={{
                                backgroundColor: editableFront.nationality_distribution.length <= 1 ? '#ccc' : '#ff4d4f',
                                color: 'white', border: 'none', padding: '8px 12px', borderRadius: '4px', cursor: editableFront.nationality_distribution.length <= 1 ? 'not-allowed' : 'pointer'
                            }}
                        >
                            Remove
                        </button>
                    </div>
                ))}
                <button onClick={addNationalityEntry} style={{ marginTop: '10px', padding: '8px 15px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                    Add Nationality
                </button>
                <p style={{ fontSize: '0.9em', color: totalPercentage !== 100 ? 'red' : '#555', marginTop: '10px' }}>
                    Total: {totalPercentage.toFixed(1)}% (must be 100%)
                </p>
            </div>
        </div>
    );
};

export default FrontEditor;
