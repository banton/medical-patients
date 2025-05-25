/**
 * UI Integration Tests
 * These tests ensure that the UI components correctly interact with the API
 */

import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';
import { APIClient } from '../js/modules/apiClient.js';
import { ConfigurationManager } from '../js/modules/configurationManager.js';
import { ValidationManager } from '../js/modules/validationManager.js';
import { JobManager } from '../js/modules/jobManager.js';

// Mock fetch for tests
global.fetch = jest.fn();

describe('APIClient', () => {
    let apiClient;

    beforeEach(() => {
        apiClient = new APIClient();
        fetch.mockClear();
    });

    describe('Reference Endpoints', () => {
        it('should fetch nationalities without authentication', async () => {
            const mockNationalities = [
                { code: 'USA', name: 'United States' },
                { code: 'GBR', name: 'United Kingdom' }
            ];

            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockNationalities
            });

            const nationalities = await apiClient.getNationalities();
            
            expect(fetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/v1/configurations/reference/nationalities/')
            );
            expect(nationalities).toEqual(['United States', 'United Kingdom']);
        });

        it('should handle nationality fetch errors', async () => {
            fetch.mockResolvedValueOnce({
                ok: false,
                status: 500
            });

            await expect(apiClient.getNationalities()).rejects.toThrow('HTTP 500');
        });
    });

    describe('Generation Endpoint', () => {
        it('should send correct format to generation endpoint', async () => {
            const mockResponse = { job_id: 'test-123', message: 'Job started' };
            
            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockResponse
            });

            const config = {
                configuration: {
                    name: 'Test Config',
                    total_patients: 100
                },
                output_formats: ['json'],
                use_compression: false,
                use_encryption: false
            };

            const result = await apiClient.startGeneration(config);

            expect(fetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/generate'),
                expect.objectContaining({
                    method: 'POST',
                    headers: expect.objectContaining({
                        'X-API-Key': 'your_secret_api_key_here',
                        'Content-Type': 'application/json'
                    }),
                    body: JSON.stringify(config)
                })
            );
            expect(result).toEqual(mockResponse);
        });
    });

    describe('Job Management', () => {
        it('should fetch job list with authentication', async () => {
            const mockJobs = [
                { job_id: '123', status: 'running', progress: 0.5 }
            ];

            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockJobs
            });

            const jobs = await apiClient.getJobs();

            expect(fetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/jobs/'),
                expect.objectContaining({
                    headers: expect.objectContaining({
                        'X-API-Key': 'your_secret_api_key_here'
                    })
                })
            );
            expect(jobs).toEqual(mockJobs);
        });
    });
});

describe('ConfigurationManager', () => {
    let configManager;

    beforeEach(() => {
        configManager = new ConfigurationManager();
    });

    describe('prepareForAPI', () => {
        it('should transform UI config to API format', () => {
            const uiConfig = {
                total_patients: 200,
                exercise_name: 'Test Exercise',
                exercise_base_date: '2025-05-25',
                description: 'Test description',
                
                fronts: [
                    {
                        id: 'front-1',
                        name: 'Eastern Front',
                        type: 'Combat',
                        casualty_rate: 0.6,
                        nationality_distribution: {
                            'United States': 60,
                            'United Kingdom': 40
                        }
                    }
                ],
                
                medical_facility_defaults: {
                    point_of_injury: {
                        name: 'Point of Injury',
                        capacity: 0,
                        kia_rate: 0.025,
                        rtd_rate: 0.10
                    },
                    role_1: {
                        name: 'Role 1',
                        capacity: 10,
                        kia_rate: 0.01,
                        rtd_rate: 0.15
                    },
                    role_2: {
                        name: 'Role 2',
                        capacity: 50,
                        kia_rate: 0.005,
                        rtd_rate: 0.30
                    },
                    role_3: {
                        name: 'Role 3',
                        capacity: 200,
                        kia_rate: 0.002,
                        rtd_rate: 0.25
                    },
                    role_4: {
                        name: 'Role 4',
                        capacity: 500,
                        kia_rate: 0.001,
                        rtd_rate: 0.40
                    }
                },
                
                injury_distribution: {
                    'Disease': 50,
                    'Non-Battle Injury': 40,
                    'Battle Trauma': 10
                },
                
                output_formats: ['json', 'xml'],
                use_compression: true,
                use_encryption: false
            };

            const apiRequest = configManager.prepareForAPI(uiConfig);

            // Check structure
            expect(apiRequest).toHaveProperty('configuration');
            expect(apiRequest).toHaveProperty('output_formats');
            expect(apiRequest).toHaveProperty('use_compression');
            expect(apiRequest).toHaveProperty('use_encryption');

            // Check configuration transformation
            const config = apiRequest.configuration;
            expect(config.name).toBe('Test Exercise');
            expect(config.total_patients).toBe(200);
            
            // Check front transformation
            expect(config.front_configs).toHaveLength(1);
            expect(config.front_configs[0].casualty_rate).toBe(0.6);
            expect(config.front_configs[0].nationality_distribution).toHaveLength(2);
            expect(config.front_configs[0].nationality_distribution[0]).toEqual({
                nationality_code: 'USA',
                percentage: 60
            });

            // Check facility transformation
            expect(config.facility_configs).toHaveLength(5);
            expect(config.facility_configs[0].id).toBe('POINT_OF_INJURY');
            expect(config.facility_configs[0].kia_rate).toBe(0.025);

            // Check injury distribution
            expect(config.injury_distribution).toEqual({
                'Disease': 50,
                'Battle Injury': 10,
                'Non-Battle Injury': 40
            });
        });

        it('should handle nationality code mapping', () => {
            const countryName = 'United States';
            const code = configManager.getCountryCode(countryName);
            expect(code).toBe('USA');
        });

        it('should handle unknown nationality codes', () => {
            const unknownCountry = 'Unknown Country';
            const code = configManager.getCountryCode(unknownCountry);
            expect(code).toBe('UNK'); // First 3 letters uppercase
        });
    });

    describe('validateConfiguration', () => {
        it('should validate correct configuration', () => {
            const config = configManager.getDefaultConfiguration();
            const validation = configManager.validateConfiguration(config);
            
            expect(validation.isValid).toBe(true);
            expect(validation.errors).toHaveLength(0);
        });

        it('should catch missing fronts', () => {
            const config = configManager.getDefaultConfiguration();
            config.fronts = [];
            
            const validation = configManager.validateConfiguration(config);
            
            expect(validation.isValid).toBe(false);
            expect(validation.errors).toContainEqual(
                expect.objectContaining({
                    field: 'fronts',
                    message: expect.stringContaining('at least one front')
                })
            );
        });
    });
});

describe('ValidationManager', () => {
    let validator;

    beforeEach(() => {
        validator = new ValidationManager();
    });

    describe('Field Validation', () => {
        it('should validate total patients range', () => {
            const config1 = { total_patients: 0 };
            const config2 = { total_patients: 5000 };
            const config3 = { total_patients: 10001 };

            const validation1 = validator.validateConfiguration(config1);
            const validation2 = validator.validateConfiguration(config2);
            const validation3 = validator.validateConfiguration(config3);

            expect(validation1.isValid).toBe(false);
            expect(validation2.errors.filter(e => e.field === 'total_patients')).toHaveLength(0);
            expect(validation3.isValid).toBe(false);
        });

        it('should validate nationality distribution sums to 100%', () => {
            const config = {
                total_patients: 100,
                exercise_base_date: '2025-05-25',
                fronts: [{
                    name: 'Test Front',
                    casualty_rate: 1.0,
                    nationality_distribution: {
                        'USA': 60,
                        'GBR': 30
                        // Missing 10%
                    }
                }],
                injury_distribution: {
                    'Disease': 50,
                    'Non-Battle Injury': 40,
                    'Battle Trauma': 10
                },
                output_formats: ['json']
            };

            const validation = validator.validateConfiguration(config);
            
            expect(validation.isValid).toBe(false);
            expect(validation.errors).toContainEqual(
                expect.objectContaining({
                    field: expect.stringContaining('nationality_distribution'),
                    message: expect.stringContaining('100%')
                })
            );
        });

        it('should validate injury distribution sums to 100%', () => {
            const config = {
                total_patients: 100,
                exercise_base_date: '2025-05-25',
                fronts: [{
                    name: 'Test Front',
                    casualty_rate: 1.0,
                    nationality_distribution: { 'USA': 100 }
                }],
                injury_distribution: {
                    'Disease': 50,
                    'Non-Battle Injury': 30,
                    'Battle Trauma': 10
                    // Sums to 90%
                },
                output_formats: ['json']
            };

            const validation = validator.validateConfiguration(config);
            
            expect(validation.isValid).toBe(false);
            expect(validation.errors).toContainEqual(
                expect.objectContaining({
                    field: 'injury_distribution',
                    message: expect.stringContaining('100%')
                })
            );
        });
    });
});

describe('JobManager', () => {
    let jobManager;
    let mockApiClient;

    beforeEach(() => {
        mockApiClient = {
            getJobs: jest.fn(),
            getJobStatus: jest.fn()
        };
        jobManager = new JobManager(mockApiClient);
    });

    afterEach(() => {
        jobManager.stopPolling();
    });

    describe('Job Polling', () => {
        it('should track active jobs', async () => {
            const mockJobs = [
                { job_id: '123', status: 'running', progress: 0.5 },
                { job_id: '456', status: 'completed', progress: 1.0 }
            ];

            mockApiClient.getJobs.mockResolvedValue(mockJobs);

            const jobs = await jobManager.loadActiveJobs();

            expect(mockApiClient.getJobs).toHaveBeenCalled();
            expect(jobs).toEqual(mockJobs);
            expect(jobManager.activeJobs.size).toBe(1); // Only running job
            expect(jobManager.activeJobs.has('123')).toBe(true);
        });

        it('should detect status changes', () => {
            const previous = { status: 'pending', progress: 0 };
            const current = { status: 'running', progress: 0.1 };

            const hasChanged = jobManager.hasStatusChanged(previous, current);
            
            expect(hasChanged).toBe(true);
        });

        it('should dispatch events on job completion', async () => {
            const jobId = 'test-123';
            const completedJob = {
                job_id: jobId,
                status: 'completed',
                progress: 1.0
            };

            // Mock document.dispatchEvent
            const dispatchSpy = jest.spyOn(document, 'dispatchEvent');
            
            // Add job to active tracking
            jobManager.activeJobs.set(jobId, { status: 'running' });
            
            // Mock API response
            mockApiClient.getJobStatus.mockResolvedValue(completedJob);

            // Trigger polling
            await jobManager.pollActiveJobs();

            // Check events were dispatched
            expect(dispatchSpy).toHaveBeenCalledWith(
                expect.objectContaining({
                    type: 'job-status-update'
                })
            );
            expect(dispatchSpy).toHaveBeenCalledWith(
                expect.objectContaining({
                    type: 'job-completed'
                })
            );

            // Job should be removed from active tracking
            expect(jobManager.activeJobs.has(jobId)).toBe(false);

            dispatchSpy.mockRestore();
        });
    });
});

// Integration test for the full flow
describe('Full UI Flow Integration', () => {
    it('should handle complete generation flow', async () => {
        const apiClient = new APIClient();
        const configManager = new ConfigurationManager();
        
        // Mock API responses
        fetch.mockImplementation((url) => {
            if (url.includes('/api/v1/configurations/reference/nationalities/')) {
                return Promise.resolve({
                    ok: true,
                    json: async () => [
                        { code: 'USA', name: 'United States' },
                        { code: 'GBR', name: 'United Kingdom' }
                    ]
                });
            }
            if (url.includes('/api/generate')) {
                return Promise.resolve({
                    ok: true,
                    json: async () => ({ job_id: 'test-123', message: 'Started' })
                });
            }
            if (url.includes('/api/jobs/')) {
                return Promise.resolve({
                    ok: true,
                    json: async () => []
                });
            }
            return Promise.reject(new Error('Unknown endpoint'));
        });

        // 1. Get nationalities
        const nationalities = await apiClient.getNationalities();
        expect(nationalities).toContain('United States');

        // 2. Create configuration
        const uiConfig = configManager.getDefaultConfiguration();
        
        // 3. Validate configuration
        const validation = configManager.validateConfiguration(uiConfig);
        expect(validation.isValid).toBe(true);

        // 4. Prepare for API
        const apiRequest = configManager.prepareForAPI(uiConfig);
        expect(apiRequest).toHaveProperty('configuration');
        expect(apiRequest).toHaveProperty('output_formats');

        // 5. Start generation
        const result = await apiClient.startGeneration(apiRequest);
        expect(result.job_id).toBe('test-123');

        fetch.mockClear();
    });
});