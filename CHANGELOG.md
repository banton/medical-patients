# Changelog

All notable changes to the Military Medical Exercise Patient Generator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive refactoring to clean domain-driven architecture (see PR #2)
- Redis caching layer for improved performance
- Modular JavaScript architecture with ES6 modules
- Configuration persistence with localStorage and import/export
- Comprehensive accessibility features (WCAG compliant)
- End-to-end and integration testing infrastructure
- CI/CD pipeline with GitHub Actions
- Pre-commit hooks and code quality tools
- Docker test containers for isolated testing

### Changed
- Transformed monolithic FastAPI app to clean layered architecture
- Async patient generation pipeline for better scalability
- Enhanced UI with better UX and accessibility
- Improved error handling and retry logic

### Performance
- 3-5x faster generation with Redis caching
- Connection pooling for database operations
- Debounced validation and lazy loading
- Client-side caching for reference data

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