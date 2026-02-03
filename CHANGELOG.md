# Changelog

All notable changes to the Diriyah AI Demo project are documented in this file.

## [2.0.0] - 2024-03-20

### 🎯 Major Release: Investor Demo Platform

This release transforms Diriyah AI into a comprehensive construction management platform with AI-powered document intelligence, BIM integration, and project forecasting capabilities.

### Added

#### Phase 1: Document Intelligence
- **Document Classifier** - AI-powered classification of 15+ construction document types
- **Action Item Extractor** - Extract tasks, assignees, due dates from meeting minutes
- **Enhanced Chat** - AI chat with document citations and RAG retrieval

#### Phase 2: BIM Integration
- **IFC Parser** - Parse IFC files with IfcOpenShell or fallback regex parser
- **Element Browser** - Filter elements by type, level, material
- **QTO Calculator** - Quantity take-off with SAR cost estimation

#### Phase 3: Project Intelligence
- **Forecast Engine** - Schedule/cost predictions with Monte Carlo simulation
- **EVM Metrics** - SPI, CPI, EAC, TCPI calculations
- **Anomaly Detection** - Real-time alerts for schedule, cost, safety, quality
- **Progress Tracking** - Track progress with trend analysis

#### Frontend Components
- **DocumentUpload.jsx** - Drag-and-drop with classification preview
- **BIMViewer.jsx** - Interactive IFC model browser
- **ProjectIntelligenceDashboard.jsx** - Analytics with gauges and charts
- **EnhancedChat.jsx** - Chat with citations
- **ActionItemsManager.jsx** - Task management with filters

#### New API Endpoints
- `/api/classify`, `/api/classify/upload` - Document classification
- `/api/extract` - Action item extraction
- `/api/ifc/parse`, `/api/ifc/{model_id}/elements` - IFC parsing
- `/api/qto/calculate`, `/api/qto/compare` - Quantity take-off
- `/api/forecast/project`, `/api/forecast/evm` - Forecasting
- `/api/anomalies/detect`, `/api/anomalies/dashboard` - Anomaly detection
- `/api/progress/update`, `/api/progress/dashboard` - Progress tracking

### Tests
- 43 comprehensive tests covering all new features
- All tests passing

---

## [1.21.0] - 2025-09-25

### Added
- Prometheus metrics endpoint and JSON logging.
- Secret management with K8s Secrets and SealedSecrets.
- CI/CD matrix testing, linting, and Trivy scans.
- Pre-commit hooks and contributing guide.
- Resource requests/limits, probes, HPAs, and PDBs.
- PVCs for Redis, Chroma, and optional PostgreSQL.

### Changed
- Migrated to semantic versioning (v1.21.0).

### Fixed
- Deployment consistency across Helm, Kustomize, and raw K8s manifests.
