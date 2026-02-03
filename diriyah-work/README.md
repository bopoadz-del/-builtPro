# Diriyah Brain AI v2.0

> **AI-Powered Construction Project Management Platform**  
> Built for the USD $63 billion Diriyah giga-project in Saudi Arabia

[![Tests](https://img.shields.io/badge/tests-43%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.12-blue)]()
[![React](https://img.shields.io/badge/react-18-61dafb)]()
[![License](https://img.shields.io/badge/license-proprietary-red)]()

## 🎯 Overview

Diriyah AI is an enterprise-grade construction management platform that combines:
- **Document Intelligence** - AI-powered classification and action item extraction
- **BIM Integration** - IFC model parsing and quantity take-off
- **Project Forecasting** - Schedule and cost predictions using Earned Value Management
- **Real-time Monitoring** - Anomaly detection and progress tracking

## ✨ New Features (v2.0)

### Phase 1: Document Intelligence
| Feature | Description |
|---------|-------------|
| **Document Classifier** | Automatically classifies 15+ construction document types (Contracts, RFIs, Submittals, etc.) |
| **Action Item Extractor** | Extracts tasks, assignees, due dates, and priorities from meeting minutes |
| **Enhanced Chat** | AI chat with document citations and RAG-based retrieval |

### Phase 2: BIM Integration
| Feature | Description |
|---------|-------------|
| **IFC Parser** | Parse Industry Foundation Classes files using IfcOpenShell |
| **Element Browser** | Filter and search building elements by type, level, material |
| **QTO Calculator** | Quantity take-off with SAR cost estimation |

### Phase 3: Project Intelligence
| Feature | Description |
|---------|-------------|
| **Forecast Engine** | Schedule and cost predictions with Monte Carlo simulation |
| **EVM Metrics** | SPI, CPI, EAC, TCPI calculations |
| **Anomaly Detection** | Real-time alerts for schedule, cost, safety, quality issues |
| **Progress Tracking** | Track progress against baseline with trend analysis |

### Frontend Components
| Component | Description |
|-----------|-------------|
| **DocumentUpload** | Drag-and-drop with live classification preview |
| **BIMViewer** | Interactive IFC model browser |
| **IntelligenceDashboard** | SPI/CPI gauges, forecasts, alerts |
| **EnhancedChat** | Chat with citations and suggested questions |
| **ActionItemsManager** | Task list with filtering and status tracking |

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.12+ (for local backend development)

### Run with Docker

```bash
# Clone the repository
git clone https://github.com/bopoadz-del/diriyah-ai-demo.git
cd diriyah-ai-demo

# Copy environment file
cp .env.example .env

# Start all services
docker compose up --build
```

Access the application:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Local Development

```bash
# Backend
./scripts/setup-dev-env.sh
source .venv/bin/activate
cd backend && uvicorn main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Run tests
pytest backend/tests/test_demo_features.py -v
```

## 📡 API Reference

### Document Classification
```bash
# Classify text content
curl -X POST http://localhost:8000/api/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "This Agreement is entered into..."}'

# Classify uploaded file
curl -X POST http://localhost:8000/api/classify/upload \
  -F "file=@contract.pdf"
```

### Action Item Extraction
```bash
# Extract from text
curl -X POST http://localhost:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "Action: John to submit report by Friday"}'
```

### BIM/IFC Parsing
```bash
# Parse IFC file
curl -X POST http://localhost:8000/api/ifc/parse \
  -F "file=@building.ifc"

# Get model elements
curl http://localhost:8000/api/ifc/{model_id}/elements?page_size=50

# Calculate QTO
curl -X POST http://localhost:8000/api/qto/calculate \
  -F "file=@building.ifc"
```

### Project Forecasting
```bash
# Full project forecast
curl -X POST http://localhost:8000/api/forecast/project \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "Heritage Quarter",
    "planned_end_date": "2025-12-31",
    "current_progress": 47,
    "planned_progress": 52,
    "budget": 63000000,
    "actual_cost": 28500000
  }'

# EVM metrics
curl -X POST http://localhost:8000/api/forecast/evm \
  -H "Content-Type: application/json" \
  -d '{
    "budget_at_completion": 1000000,
    "actual_cost": 500000,
    "percent_complete": 45,
    "planned_percent": 50
  }'
```

### Anomaly Detection
```bash
# Detect anomalies
curl -X POST http://localhost:8000/api/anomalies/detect \
  -H "Content-Type: application/json" \
  -d '{
    "data_stream": [
      {"risk_score": 0.85, "section": "Foundation"},
      {"progress_percent": 30, "expected_progress_percent": 50}
    ]
  }'
```

## 🏗️ Architecture

```
diriyah-ai-demo/
├── backend/
│   ├── api/                    # FastAPI route handlers
│   │   ├── document_classifier.py
│   │   ├── action_item_extractor.py
│   │   ├── ifc_parser.py
│   │   ├── qto.py
│   │   ├── forecast_engine.py
│   │   ├── anomaly_detector.py
│   │   ├── progress_tracking.py
│   │   └── chat.py
│   ├── services/               # Business logic
│   │   ├── document_classifier.py
│   │   ├── action_item_extractor.py
│   │   ├── ifc_parser.py
│   │   ├── forecast_engine.py
│   │   └── anomaly_detector.py
│   └── tests/
│       └── test_demo_features.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DocumentUpload.jsx
│   │   │   ├── BIMViewer.jsx
│   │   │   ├── ProjectIntelligenceDashboard.jsx
│   │   │   ├── EnhancedChat.jsx
│   │   │   └── ActionItemsManager.jsx
│   │   └── pages/
│   │       ├── BIMViewerPage.jsx
│   │       ├── IntelligencePage.jsx
│   │       ├── DocumentsPage.jsx
│   │       └── ActionsPage.jsx
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for AI features | (optional) |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `JWT_SECRET_KEY` | Secret for JWT tokens | (required in production) |
| `USE_FIXTURE_PROJECTS` | Use demo data | `true` |

### Optional Dependencies

```bash
# For full BIM support
pip install ifcopenshell

# For ML features
INSTALL_BACKEND_OPTIONALS=true ./scripts/setup-dev-env.sh
```

## 📊 Demo Data

The platform includes demo data for the Diriyah Heritage Quarter project:
- 5 sample action items with various priorities
- Simulated progress data (47% complete)
- Budget tracking (SAR 63M project)
- Sample anomalies and alerts

## 🧪 Testing

```bash
# Run all new feature tests
pytest backend/tests/test_demo_features.py -v

# Test specific phase
pytest backend/tests/test_demo_features.py::TestDocumentClassifier -v
pytest backend/tests/test_demo_features.py::TestIFCParser -v
pytest backend/tests/test_demo_features.py::TestForecastEngine -v
```

## 📝 API Documentation

Full OpenAPI documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🚢 Deployment

### Render.com

The project includes `render.yaml` for one-click deployment:

1. Connect your GitHub repository to Render
2. Set required environment variables
3. Deploy

### Docker Production

```bash
docker compose -f docker-compose.prod.yml up -d
```

## 📄 License

Proprietary - Diriyah Company © 2024

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For questions or support, contact the Diriyah AI Platform team.
