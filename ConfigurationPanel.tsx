{/* ConfigurationPanel.tsx */}
import React, { useState, useEffect } from 'react';
import FrontEditor from './FrontEditor';
import FacilityEditor from './FacilityEditor'; // Import the FacilityEditor component

// Define interfaces for the configuration objects based on schemas_config.py
// These might be simplified versions for UI state or imported if shareable
interface FrontConfigUI {
    id: string;
    name: string;
    description?: string;
    nationality_distribution: { [key: string]: number }; // nationality code -> percentage
    casualty_rate?: number;
}

interface FacilityConfigUI {
    id: string;
    name: string;
    description?: string;
    capacity?: number;
    kia_rate: number;
    rtd_rate: number;
}

interface ConfigTemplateUI {
    id?: string;
    name: string;
    description?: string;
    front_configs: FrontConfigUI[];
    facility_configs: FacilityConfigUI[];
    total_patients: number;
    injury_distribution: { [key: string]: number };
    version?: number;
    parent_config_id?: string;
}

interface StaticFrontNationUI {
    iso: string;
    ratio: number;
}

interface StaticFrontDefinitionUI {
    name: string;
    ratio: number;
    nations: StaticFrontNationUI[];
}

// Helper to generate unique IDs for new items
const generateId = () => `temp_${Math.random().toString(36).substr(2, 9)}`;

const ConfigurationPanel: React.FC = () => {
    const [savedConfigs, setSavedConfigs] = useState<ConfigTemplateUI[]>([]);
    const [activeConfig, setActiveConfig] = useState<ConfigTemplateUI | null>(null);
    
    // Separate states for editable parts of the activeConfig
    const [fronts, setFronts] = useState<FrontConfigUI[]>([]);
    const [facilities, setFacilities] = useState<FacilityConfigUI[]>([]);
    const [configName, setConfigName] = useState<string>("");
    const [configDescription, setConfigDescription] = useState<string>("");
    const [totalPatients, setTotalPatients] = useState<number>(1000);
    const [injuryDistribution, setInjuryDistribution] = useState<{ [key: string]: number }>({});
    const [availableNationalities, setAvailableNationalities] = useState<{ code: string; name: string }[]>([]);
    const [staticFrontsData, setStaticFrontsData] = useState<StaticFrontDefinitionUI[] | null>(null);


    useEffect(() => {
        const fetchInitialData = async () => {
            // Fetch saved configurations
            try {
                const responseConfigs = await fetch('/api/v1/configurations/', {
                    method: 'GET',
                    headers: { 
                        'Accept': 'application/json',
                        'X-API-KEY': 'your_secret_api_key_here' // Placeholder API Key
                    }
                });
                if (!responseConfigs.ok) throw new Error(`Fetch configs failed: ${responseConfigs.status}`);
                const dataConfigs: ConfigTemplateUI[] = await responseConfigs.json();
                setSavedConfigs(dataConfigs);
                console.log("Fetched saved configurations:", dataConfigs);
            } catch (error) {
                console.error("Error fetching configurations:", error);
            }

            // Fetch available nationalities
            try {
                const responseNats = await fetch('/api/v1/configurations/reference/nationalities/', {
                     method: 'GET',
                     headers: {
                         'Accept': 'application/json',
                         'X-API-KEY': 'your_secret_api_key_here' // Placeholder API Key
                     }
                });
                if (!responseNats.ok) throw new Error(`Fetch nationalities failed: ${responseNats.status}`);
                const dataNats: { code: string; name: string }[] = await responseNats.json();
                setAvailableNationalities(dataNats);
                console.log("Fetched available nationalities:", dataNats);
            } catch (error) {
                console.error("Error fetching nationalities:", error);
            }

            // Fetch static front definitions
            try {
                const responseStaticFronts = await fetch('/api/v1/configurations/reference/static-fronts/', {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'X-API-KEY': 'your_secret_api_key_here' // Placeholder API Key
                    }
                });
                if (!responseStaticFronts.ok) {
                    if (responseStaticFronts.status === 404) { // Or however your API indicates "not found / not configured"
                        console.log("Static fronts configuration file (fronts_config.json) not found or empty on backend.");
                        setStaticFrontsData(null); // Explicitly set to null or empty array
                    } else {
                        throw new Error(`Fetch static fronts failed: ${responseStaticFronts.status}`);
                    }
                } else {
                    const dataStaticFronts: StaticFrontDefinitionUI[] | null = await responseStaticFronts.json();
                    // API might return null if file not found/empty and response_model is Optional[...]
                    setStaticFrontsData(dataStaticFronts);
                    console.log("Fetched static front definitions:", dataStaticFronts);
                }
            } catch (error) {
                console.error("Error fetching static front definitions:", error);
                setStaticFrontsData(null); // Ensure it's null on error
            }
        };

        fetchInitialData();
    }, []);

    const loadConfigToEdit = (config: ConfigTemplateUI) => {
        setActiveConfig(config);
        setConfigName(config.name);
        setConfigDescription(config.description || "");
        setFronts([...config.front_configs]); // Deep copy for editing
        setFacilities([...config.facility_configs]); // Deep copy
        setTotalPatients(config.total_patients);
        setInjuryDistribution({...config.injury_distribution});
    };
    
    const handleAddNewFront = () => {
        setFronts([...fronts, {
            id: generateId(),
            name: "New Front",
            nationality_distribution: {},
            casualty_rate: 0.1
        }]);
    };

    const handleAddNewFacility = () => {
        setFacilities([...facilities, {
            id: generateId(),
            name: "New Facility",
            kia_rate: 0.1,
            rtd_rate: 0.3
        }]);
    };

    // TODO: Implement update/delete for fronts and facilities
    
    const handleSaveConfiguration = async () => {
        if (!configName.trim()) {
            alert("Configuration name cannot be empty.");
            return;
        }
        // Basic validation for distributions (should sum to 100)
        for (const front of fronts) {
            const natTotal = Object.values(front.nationality_distribution).reduce((s, p) => s + p, 0);
            if (Math.abs(natTotal - 100.0) > 0.1 && Object.values(front.nationality_distribution).length > 0) {
                alert(`Nationality distribution for front "${front.name}" must sum to 100%. Currently: ${natTotal.toFixed(1)}%`);
                return;
            }
        }
        const injuryTotal = Object.values(injuryDistribution).reduce((s, p) => s + p, 0);
        if (Math.abs(injuryTotal - 100.0) > 0.1 && Object.values(injuryDistribution).length > 0) {
            alert(`Injury distribution must sum to 100%. Currently: ${injuryTotal.toFixed(1)}%`);
            return;
        }


        const configToSave: Omit<ConfigTemplateUI, 'id' | 'created_at' | 'updated_at' | 'version'> & { parent_config_id?: string, version?: number} = {
            name: configName,
            description: configDescription || undefined,
            front_configs: fronts,
            facility_configs: facilities,
            total_patients: totalPatients,
            injury_distribution: injuryDistribution,
            parent_config_id: activeConfig?.parent_config_id, // Preserve parent if updating a derived config
            version: activeConfig?.id ? (activeConfig.version || 0) + 1 : 1 // Increment version if updating, else 1
        };
        
        // If it's an update to an existing config, use its ID for parent_config_id if creating a new version
        // Or, if simply updating, the API PUT should handle versioning.
        // For now, let's assume save always creates new or updates existing with new version.
        // The API PUT /configurations/{id} updates in place. POST / creates new.

        let endpoint = '/api/v1/configurations/';
        let method = 'POST';

        if (activeConfig && activeConfig.id && !activeConfig.id.startsWith('temp_')) { // Check if it's a saved config being edited
            // Option 1: Update existing (PUT) - API should handle version increment or use optimistic locking
            // endpoint = `/api/v1/configurations/${activeConfig.id}`;
            // method = 'PUT';
            // Option 2: Save as new version (POST, with parent_id set) - this requires more complex UI/UX
            // For simplicity, let's assume we are creating a new one or updating an existing one.
            // If activeConfig.id exists, we are updating.
            endpoint = `/api/v1/configurations/${activeConfig.id}`;
            method = 'PUT';
            // The backend ConfigurationRepository.update_configuration will set updated_at.
            // Versioning logic on backend might increment version or require it in payload.
            // Our Pydantic ConfigurationTemplateCreate does not include 'id', 'created_at', 'updated_at'.
            // The backend PUT should handle setting updated_at. Version might be auto-incremented or taken from payload.
            // Let's ensure the payload for PUT matches ConfigurationTemplateCreate.
        }


        try {
            const payloadForApi: any = { ...configToSave };
            // Remove fields not in ConfigurationTemplateCreate for POST/PUT
            delete payloadForApi.id; 
            delete payloadForApi.created_at;
            delete payloadForApi.updated_at;
            // Version might be handled by backend on PUT, or could be part of payload if API supports it.
            // For now, ConfigurationTemplateCreate allows version.

            const response = await fetch(endpoint, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-API-KEY': 'your_secret_api_key_here' // Placeholder
                },
                body: JSON.stringify(payloadForApi)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`Failed to save configuration: ${response.status} - ${errorData.detail || response.statusText}`);
            }

            const savedOrUpdatedConfig: ConfigTemplateUI = await response.json();
            alert(`Configuration "${savedOrUpdatedConfig.name}" saved successfully!`);
            
            // Refresh list of saved configs and update active one
            const newSavedConfigs = [...savedConfigs];
            const existingIndex = newSavedConfigs.findIndex(c => c.id === savedOrUpdatedConfig.id);
            if (existingIndex !== -1) {
                newSavedConfigs[existingIndex] = savedOrUpdatedConfig;
            } else {
                newSavedConfigs.push(savedOrUpdatedConfig);
            }
            setSavedConfigs(newSavedConfigs);
            loadConfigToEdit(savedOrUpdatedConfig); // Load the saved version (with ID, timestamps) into form

        } catch (error) {
            console.error("Error saving configuration:", error);
            alert(`Error saving configuration: ${error instanceof Error ? error.message : String(error)}`);
        }
    };

    const handleResetForm = () => {
        setActiveConfig(null);
        setConfigName("New Scenario");
        setConfigDescription("");
        setFronts([]);
        setFacilities([]);
        setTotalPatients(1000);
        setInjuryDistribution({});
    };


    return (
        <div className="configuration-panel p-3" style={{ fontFamily: 'Arial, sans-serif' }}>
            <h2>Scenario Configuration Panel</h2>
            <hr />

            <div style={{ marginBottom: '20px' }}>
                <h4>Load Existing Configuration</h4>
                <select 
                    onChange={(e) => {
                        const selectedId = e.target.value;
                        const configToLoad = savedConfigs.find(c => c.id === selectedId);
                        if (configToLoad) {
                            loadConfigToEdit(configToLoad);
                        }
                    }}
                    defaultValue=""
                    style={{ padding: '8px', marginRight: '10px', minWidth: '200px' }}
                >
                    <option value="" disabled>Select a configuration...</option>
                    {savedConfigs.map(conf => (
                        <option key={conf.id} value={conf.id}>{conf.name} (v{conf.version})</option>
                    ))}
                </select>
                <button onClick={() => { /* TODO: Clear form for new config */ setActiveConfig(null); setConfigName("New Config"); /* reset other fields */ }} style={{ padding: '8px' }}>
                    Create New
                </button>
            </div>

            <div style={{ marginBottom: '20px' }}>
                <h4>Configuration Details</h4>
                <div>
                    <label htmlFor="configName" style={{ marginRight: '10px' }}>Name:</label>
                    <input type="text" id="configName" value={configName} onChange={(e) => setConfigName(e.target.value)} placeholder="Configuration Name" style={{ padding: '5px', width: '300px' }}/>
                </div>
                <div style={{ marginTop: '10px' }}>
                    <label htmlFor="configDesc" style={{ marginRight: '10px' }}>Description:</label>
                    <textarea id="configDesc" value={configDescription} onChange={(e) => setConfigDescription(e.target.value)} placeholder="Optional Description" style={{ padding: '5px', width: '300px', minHeight: '60px' }}/>
                </div>
                 <div style={{ marginTop: '10px' }}>
                    <label htmlFor="totalPatients" style={{ marginRight: '10px' }}>Total Patients:</label>
                    <input type="number" id="totalPatients" value={totalPatients} onChange={(e) => setTotalPatients(parseInt(e.target.value,10) || 0)} style={{ padding: '5px', width: '100px' }}/>
                </div>
                {/* TODO: UI for injury_distribution */}
            </div>


            <section style={{ marginBottom: '20px' }}>
                <h4>Combat Fronts (Editable Scenario Definition)</h4>
                <p style={{fontSize: '0.9em', color: '#555'}}>
                    Define fronts below if NOT using the static <code>fronts_config.json</code>. 
                    If static fronts (shown below) are active, they will override these settings.
                </p>
                <button onClick={handleAddNewFront} style={{ padding: '8px', marginBottom: '10px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px' }}>
                    Add Editable Front
                </button>
                {fronts.map((front, index) => (
                    <FrontEditor
                        key={front.id}
                        front={front}
                        availableNationalities={availableNationalities}
                        onUpdate={(updatedFront) => {
                            const newFronts = [...fronts];
                            newFronts[index] = updatedFront;
                            setFronts(newFronts);
                        }}
                        onDelete={() => {
                            setFronts(fronts.filter(f => f.id !== front.id));
                        }}
                    />
                ))}
            </section>

            {staticFrontsData && staticFrontsData.length > 0 && (
                <section style={{ marginBottom: '20px', padding: '15px', border: '1px solid #007bff', borderRadius: '5px', backgroundColor: '#e7f3ff' }}>
                    <h4>Static Fronts Configuration (from <code>fronts_config.json</code> - Read-Only)</h4>
                    <p style={{color: '#004085', fontWeight: 'bold'}}>
                        The following static front configuration is active and will be used for patient generation, overriding any editable fronts defined above.
                    </p>
                    {staticFrontsData.map((front, index) => (
                        <div key={index} style={{ border: '1px solid #ccc', borderRadius: '4px', padding: '10px', marginBottom: '10px', backgroundColor: 'white' }}>
                            <h5>{front.name} (Ratio: {(front.ratio * 100).toFixed(1)}%)</h5>
                            {front.nations && front.nations.length > 0 ? (
                                <ul style={{ listStyleType: 'disc', paddingLeft: '20px' }}>
                                    {front.nations.map((nation, nIndex) => (
                                        <li key={nIndex}>
                                            {nation.iso}: {(nation.ratio * 100).toFixed(1)}%
                                        </li>
                                    ))}
                                </ul>
                            ) : <p>No nations specified for this front.</p>}
                        </div>
                    ))}
                </section>
            )}
             {staticFrontsData === null && (
                 <section style={{ marginBottom: '20px', padding: '15px', border: '1px solid #ffc107', borderRadius: '5px', backgroundColor: '#fff3cd' }}>
                    <h4>Static Fronts Configuration (from <code>fronts_config.json</code>)</h4>
                    <p style={{color: '#856404'}}>
                        Static <code>fronts_config.json</code> was not found or is empty/invalid. Editable scenario fronts (if defined above) will be used.
                    </p>
                </section>
            )}


            <section style={{ marginBottom: '20px' }}>
                <h4>Medical Facilities (Evacuation Chain - Order Matters)</h4>
                <button onClick={handleAddNewFacility} style={{ padding: '8px', marginBottom: '10px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px' }}>
                    Add Facility
                </button>
                {/* TODO: Implement drag-and-drop for reordering facilities */}
                {facilities.map((facility, index) => (
                    <FacilityEditor
                        key={facility.id}
                        facility={facility}
                        onUpdate={(updatedFacility) => {
                            const newFacilities = [...facilities];
                            newFacilities[index] = updatedFacility;
                            setFacilities(newFacilities);
                        }}
                        onDelete={() => {
                            setFacilities(facilities.filter(f => f.id !== facility.id));
                        }}
                    />
                ))}
            </section>
            
            <section style={{ marginTop: '20px', padding: '15px', border: '1px solid #eee', borderRadius: '5px', backgroundColor: '#fdfdfd' }}>
                <h4>Quick Preview & Validation</h4>
                {configName && <p><strong>Scenario Name:</strong> {configName}</p>}
                <p><strong>Total Patients to Generate:</strong> {totalPatients}</p>
                
                <h5>Fronts Summary:</h5>
                {fronts.length > 0 ? (
                    <ul>
                        {fronts.map(f => (
                            <li key={f.id}>
                                {f.name || "(Unnamed Front)"}: 
                                Casualty Rate: {f.casualty_rate === undefined ? 'N/A' : (f.casualty_rate * 100).toFixed(1) + '%'}
                                | Nationalities: {Object.keys(f.nationality_distribution).join(', ') || 'None'}
                                (Total Dist: {Object.values(f.nationality_distribution).reduce((s, p) => s + p, 0).toFixed(1)}%)
                            </li>
                        ))}
                    </ul>
                ) : <p>No fronts configured.</p>}

                <h5>Facilities Summary:</h5>
                {facilities.length > 0 ? (
                     <p>Evacuation Chain: {facilities.map(f => f.name || "(Unnamed)").join(' → ')}</p>
                ) : <p>No facilities configured.</p>}

                <h5>Injury Distribution:</h5>
                {Object.keys(injuryDistribution).length > 0 ? (
                    <ul>
                        {Object.entries(injuryDistribution).map(([type, percent]) => (
                            <li key={type}>{type}: {percent.toFixed(1)}%</li>
                        ))}
                         <li>Total: {Object.values(injuryDistribution).reduce((s, p) => s + p, 0).toFixed(1)}%</li>
                    </ul>
                ) : <p>No injury distribution configured.</p>}
            </section>
            
            <hr />
            <div className="actions" style={{ marginTop: '20px' }}>
                <button onClick={handleSaveConfiguration} style={{ padding: '10px 15px', marginRight: '10px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px' }}>
                    Save Configuration
                </button>
                <button onClick={handleResetForm} style={{ padding: '10px 15px', marginRight: '10px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px' }}>
                    Clear Form / New
                </button>
                {/* Apply might not be needed if this panel is part of the main generation page */}
                {/* <button onClick={() => console.log("TODO: Apply Configuration to Generator")} style={{ padding: '10px 15px', backgroundColor: '#17a2b8', color: 'white', border: 'none', borderRadius: '4px' }}>
                    Apply to Generator
                </button> */}
            </div>
        </div>
    );
};

// This component would typically be rendered into a DOM element by another script,
// similar to enhanced-visualization-dashboard.tsx, or imported into a larger React app.
// For example, if it's meant to be a standalone bundle:
import ReactDOM from 'react-dom/client';

const renderConfigurationPanel = () => {
    const container = document.getElementById('reactConfigurationPanelRoot');
    if (container) {
      const root = ReactDOM.createRoot(container);
      root.render(
        <React.StrictMode>
          <ConfigurationPanel />
        </React.StrictMode>
      );
    } else {
        console.warn("Root element 'reactConfigurationPanelRoot' not found for ConfigurationPanel.");
    }
};

// Check if we are in a browser environment before trying to render
if (typeof window !== 'undefined' && typeof document !== 'undefined') {
    // Auto-render if the specific root element exists, or provide a function to call
    if (document.getElementById('reactConfigurationPanelRoot')) {
        renderConfigurationPanel();
    } else {
        // Expose the render function globally if the root isn't immediately available,
        // allowing an external script to call it once the DOM is ready.
        (window as any).renderReactConfigurationPanel = renderConfigurationPanel;
        console.log("ConfigurationPanel: Root element not found. Call window.renderReactConfigurationPanel() to render.");
    }
}


export default ConfigurationPanel;
