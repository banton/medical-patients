# Changelog

All notable changes to the Military Medical Exercise Patient Generator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-11-29

### Added
- **Enhanced Medical Simulation System (PR #19)**
  - Realistic treatment protocol system with SNOMED CT procedure mappings
  - Body part tracking for injuries (Head, Torso, Left/Right Arm, Left/Right Leg)
  - Health score engine with deterioration and improvement mechanics
  - Treatment effectiveness modeling by facility level (POI → Role 4)
  - Markov chain health state transitions for realistic patient outcomes

- **Treatment Protocol Features**
  - Facility-specific treatment capabilities (basic → advanced care)
  - Treatment success rates based on facility level and patient condition
  - SNOMED CT coded procedures for interoperability
  - Health impact tracking (health_before/health_after for each treatment)

- **Patient Flow Enhancements**
  - Triage category assignment (T1-T3) based on health scores
  - Transport type selection (ground/air ambulance) based on urgency
  - Facility capacity management with overflow routing
  - Evacuation time modeling between facilities

- **Mortality and Outcomes**
  - Realistic mortality rates (~20-35% depending on scenario intensity)
  - DOW (Died of Wounds) status tracking
  - RTD (Returned to Duty) outcome modeling
  - Death event recording with cause (deterioration, KIA, etc.)

### Changed
- Patient timeline now includes detailed treatment events with health tracking
- Facility progression includes treatment application at each level
- Output JSON schema extended with `body_part`, `treatments`, and enhanced `timeline`

### Fixed
- Timeline events now properly record deaths before continuing simulation
- Health scores properly bounded (0-100 range)
- Triage reassignment based on health changes during transport

## [1.1.0] - 2025-06-19

### Added
- **Cross-Platform Development Environment (EPIC-001)**
  - Task runner with 14 essential commands for consistent workflow
  - Automatic OS detection and environment setup
  - Support for Ubuntu 22.04/24.04 with PEP 668 compliance
  - Simplified installation process completing in 30 seconds
  
- **API Key Management System (EPIC-002)**  
  - Comprehensive CLI tool for API key lifecycle management
  - Secure key generation with SHA256 hashing
  - Rate limiting and usage tracking
  - Key rotation and statistics monitoring
  
- **Production Scalability Improvements (EPIC-003)**
  - Enhanced database connection pooling with health monitoring
  - Prometheus metrics integration with /metrics endpoint
  - Memory-optimized patient generation (54% reduction)
  - Streaming API for large-scale generation
  - Background job resource management with limits
  
- **Intelligent Memory Management System (EPIC-006)**
  - Token-aware memory system with 10,000 token budget
  - Automatic compression achieving 98.5% reduction
  - Structured knowledge organization (active/reference/archive)
  - Weekly maintenance automation
  
- **React Timeline Viewer**
  - Interactive patient flow visualization
  - 5-facility progression tracking (POI → Role1-4)
  - Real-time playback with speed control
  - Smart KIA/RTD tallying and auto-hide
  
- **Enhanced Caching Layer**
  - API key limits caching (5 minute TTL)
  - Job status caching (dynamic TTL)
  - Configuration templates caching (1 hour TTL)

### Changed
- **Architecture**: Transformed to clean domain-driven design with proper separation of concerns
- **API**: Standardized all endpoints to v1 with consistent request/response models
- **Installation**: Streamlined to 5-step quick start with clear mandatory vs optional features
- **Documentation**: Updated README with professional structure and platform support guide
- **Task Commands**: Reduced from 150+ to 14 essential commands with clear help system
- **Platform Support**: Officially supporting Linux (Ubuntu 22.04+) and macOS only
- **Testing**: Enhanced test coverage with 113 total tests (77 unit + 21 integration + 9 E2E + 6 timeline)

### Fixed
- Database connection stability with proper pooling and recycling
- Memory leaks during large patient generation
- API response consistency across all endpoints
- Ubuntu 24.04 PEP 668 compliance issues
- CI/CD pipeline reliability

### Performance
- 3-5x faster generation with Redis caching
- 50-70% memory reduction for large patient counts
- Connection pooling reducing database load
- Streaming API enabling 10,000+ patient generation
- Batch processing with garbage collection

### Security
- Enhanced API key security with proper hashing
- Removed all hardcoded secrets from codebase
- Added comprehensive input validation
- Secure error handling without information leakage

## [Unreleased]

### Planned
- Advanced visualization dashboard
- Plugin architecture for extensible configurations
- Enhanced monitoring and observability
- Multi-tenant deployment options

## [1.0.0] - TBD

### Added
- Initial release of Military Medical Exercise Patient Generator
- Basic patient generation with FHIR output
- Web-based configuration interface
- Docker containerization
- PostgreSQL database for configuration storage
- Basic REST API for patient generation

### Features
- Generate realistic military medical scenarios
- Multiple nationality support
- Injury distribution modeling
- Medical facility progression simulation
- Export to JSON, XML formats
- Encryption and compression options

### Security
- API key authentication
- Data encryption capabilities
- Secure file handling

---

## Version Numbering

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR** version when you make incompatible API changes
- **MINOR** version when you add functionality in a backward compatible manner  
- **PATCH** version when you make backward compatible bug fixes

## Release Process

1. Create release branch from `develop`
2. Update VERSION file and CHANGELOG.md
3. Test thoroughly
4. Merge to `main` via pull request
5. Create GitHub release with tag
6. Deploy to production
7. Merge back to `develop`