{/* FrontEditor.tsx */}
import React from 'react';

interface FrontConfigUI {
    id: string;
    name: string;
    description?: string;
    nationality_distribution: { [key: string]: number };
    casualty_rate?: number;
}

interface FrontEditorProps {
    front: FrontConfigUI;
    onUpdate: (updatedFront: FrontConfigUI) => void;
    onDelete: () => void;
    availableNationalities: { code: string; name: string }[]; // For dropdown
}

const FrontEditor: React.FC<FrontEditorProps> = ({ front, onUpdate, onDelete, availableNationalities }) => {
    const handleInputChange = (field: keyof FrontConfigUI, value: any) => {
        onUpdate({ ...front, [field]: value });
    };

    const handleNatDistChange = (natCode: string, percentage: string) => {
        const newDist = { ...front.nationality_distribution };
        const numPercentage = parseFloat(percentage);
        if (!isNaN(numPercentage) && numPercentage >= 0 && numPercentage <= 100) {
            newDist[natCode] = numPercentage;
        } else if (percentage === "") {
            delete newDist[natCode]; // Remove if empty
        }
        onUpdate({ ...front, nationality_distribution: newDist });
    };
    
    const addNationalityToDistribution = () => {
        // Find a nationality not yet in the distribution
        const currentNatCodes = Object.keys(front.nationality_distribution);
        const newNat = availableNationalities.find(n => !currentNatCodes.includes(n.code));
        if (newNat) {
            handleNatDistChange(newNat.code, "0");
        } else {
            alert("All available nationalities are already added or no nationalities available.");
        }
    };


    return (
        <div style={{ border: '1px solid #e0e0e0', padding: '15px', marginBottom: '15px', borderRadius: '5px', backgroundColor: '#f9f9f9' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h5 style={{ margin: 0 }}>Edit Front: {front.name || '(New Front)'}</h5>
                <button onClick={onDelete} style={{ backgroundColor: '#dc3545', color: 'white', border: 'none', padding: '5px 10px', borderRadius: '4px', cursor: 'pointer' }}>Delete Front</button>
            </div>
            <hr />
            <div style={{ marginBottom: '10px' }}>
                <label htmlFor={`frontName-${front.id}`} style={{ display: 'block', marginBottom: '5px' }}>Name:</label>
                <input
                    type="text"
                    id={`frontName-${front.id}`}
                    value={front.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    placeholder="Front Name"
                    style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                />
            </div>
            <div style={{ marginBottom: '10px' }}>
                <label htmlFor={`frontDesc-${front.id}`} style={{ display: 'block', marginBottom: '5px' }}>Description:</label>
                <textarea
                    id={`frontDesc-${front.id}`}
                    value={front.description || ''}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    placeholder="Optional Description"
                    style={{ width: '100%', padding: '8px', minHeight: '60px', boxSizing: 'border-box' }}
                />
            </div>
            <div style={{ marginBottom: '10px' }}>
                <label htmlFor={`frontCasualtyRate-${front.id}`} style={{ display: 'block', marginBottom: '5px' }}>Casualty Rate (0.0 - 1.0):</label>
                <input
                    type="number"
                    id={`frontCasualtyRate-${front.id}`}
                    value={front.casualty_rate === undefined ? '' : front.casualty_rate}
                    onChange={(e) => handleInputChange('casualty_rate', e.target.value === '' ? undefined : parseFloat(e.target.value))}
                    placeholder="e.g., 0.1 for 10%"
                    step="0.01" min="0" max="1"
                    style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                />
            </div>
            <div>
                <h6>Nationality Distribution (%)</h6>
                {Object.entries(front.nationality_distribution).map(([natCode, percentage]) => (
                    <div key={natCode} style={{ display: 'flex', alignItems: 'center', marginBottom: '5px' }}>
                        <span style={{ width: '100px', marginRight: '10px' }}>{availableNationalities.find(n => n.code === natCode)?.name || natCode}:</span>
                        <input
                            type="number"
                            value={percentage}
                            onChange={(e) => handleNatDistChange(natCode, e.target.value)}
                            placeholder="%"
                            min="0" max="100" step="0.1"
                            style={{ width: '80px', padding: '5px', marginRight: '10px' }}
                        />
                        <button onClick={() => {
                            const newDist = { ...front.nationality_distribution };
                            delete newDist[natCode];
                            onUpdate({ ...front, nationality_distribution: newDist });
                        }} style={{backgroundColor: 'transparent', border: 'none', color: 'red', cursor: 'pointer'}}>&#x2716;</button> {/* Cross mark */}
                    </div>
                ))}
                 <button onClick={addNationalityToDistribution} style={{marginTop: '5px', padding: '5px 10px'}}>Add Nationality</button>
                <p style={{fontSize: '0.9em', color: '#555'}}>Total: {Object.values(front.nationality_distribution).reduce((sum, val) => sum + (val || 0), 0).toFixed(1)}% (should be 100%)</p>
            </div>
        </div>
    );
};

export default FrontEditor;
