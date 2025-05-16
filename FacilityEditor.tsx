{/* FacilityEditor.tsx */}
import React from 'react';

interface FacilityConfigUI {
    id: string;
    name: string;
    description?: string;
    capacity?: number;
    kia_rate: number;
    rtd_rate: number;
}

interface FacilityEditorProps {
    facility: FacilityConfigUI;
    onUpdate: (updatedFacility: FacilityConfigUI) => void;
    onDelete: () => void;
    // availableCapabilities?: string[]; // Example if facilities had selectable capabilities
}

const FacilityEditor: React.FC<FacilityEditorProps> = ({ facility, onUpdate, onDelete }) => {
    const handleInputChange = (field: keyof FacilityConfigUI, value: any) => {
        let processedValue = value;
        if (field === 'capacity') {
            processedValue = value === '' ? undefined : parseInt(value, 10);
            if (value !== '' && (isNaN(processedValue as number) || (processedValue as number) < 0)) {
                 alert(`Capacity must be a positive number or empty.`);
                 processedValue = facility.capacity; // Revert to old value or handle as error
            }
        } else if (field === 'kia_rate' || field === 'rtd_rate') {
            processedValue = value === '' ? undefined : parseFloat(value);
            // Allow empty to clear, Pydantic will validate. Only validate format here.
            if (value !== '' && typeof processedValue === 'number' && (isNaN(processedValue) || processedValue < 0 || processedValue > 1)) {
                 alert(`${field} must be between 0.0 and 1.0 if specified.`);
                 processedValue = field === 'kia_rate' ? facility.kia_rate : facility.rtd_rate; // Revert
            } else if (value === '') {
                processedValue = undefined; // Explicitly set to undefined if cleared
            }
        }
        onUpdate({ ...facility, [field]: processedValue });
    };

    return (
        <div style={{ border: '1px solid #e0e0e0', padding: '15px', marginBottom: '15px', borderRadius: '5px', backgroundColor: '#f9f9f9' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h5 style={{ margin: 0 }}>Edit Facility: {facility.name || '(New Facility)'}</h5>
                <button onClick={onDelete} style={{ backgroundColor: '#dc3545', color: 'white', border: 'none', padding: '5px 10px', borderRadius: '4px', cursor: 'pointer' }}>Delete Facility</button>
            </div>
            <hr />
            <div style={{ marginBottom: '10px' }}>
                <label htmlFor={`facilityName-${facility.id}`} style={{ display: 'block', marginBottom: '5px' }}>Name:</label>
                <input
                    type="text"
                    id={`facilityName-${facility.id}`}
                    value={facility.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    placeholder="Facility Name"
                    style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                />
            </div>
            <div style={{ marginBottom: '10px' }}>
                <label htmlFor={`facilityDesc-${facility.id}`} style={{ display: 'block', marginBottom: '5px' }}>Description:</label>
                <textarea
                    id={`facilityDesc-${facility.id}`}
                    value={facility.description || ''}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    placeholder="Optional Description"
                    style={{ width: '100%', padding: '8px', minHeight: '60px', boxSizing: 'border-box' }}
                />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                <div style={{ flex: 1, marginRight: '10px' }}>
                    <label htmlFor={`facilityCap-${facility.id}`} style={{ display: 'block', marginBottom: '5px' }}>Capacity:</label>
                    <input
                        type="number"
                        id={`facilityCap-${facility.id}`}
                        value={facility.capacity === undefined ? '' : facility.capacity}
                        onChange={(e) => handleInputChange('capacity', e.target.value)}
                        placeholder="e.g., 50"
                        min="0"
                        style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                    />
                </div>
                <div style={{ flex: 1, marginRight: '10px' }}>
                    <label htmlFor={`facilityKiaRate-${facility.id}`} style={{ display: 'block', marginBottom: '5px' }}>KIA Rate (0.0-1.0):</label>
                    <input
                        type="number"
                        id={`facilityKiaRate-${facility.id}`}
                        value={facility.kia_rate === undefined ? '' : facility.kia_rate}
                        onChange={(e) => handleInputChange('kia_rate', e.target.value)}
                        placeholder="e.g., 0.1"
                        step="0.01" min="0" max="1"
                        style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                    />
                </div>
                <div style={{ flex: 1 }}>
                    <label htmlFor={`facilityRtdRate-${facility.id}`} style={{ display: 'block', marginBottom: '5px' }}>RTD Rate (0.0-1.0):</label>
                    <input
                        type="number"
                        id={`facilityRtdRate-${facility.id}`}
                        value={facility.rtd_rate === undefined ? '' : facility.rtd_rate}
                        onChange={(e) => handleInputChange('rtd_rate', e.target.value)}
                        placeholder="e.g., 0.3"
                        step="0.01" min="0" max="1"
                        style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                    />
                </div>
            </div>
        </div>
    );
};

export default FacilityEditor;
