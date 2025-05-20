{/* ConfigurationPanel.tsx */}
import React, { useState, useEffect } from 'react';
import FrontEditor from './FrontEditor';
import FacilityEditor from './FacilityEditor';

// --- UI State Interfaces (include client-side temporary IDs) ---
interface NationalityDistributionItemState {
    id: string; 
    nationality_code: string; 
    percentage: number;
}

interface FrontConfigUI {
    id: string;
    name: string;
    description?: string;
    nationality_distribution: NationalityDistributionItemState[]; 
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
    injury_distribution: { [key: string]: number }; // Reverted to dictionary
    version?: number;
    parent_config_id?: string;
}

// --- Static Data Interfaces ---
interface StaticFrontNationUI {
    iso: string;
    ratio: number;
}

interface StaticFrontDefinitionUI {
    name: string;
    ratio: number;
    nations: StaticFrontNationUI[];
}

// --- API Payload Interfaces ---
interface ApiNationalityDistributionItem {
    nationality_code: string;
    percentage: number;
}

interface ApiFrontConfig {
    id: string; 
    name: string;
    description?: string;
    nationality_distribution: ApiNationalityDistributionItem[];
    casualty_rate?: number;
}

interface ApiConfigTemplatePayload {
    name: string;
    description?: string;
    front_configs: ApiFrontConfig[];
    facility_configs: FacilityConfigUI[];
    total_patients: number;
    injury_distribution: { [key: string]: number }; // Reverted to dictionary
    version?: number; // Kept optional for UI state
    parent_config_id?: string; // Kept optional for UI state
}

// API Payload - version and parent_config_id are truly optional if not sent
interface ApiConfigTemplatePayloadForSave {
    name: string;
    description?: string;
    front_configs: ApiFrontConfig[];
    facility_configs: FacilityConfigUI[];
    total_patients: number;
    injury_distribution: { [key: string]: number };
    version?: number; // Optional: will be sent if present
    parent_config_id?: string; // Optional: will be sent if present
}


const generateId = () => `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

const DEFAULT_INJURY_DISTRIBUTION = {
    "Battle Injury": 52,
    "Disease": 33,
    "Non-Battle Injury": 15
};

const ConfigurationPanel: React.FC = () => {
    const [savedConfigs, setSavedConfigs] = useState<ConfigTemplateUI[]>([]);
    const [activeConfig, setActiveConfig] = useState<ConfigTemplateUI | null>(null);
    
    const [fronts, setFronts] = useState<FrontConfigUI[]>([]);
    const [facilities, setFacilities] = useState<FacilityConfigUI[]>([]);
    const [configName, setConfigName] = useState<string>("");
    const [configDescription, setConfigDescription] = useState<string>("");
    const [totalPatients, setTotalPatients] = useState<number>(1000);
    const [injuryDistribution, setInjuryDistribution] = useState<{ [key: string]: number }>(DEFAULT_INJURY_DISTRIBUTION); // State reverted
    const [availableNationalities, setAvailableNationalities] = useState<{ code: string; name: string }[]>([]);
    const [staticFrontsData, setStaticFrontsData] = useState<StaticFrontDefinitionUI[] | null>(null);
    const [apiError, setApiError] = useState<string | null>(null);

    useEffect(() => {
        // Fetch initial data (simplified for brevity, assuming it works as before for configs, nationalities, static fronts)
        // Important: When loading configs, ensure injury_distribution is correctly populated or defaulted.
        const fetchInitialData = async () => {
            setApiError(null);
            try {
                const responseConfigs = await fetch('/api/v1/configurations/', {
                    method: 'GET',
                    headers: { 'Accept': 'application/json', 'X-API-KEY': 'your_secret_api_key_here' }
                });
                if (!responseConfigs.ok) throw new Error(`Fetch configs failed: ${responseConfigs.status}`);
                const dataConfigs: ConfigTemplateUI[] = await responseConfigs.json(); 
                
                const typedDataConfigs = dataConfigs.map(config => ({
                    ...config,
                    front_configs: config.front_configs.map((fc: any) => ({
                        ...fc,
                        nationality_distribution: Array.isArray(fc.nationality_distribution) 
                            ? fc.nationality_distribution.map((nd: any, index: number) => ({
                                id: `loaded-nat-${fc.id}-${index}-${Date.now()}`,
                                nationality_code: nd.nationality_code,
                                percentage: nd.percentage
                              }))
                            : [] 
                    })),
                    // Ensure injury_distribution is a dictionary, defaulting if not present or wrong type
                    injury_distribution: (typeof config.injury_distribution === 'object' && config.injury_distribution !== null && !Array.isArray(config.injury_distribution))
                        ? config.injury_distribution
                        : DEFAULT_INJURY_DISTRIBUTION
                }));
                setSavedConfigs(typedDataConfigs);
            } catch (error) {
                console.error("Error fetching configurations:", error);
                setApiError(`Error fetching configurations: ${error instanceof Error ? error.message : String(error)}`);
            }
             try {
                const responseNats = await fetch('/api/v1/configurations/reference/nationalities/', {
                     method: 'GET', headers: { 'Accept': 'application/json', 'X-API-KEY': 'your_secret_api_key_here' }
                });
                if (!responseNats.ok) throw new Error(`Fetch nationalities failed: ${responseNats.status}`);
                const dataNats: { code: string; name: string }[] = await responseNats.json();
                setAvailableNationalities(dataNats);
            } catch (error) {
                console.error("Error fetching nationalities:", error);
                setApiError(`Error fetching nationalities: ${error instanceof Error ? error.message : String(error)}`);

            }

            try {
                const responseStaticFronts = await fetch('/api/v1/configurations/reference/static-fronts/', {
                    method: 'GET', headers: { 'Accept': 'application/json', 'X-API-KEY': 'your_secret_api_key_here' }
                });
                if (!responseStaticFronts.ok) {
                    if (responseStaticFronts.status === 404) {
                        console.log("Static fronts configuration file not found or empty.");
                        setStaticFrontsData(null);
                    } else {
                        throw new Error(`Fetch static fronts failed: ${responseStaticFronts.status}`);
                    }
                } else {
                    const dataStaticFronts: StaticFrontDefinitionUI[] | null = await responseStaticFronts.json();
                    setStaticFrontsData(dataStaticFronts);
                }
            } catch (error) {
                console.error("Error fetching static front definitions:", error);
                setApiError(`Error fetching static fronts: ${error instanceof Error ? error.message : String(error)}`);
                setStaticFrontsData(null);
            }
        };
        fetchInitialData();
    }, []);

    const loadConfigToEdit = (config: ConfigTemplateUI) => {
        setApiError(null);
        setActiveConfig(config);
        setConfigName(config.name);
        setConfigDescription(config.description || "");
        
        const frontsWithClientIds = config.front_configs.map(f => ({
            ...f,
            nationality_distribution: f.nationality_distribution.map((nd, index) => ({
                id: nd.id || `loaded-nat-${f.id}-${index}-${Date.now()}`,
                nationality_code: nd.nationality_code,
                percentage: nd.percentage
            }))
        }));
        setFronts([...frontsWithClientIds]);
        setFacilities([...config.facility_configs]);
        setTotalPatients(config.total_patients);
        // Ensure injury_distribution is a dictionary, defaulting if not present or wrong type
        setInjuryDistribution(
            (typeof config.injury_distribution === 'object' && config.injury_distribution !== null && !Array.isArray(config.injury_distribution))
                ? { ...DEFAULT_INJURY_DISTRIBUTION, ...config.injury_distribution } // Merge with defaults to ensure all keys
                : { ...DEFAULT_INJURY_DISTRIBUTION }
        );
    };
    
    const handleAddNewFront = () => { /* ... (remains the same) ... */ 
        const defaultNationalityCode = availableNationalities.length > 0 ? availableNationalities[0].code : "";
        setFronts([...fronts, {
            id: generateId(),
            name: "New Front",
            nationality_distribution: [{ id: generateId(), nationality_code: defaultNationalityCode, percentage: 100.0 }],
            casualty_rate: 0.1
        }]);
    };
    const handleAddNewFacility = () => { /* ... (remains the same) ... */ 
        setFacilities([...facilities, {
            id: generateId(),
            name: "New Facility",
            kia_rate: 0.1,
            rtd_rate: 0.3
        }]);
    };

    const handleInjuryPercentageChange = (type: string, value: string) => {
        const percentage = parseFloat(value);
        setInjuryDistribution(prev => ({
            ...prev,
            [type]: isNaN(percentage) ? 0 : Math.max(0, Math.min(100, percentage))
        }));
    };
    
    const handleSaveConfiguration = async () => {
        setApiError(null);
        if (!configName.trim()) {
            alert("Configuration name cannot be empty.");
            return;
        }
        // Fronts validation (remains the same)
        for (const front of fronts) {
            if (front.nationality_distribution.length === 0) {
                alert(`Front "${front.name}" must have at least one nationality in its distribution.`);
                return;
            }
            const natTotal = front.nationality_distribution.reduce((s, item) => s + (item.percentage || 0), 0);
            if (Math.abs(natTotal - 100.0) > 0.1) {
                alert(`Nationality distribution for front "${front.name}" must sum to 100%. Currently: ${natTotal.toFixed(1)}%`);
                return;
            }
            const natCodes = front.nationality_distribution.map(item => item.nationality_code);
            if (new Set(natCodes).size !== natCodes.length) {
                alert(`Front "${front.name}" has duplicate nationalities in its distribution.`);
                return;
            }
        }

        // Injury distribution validation (dictionary based)
        const injuryValues = Object.values(injuryDistribution);
        if (injuryValues.length !== 3) { // Ensure all 3 keys are present
             alert("Injury distribution must include Battle Injury, Disease, and Non-Battle Injury percentages.");
             return;
        }
        const injuryTotalPercentage = injuryValues.reduce((s, p) => s + (p || 0), 0);
        if (Math.abs(injuryTotalPercentage - 100.0) > 0.1) {
            alert(`Injury distribution percentages must sum to 100%. Currently: ${injuryTotalPercentage.toFixed(1)}%`);
            return;
        }

        const apiFrontConfigs: ApiFrontConfig[] = fronts.map(f_ui => ({ /* ... (remains the same) ... */ 
            id: f_ui.id.startsWith('temp_') ? f_ui.name.replace(/\s+/g, '_').toLowerCase() : f_ui.id,
            name: f_ui.name,
            description: f_ui.description,
            casualty_rate: f_ui.casualty_rate,
            nationality_distribution: f_ui.nationality_distribution.map(item_ui => ({
                nationality_code: item_ui.nationality_code,
                percentage: item_ui.percentage,
            })),
        }));
        const apiFacilityConfigs: FacilityConfigUI[] = facilities.map(fac_ui => ({ /* ... (remains the same) ... */ 
            id: fac_ui.id.startsWith('temp_') ? fac_ui.name.replace(/\s+/g, '_').toLowerCase() : fac_ui.id,
            name: fac_ui.name,
            description: fac_ui.description,
            capacity: fac_ui.capacity,
            kia_rate: fac_ui.kia_rate,
            rtd_rate: fac_ui.rtd_rate,
        }));

        const payloadForApi: ApiConfigTemplatePayload = {
            name: configName,
            description: configDescription || undefined,
            front_configs: apiFrontConfigs,
            facility_configs: apiFacilityConfigs,
            total_patients: totalPatients,
            injury_distribution: injuryDistribution, // Now a dictionary
            // parent_config_id and version are handled below for finalPayload
        };
        
        // Construct the actual payload for the API, conditionally including version and parent_config_id
        const finalPayload: ApiConfigTemplatePayloadForSave = {
            name: payloadForApi.name,
            description: payloadForApi.description,
            front_configs: payloadForApi.front_configs,
            facility_configs: payloadForApi.facility_configs,
            total_patients: payloadForApi.total_patients,
            injury_distribution: payloadForApi.injury_distribution,
        };

        if (activeConfig?.id && !activeConfig.id.startsWith('temp_')) {
            // If updating an existing config, include version and potentially parent_config_id
            finalPayload.version = (activeConfig.version || 0) + 1;
            if (activeConfig.parent_config_id) { // Only include if it was part of the loaded config
                finalPayload.parent_config_id = activeConfig.parent_config_id;
            }
        } else {
            // For new configs, version defaults to 1 on backend if not provided.
            // parent_config_id might be set if "Save As New Version" from an existing one,
            // but current UI doesn't explicitly support that flow for parent_config_id.
            // Let's assume for a brand new config, parent_config_id is not sent.
            // If activeConfig was a derivative (had parent_config_id) but is being saved as NEW (no activeConfig.id),
            // this logic might need refinement based on desired UX for "Save As" vs "New".
            // For now, only include parent_config_id if it's an update of a config that had one.
        }
        
        let endpoint = '/api/v1/configurations/';
        let method = 'POST';

        if (activeConfig && activeConfig.id && !activeConfig.id.startsWith('temp_')) {
            endpoint = `/api/v1/configurations/${activeConfig.id}`;
            method = 'PUT';
        }

        try {
            // const finalPayload: any = { ...payloadForApi }; // Old way
            const response = await fetch(endpoint, { 
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-API-KEY': 'your_secret_api_key_here'
                },
                body: JSON.stringify(finalPayload)
            });

            if (!response.ok) {
                const errorData = await response.json();
                let formattedError = `Failed to save configuration: ${response.status}`;
                if (errorData.detail && Array.isArray(errorData.detail)) {
                    formattedError += errorData.detail.map((err: any) => `\n- ${err.loc.join(' -> ')}: ${err.msg}`).join('');
                } else if (errorData.detail) {
                    formattedError += ` - ${errorData.detail}`;
                } else {
                    formattedError += ` - ${response.statusText}`;
                }
                setApiError(formattedError);
                throw new Error(formattedError);
            }
            setApiError(null);

            const savedOrUpdatedConfigResponse: ConfigTemplateUI = await response.json();
            
            const savedOrUpdatedConfigUI: ConfigTemplateUI = {
                ...savedOrUpdatedConfigResponse,
                front_configs: savedOrUpdatedConfigResponse.front_configs.map((fc: any) => ({
                    ...fc,
                    nationality_distribution: fc.nationality_distribution.map((nd: any, index: number) => ({
                        id: `saved-nat-${fc.id}-${index}-${Date.now()}`,
                        nationality_code: nd.nationality_code,
                        percentage: nd.percentage
                    }))
                })),
                // Ensure injury_distribution is correctly formed for UI state
                injury_distribution: (typeof savedOrUpdatedConfigResponse.injury_distribution === 'object' && savedOrUpdatedConfigResponse.injury_distribution !== null && !Array.isArray(savedOrUpdatedConfigResponse.injury_distribution))
                    ? savedOrUpdatedConfigResponse.injury_distribution
                    : { ...DEFAULT_INJURY_DISTRIBUTION }
            };

            alert(`Configuration "${savedOrUpdatedConfigUI.name}" saved successfully!`);
            
            const newSavedConfigs = [...savedConfigs];
            const existingIndex = newSavedConfigs.findIndex(c => c.id === savedOrUpdatedConfigUI.id);
            if (existingIndex !== -1) {
                newSavedConfigs[existingIndex] = savedOrUpdatedConfigUI;
            } else {
                newSavedConfigs.push(savedOrUpdatedConfigUI);
            }
            setSavedConfigs(newSavedConfigs);
            loadConfigToEdit(savedOrUpdatedConfigUI);

        } catch (error) {
            if (!apiError) {
                 setApiError(error instanceof Error ? error.message : String(error));
            }
            console.error("Error saving configuration:", error);
        }
    };

    const handleResetForm = () => {
        setApiError(null);
        setActiveConfig(null);
        setConfigName("New Scenario");
        setConfigDescription("");
        const defaultNationalityCode = availableNationalities.length > 0 ? availableNationalities[0].code : "";
        setFronts([{ id: generateId(), name: "Default Front", nationality_distribution: [{id: generateId(), nationality_code: defaultNationalityCode, percentage: 100}], casualty_rate: 0.1 }]);
        setFacilities([{id: generateId(), name: "Default Facility", kia_rate: 0.05, rtd_rate: 0.2}]);
        setTotalPatients(1000);
        setInjuryDistribution({ ...DEFAULT_INJURY_DISTRIBUTION });
    };

    const totalInjuryPercentage = Object.values(injuryDistribution).reduce((sum, val) => sum + (val || 0), 0);

    return (
        <div className="configuration-panel p-3" style={{ fontFamily: 'Arial, sans-serif' }}>
            <h2>Scenario Configuration Panel</h2>
            {apiError && (
                <div style={{ padding: '10px', margin: '10px 0', backgroundColor: '#f8d7da', color: '#721c24', border: '1px solid #f5c6cb', borderRadius: '4px', whiteSpace: 'pre-wrap' }}>
                    <strong>Error:</strong> {apiError}
                </div>
            )}
            <hr />

            {/* Load Existing / Create New Section */}
            <div style={{ marginBottom: '20px' }}> {/* ... (remains the same) ... */ }
                <h4>Load Existing Configuration</h4>
                <select 
                    onChange={(e) => {
                        const selectedId = e.target.value;
                        if (selectedId) {
                            const configToLoad = savedConfigs.find(c => c.id === selectedId);
                            if (configToLoad) loadConfigToEdit(configToLoad);
                        } else {
                            handleResetForm();
                        }
                    }}
                    value={activeConfig?.id || ""}
                    style={{ padding: '8px', marginRight: '10px', minWidth: '200px' }}
                >
                    <option value="">-- Create New / Clear --</option>
                    {savedConfigs.map(conf => (
                        <option key={conf.id} value={conf.id}>{conf.name} (v{conf.version})</option>
                    ))}
                </select>
            </div>

            {/* Configuration Details Section */}
            <div style={{ marginBottom: '20px' }}> {/* ... (remains the same) ... */ }
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
            </div>

            {/* Injury Distribution Section - Reverted to simple inputs */}
            <section style={{ marginBottom: '20px', padding: '15px', border: '1px solid #ddd', borderRadius: '5px' }}>
                <h4>Overall Injury Distribution (%)</h4>
                {Object.keys(DEFAULT_INJURY_DISTRIBUTION).map((key) => (
                    <div key={key} style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                        <label htmlFor={`injury-${key}`} style={{ width: '150px', marginRight: '10px' }}>{key}:</label>
                        <input
                            type="number"
                            id={`injury-${key}`}
                            value={injuryDistribution[key] === undefined ? '' : injuryDistribution[key]}
                            onChange={(e) => handleInjuryPercentageChange(key, e.target.value)}
                            placeholder="%"
                            min="0" max="100" step="0.1"
                            style={{ width: '80px', padding: '8px' }}
                        />
                    </div>
                ))}
                <p style={{ fontSize: '0.9em', color: Math.abs(totalInjuryPercentage - 100.0) > 0.1 ? 'red' : '#555', marginTop: '10px' }}>
                    Total: {totalInjuryPercentage.toFixed(1)}% (must be 100%)
                </p>
            </section>

            {/* Combat Fronts Section */}
            <section style={{ marginBottom: '20px' }}> {/* ... (remains the same) ... */ }
                <h4>Combat Fronts (Editable Scenario Definition)</h4>
                <p style={{fontSize: '0.9em', color: '#555'}}>
                    Define fronts below. These will be used for generation.
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

            {/* Static Fronts Display Section */}
            {staticFrontsData && staticFrontsData.length > 0 && ( /* ... (remains the same) ... */ 
                <section style={{ marginBottom: '20px', padding: '15px', border: '1px solid #007bff', borderRadius: '5px', backgroundColor: '#e7f3ff' }}>
                    <h4>Static Fronts Configuration (from <code>fronts_config.json</code> - Read-Only for Reference)</h4>
                    <p style={{color: '#004085'}}>
                        The following static front configuration (if file exists on backend) is shown for reference. 
                        The editable scenario fronts defined above will be used for saving and generation via this panel.
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
             {staticFrontsData === null && ( /* ... (remains the same) ... */ 
                 <section style={{ marginBottom: '20px', padding: '15px', border: '1px solid #ffc107', borderRadius: '5px', backgroundColor: '#fff3cd' }}>
                    <h4>Static Fronts Configuration (from <code>fronts_config.json</code>)</h4>
                    <p style={{color: '#856404'}}>
                        Static <code>fronts_config.json</code> was not found or is empty/invalid on the backend.
                    </p>
                </section>
            )}

            {/* Medical Facilities Section */}
            <section style={{ marginBottom: '20px' }}> {/* ... (remains the same) ... */ }
                <h4>Medical Facilities (Evacuation Chain - Order Matters)</h4>
                <button onClick={handleAddNewFacility} style={{ padding: '8px', marginBottom: '10px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px' }}>
                    Add Facility
                </button>
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
            
            {/* Quick Preview Section - Updated for injury_distribution */}
            <section style={{ marginTop: '20px', padding: '15px', border: '1px solid #eee', borderRadius: '5px', backgroundColor: '#fdfdfd' }}> {/* ... (summary updated) ... */ }
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
                                | Nationalities: {f.nationality_distribution.map(n => `${n.nationality_code || '(select)'} (${n.percentage.toFixed(1)}%)`).join(', ') || 'None'}
                                (Total Dist: {f.nationality_distribution.reduce((s, item) => s + (item.percentage || 0), 0).toFixed(1)}%)
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
                            <li key={type}>{type}: {(percent || 0).toFixed(1)}%</li>
                        ))}
                         <li>Total: {totalInjuryPercentage.toFixed(1)}%</li>
                    </ul>
                ) : <p>No injury distribution configured (will use defaults).</p>}
            </section>
            
            <hr />
            {/* Actions Section */}
            <div className="actions" style={{ marginTop: '20px' }}> {/* ... (remains the same) ... */ }
                <button onClick={handleSaveConfiguration} style={{ padding: '10px 15px', marginRight: '10px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px' }}>
                    Save Configuration
                </button>
                <button onClick={handleResetForm} style={{ padding: '10px 15px', marginRight: '10px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px' }}>
                    Clear Form / New
                </button>
            </div>
        </div>
    );
};

import ReactDOM from 'react-dom/client';

const renderConfigurationPanel = () => { /* ... (remains the same) ... */ 
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

if (typeof window !== 'undefined' && typeof document !== 'undefined') { /* ... (remains the same) ... */ 
    if (document.getElementById('reactConfigurationPanelRoot')) {
        renderConfigurationPanel();
    } else {
        (window as any).renderReactConfigurationPanel = renderConfigurationPanel;
        console.log("ConfigurationPanel: Root element not found. Call window.renderReactConfigurationPanel() to render.");
    }
}

export default ConfigurationPanel;
