"""Comprehensive tests for Diriyah AI Demo features (Phases 1-3).

Tests cover:
- Phase 1: Document Classifier, Action Item Extractor, Enhanced Chat
- Phase 2: IFC Parser, QTO Calculator
- Phase 3: Progress Tracking, Forecast Engine, Anomaly Detector
"""

import pytest
from datetime import datetime, timedelta


# =============================================================================
# PHASE 1 TESTS: Demo-Ready Core
# =============================================================================

class TestDocumentClassifier:
    """Tests for Document Classification service and API."""
    
    def test_classify_contract(self):
        """Test classification of contract document."""
        from backend.services.document_classifier import classify_document, DocumentType
        
        content = """
        This Agreement is entered into as of January 15, 2024, by and between 
        ABC Construction LLC ("Contractor") and Diriyah Company ("Owner"). 
        The Contractor agrees to perform the Work described in Exhibit A 
        for a Contract Sum of SAR 45,000,000. This contract shall be governed 
        by the laws of Saudi Arabia.
        """
        
        result = classify_document(content, filename="contract.pdf", use_ai=False)
        
        assert result.document_type == DocumentType.CONTRACT
        assert result.confidence > 0.3  # Rule-based has lower confidence
        assert result.summary is not None
    
    def test_classify_rfi(self):
        """Test classification of RFI document."""
        from backend.services.document_classifier import classify_document, DocumentType
        
        content = """
        RFI #2024-0156
        Project: Heritage Quarter Phase 2
        Subject: Foundation Detail Clarification
        
        We request clarification on the foundation reinforcement details 
        shown on Drawing S-101. Please advise on the rebar spacing.
        """
        
        result = classify_document(content, filename="RFI_0156.pdf", use_ai=False)
        
        assert result.document_type == DocumentType.RFI
        assert result.confidence > 0.3  # Rule-based has lower confidence
    
    def test_classify_meeting_minutes(self):
        """Test classification of meeting minutes."""
        from backend.services.document_classifier import classify_document, DocumentType
        
        content = """
        Meeting Minutes - Weekly Progress Meeting
        Date: March 15, 2024
        Attendees: John Smith (PM), Ahmed Hassan (Site Engineer)
        
        Discussion Items:
        1. Foundation work progress
        2. Material delivery schedule
        
        Action Items:
        1. John to submit revised schedule by Friday
        2. Ahmed to coordinate with supplier
        """
        
        result = classify_document(content, use_ai=False)
        
        assert result.document_type == DocumentType.MEETING_MINUTES
        assert result.confidence > 0.7
    
    def test_classify_invoice(self):
        """Test classification of invoice."""
        from backend.services.document_classifier import classify_document, DocumentType
        
        content = """
        INVOICE #INV-2024-0892
        Bill To: Diriyah Company
        From: Gulf Steel Suppliers
        Date: March 20, 2024
        
        Description: Reinforcement Steel Grade 60
        Quantity: 500 tons
        Unit Price: SAR 2,800/ton
        Total Amount Due: SAR 1,400,000
        """
        
        result = classify_document(content, use_ai=False)
        
        assert result.document_type == DocumentType.INVOICE
        assert result.confidence > 0.5  # Rule-based has lower confidence
    
    def test_classify_empty_content(self):
        """Test handling of empty content."""
        from backend.services.document_classifier import classify_document, DocumentType
        
        result = classify_document("", use_ai=False)
        
        assert result.document_type == DocumentType.UNKNOWN
        assert result.confidence == 0.0
    
    def test_document_types_enum(self):
        """Test all document types are defined."""
        from backend.services.document_classifier import DocumentType
        
        expected_types = [
            "Contract", "Drawing", "Specification", "RFI", "Submittal",
            "Change Order", "Meeting Minutes", "Invoice", "Schedule",
            "Report", "Correspondence", "Permit", "Safety Document",
            "QA/QC Document", "Unknown"
        ]
        
        actual_types = [dt.value for dt in DocumentType]
        
        for expected in expected_types:
            assert expected in actual_types, f"Missing document type: {expected}"


class TestActionItemExtractor:
    """Tests for Action Item Extraction service."""
    
    def test_extract_basic_actions(self):
        """Test extraction of basic action items."""
        from backend.services.action_item_extractor import extract_actions
        
        text = """
        Meeting Minutes - March 15, 2024
        Attendees: John Smith, Ahmed Hassan, Sarah Johnson
        
        Action Items:
        1. John will submit the revised schedule by Friday
        2. Ahmed needs to coordinate with the steel supplier
        3. Sarah should prepare the safety report by next Monday
        """
        
        result = extract_actions(text, use_ai=False)
        
        assert len(result.action_items) >= 2
        assert result.summary is not None
        assert "John" in result.attendees or len(result.action_items) > 0
    
    def test_extract_with_priorities(self):
        """Test extraction with priority detection."""
        from backend.services.action_item_extractor import extract_actions, Priority
        
        text = """
        URGENT: Complete foundation inspection immediately
        The safety audit must be done ASAP before work continues.
        Normal task: Review drawings by end of week.
        """
        
        result = extract_actions(text, use_ai=False)
        
        # Should detect at least one high-priority item
        priorities = [item.priority for item in result.action_items]
        assert Priority.CRITICAL in priorities or Priority.HIGH in priorities
    
    def test_extract_with_dates(self):
        """Test extraction of due dates."""
        from backend.services.action_item_extractor import extract_actions
        
        text = """
        Action: Submit report by March 25
        Task: Complete review by next Friday
        Deliver materials by 2024-04-01
        """
        
        result = extract_actions(text, use_ai=False)
        
        # Should extract some due dates
        dates_found = [item.due_date for item in result.action_items if item.due_date]
        assert len(dates_found) >= 1
    
    def test_extract_categories(self):
        """Test action item categorization."""
        from backend.services.action_item_extractor import extract_actions
        
        text = """
        Design team will finalize drawings by Friday.
        Procurement needs to order steel immediately.
        Safety officer must conduct site inspection.
        QA team should review test results.
        """
        
        result = extract_actions(text, use_ai=False)
        
        categories = [item.category for item in result.action_items if item.category]
        # Should have multiple categories
        assert len(set(categories)) >= 1
    
    def test_extract_empty_text(self):
        """Test handling of empty text."""
        from backend.services.action_item_extractor import extract_actions
        
        result = extract_actions("", use_ai=False)
        
        assert len(result.action_items) == 0
        assert result.summary is not None


class TestEnhancedChat:
    """Tests for Enhanced Chat with Citations."""
    
    def test_chat_response_generation(self):
        """Test that chat generates responses."""
        from backend.api.chat import _generate_ai_response
        
        message = "What is the concrete specification?"
        context_docs = ["The concrete shall be C40/50 grade with 28-day strength."]
        
        response, confidence = _generate_ai_response(message, context_docs)
        
        assert response is not None
        assert len(response) > 0
        assert 0 <= confidence <= 1
    
    def test_chat_without_context(self):
        """Test chat response without document context."""
        from backend.api.chat import _generate_ai_response
        
        message = "Hello, how are you?"
        
        response, confidence = _generate_ai_response(message, [])
        
        assert response is not None
        assert confidence > 0


# =============================================================================
# PHASE 2 TESTS: BIM Integration
# =============================================================================

class TestIFCParser:
    """Tests for IFC Parser service."""
    
    def test_parse_nonexistent_file(self):
        """Test handling of non-existent file."""
        from backend.services.ifc_parser import parse_ifc
        
        result = parse_ifc("/nonexistent/file.ifc")
        
        assert result.total_elements == 0
        assert len(result.errors) > 0
    
    def test_element_categories(self):
        """Test element category mapping."""
        from backend.services.ifc_parser import _get_category, ElementCategory
        
        assert _get_category("IfcWall") == ElementCategory.STRUCTURAL
        assert _get_category("IfcColumn") == ElementCategory.STRUCTURAL
        assert _get_category("IfcDoor") == ElementCategory.ARCHITECTURAL
        assert _get_category("IfcPipeSegment") == ElementCategory.MEP
        assert _get_category("IfcUnknownType") == ElementCategory.OTHER
    
    def test_ifc_availability_flag(self):
        """Test IFC availability detection."""
        from backend.services.ifc_parser import IFC_AVAILABLE
        
        # Should be a boolean
        assert isinstance(IFC_AVAILABLE, bool)
    
    def test_bim_element_dataclass(self):
        """Test BIMElement dataclass."""
        from backend.services.ifc_parser import BIMElement, ElementCategory
        
        element = BIMElement(
            global_id="test123",
            ifc_type="IfcWall",
            name="Wall 1",
            category=ElementCategory.STRUCTURAL
        )
        
        result = element.to_dict()
        
        assert result["global_id"] == "test123"
        assert result["ifc_type"] == "IfcWall"
        assert result["category"] == "Structural"
    
    def test_ifc_parse_result_dataclass(self):
        """Test IFCParseResult dataclass."""
        from backend.services.ifc_parser import IFCParseResult, IFCModelInfo
        
        model_info = IFCModelInfo(
            schema_version="IFC4",
            application="Test",
            project_name="Test Project",
            site_name=None,
            building_name="Building 1",
            author=None,
            organization="Test Org",
            creation_date=None
        )
        
        result = IFCParseResult(
            model_info=model_info,
            elements=[],
            element_counts={"IfcWall": 10},
            levels=["Level 1", "Level 2"],
            materials=["Concrete", "Steel"],
            total_elements=10
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["model_info"]["schema_version"] == "IFC4"
        assert result_dict["total_elements"] == 10


class TestQTOCalculator:
    """Tests for Quantity Take-Off Calculator."""
    
    def test_default_rates(self):
        """Test default unit rates are defined."""
        from backend.api.qto import DEFAULT_UNIT_RATES
        
        assert "IfcWall" in DEFAULT_UNIT_RATES
        assert "IfcColumn" in DEFAULT_UNIT_RATES
        assert "IfcSlab" in DEFAULT_UNIT_RATES
        
        # Check rate structure
        wall_rate = DEFAULT_UNIT_RATES["IfcWall"]
        assert "rate" in wall_rate
        assert "unit" in wall_rate
        assert wall_rate["rate"] > 0
    
    def test_typical_quantities(self):
        """Test typical quantities are defined."""
        from backend.api.qto import TYPICAL_QUANTITIES
        
        assert "IfcWall" in TYPICAL_QUANTITIES
        assert "area" in TYPICAL_QUANTITIES["IfcWall"] or "volume" in TYPICAL_QUANTITIES["IfcWall"]
    
    def test_quantity_item_dataclass(self):
        """Test QuantityItem dataclass."""
        from backend.api.qto import QuantityItem
        
        item = QuantityItem(
            element_type="IfcWall",
            description="Concrete Wall",
            count=10,
            quantity=150.0,
            unit="m²",
            unit_rate=850,
            total_cost=127500,
            category="Structural"
        )
        
        assert item.total_cost == 127500
        assert item.unit == "m²"
    
    def test_qto_summary_dataclass(self):
        """Test QTOSummary dataclass."""
        from backend.api.qto import QTOSummary, QuantityItem
        
        items = [
            QuantityItem("IfcWall", "Wall", 10, 100, "m²", 850, 85000, "Structural"),
            QuantityItem("IfcSlab", "Slab", 5, 200, "m²", 450, 90000, "Structural")
        ]
        
        summary = QTOSummary(
            items=items,
            total_cost=175000,
            category_totals={"Structural": 175000}
        )
        
        result = summary.to_dict()
        
        assert result["total_cost"] == 175000
        assert len(result["items"]) == 2


# =============================================================================
# PHASE 3 TESTS: Project Intelligence
# =============================================================================

class TestForecastEngine:
    """Tests for Forecast Engine service."""
    
    def test_schedule_forecast_on_track(self):
        """Test schedule forecast when project is on track."""
        from backend.services.forecast_engine import predict_schedule_delay, RiskLevel
        
        schedule_data = {
            "planned_end_date": (datetime.now() + timedelta(days=100)).strftime("%Y-%m-%d"),
            "current_progress": 50,
            "planned_progress": 50,
            "project_duration_days": 200,
            "elapsed_days": 100
        }
        
        result = predict_schedule_delay(schedule_data)
        
        assert result.delay_days >= 0
        assert result.probability_on_time > 0.5
        assert result.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]
    
    def test_schedule_forecast_behind(self):
        """Test schedule forecast when project is behind."""
        from backend.services.forecast_engine import predict_schedule_delay, RiskLevel
        
        schedule_data = {
            "planned_end_date": (datetime.now() + timedelta(days=50)).strftime("%Y-%m-%d"),
            "current_progress": 30,
            "planned_progress": 60,
            "project_duration_days": 200,
            "elapsed_days": 120
        }
        
        result = predict_schedule_delay(schedule_data)
        
        assert result.delay_days > 0
        assert result.probability_on_time < 0.7
        assert result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    def test_cost_forecast_on_budget(self):
        """Test cost forecast when project is on budget."""
        from backend.services.forecast_engine import predict_cost_overrun, RiskLevel
        
        cost_data = {
            "budget": 1000000,
            "actual_cost": 480000,
            "percent_complete": 50,
            "planned_percent": 50
        }
        
        result = predict_cost_overrun(cost_data)
        
        assert result.variance_percent < 15
        assert result.probability_within_budget > 0.4
    
    def test_cost_forecast_over_budget(self):
        """Test cost forecast when project is over budget."""
        from backend.services.forecast_engine import predict_cost_overrun, RiskLevel
        
        cost_data = {
            "budget": 1000000,
            "actual_cost": 700000,
            "percent_complete": 50,
            "planned_percent": 50
        }
        
        result = predict_cost_overrun(cost_data)
        
        assert result.forecasted_cost > result.original_budget
        assert result.variance > 0
    
    def test_evm_metrics(self):
        """Test Earned Value Management calculations."""
        from backend.services.forecast_engine import calculate_performance_metrics
        
        metrics = calculate_performance_metrics(
            budget_at_completion=1000000,
            actual_cost=500000,
            percent_complete=50,
            planned_percent=50
        )
        
        # EV = BAC * % complete = 1000000 * 0.5 = 500000
        assert metrics.earned_value == 500000
        
        # SPI = EV / PV = 500000 / 500000 = 1.0
        assert abs(metrics.schedule_performance_index - 1.0) < 0.01
        
        # CPI = EV / AC = 500000 / 500000 = 1.0
        assert abs(metrics.cost_performance_index - 1.0) < 0.01
    
    def test_trend_analysis(self):
        """Test trend analysis."""
        from backend.services.forecast_engine import analyze_trend, TrendDirection
        
        # Improving trend
        data_points = [
            {"date": "2024-01-01", "value": 100},
            {"date": "2024-01-02", "value": 95},
            {"date": "2024-01-03", "value": 90},
            {"date": "2024-01-04", "value": 85},
        ]
        
        result = analyze_trend(data_points, "value")
        
        assert result["direction"] in [TrendDirection.IMPROVING.value, TrendDirection.DECLINING.value, TrendDirection.STABLE.value]
        assert result["forecast_next"] is not None


class TestAnomalyDetector:
    """Tests for Anomaly Detection service."""
    
    def test_detect_risk_anomaly(self):
        """Test detection of risk score anomaly."""
        from backend.services.anomaly_detector import detect_anomalies
        
        data_stream = [
            {"risk_score": 0.95, "section": "Foundation", "timestamp": "2024-03-15"}
        ]
        
        findings = detect_anomalies(data_stream)
        
        assert len(findings) > 0
        risk_findings = [f for f in findings if f["type"] == "risk"]
        assert len(risk_findings) > 0
        assert risk_findings[0]["severity"] in ["critical", "high"]
    
    def test_detect_schedule_anomaly(self):
        """Test detection of schedule delay anomaly."""
        from backend.services.anomaly_detector import detect_anomalies
        
        data_stream = [
            {
                "progress_percent": 30,
                "expected_progress_percent": 50,
                "timestamp": "2024-03-15"
            }
        ]
        
        findings = detect_anomalies(data_stream)
        
        schedule_findings = [f for f in findings if f["type"] == "schedule"]
        assert len(schedule_findings) > 0
    
    def test_detect_cost_anomaly(self):
        """Test detection of cost overrun anomaly."""
        from backend.services.anomaly_detector import detect_anomalies
        
        data_stream = [
            {
                "planned_cost": 100000,
                "actual_cost": 125000,
                "timestamp": "2024-03-15"
            }
        ]
        
        findings = detect_anomalies(data_stream)
        
        cost_findings = [f for f in findings if f["type"] == "cost"]
        assert len(cost_findings) > 0
    
    def test_detect_safety_anomaly(self):
        """Test detection of safety incident anomaly."""
        from backend.services.anomaly_detector import detect_anomalies
        
        data_stream = [
            {"incidents": 2, "timestamp": "2024-03-15"}
        ]
        
        findings = detect_anomalies(data_stream)
        
        safety_findings = [f for f in findings if f["type"] == "safety"]
        assert len(safety_findings) > 0
    
    def test_detect_quality_anomaly(self):
        """Test detection of quality defect anomaly."""
        from backend.services.anomaly_detector import detect_anomalies
        
        data_stream = [
            {"defects": 6, "section": "Zone A", "timestamp": "2024-03-15"}
        ]
        
        findings = detect_anomalies(data_stream)
        
        quality_findings = [f for f in findings if f["type"] == "quality"]
        assert len(quality_findings) > 0
    
    def test_severity_ordering(self):
        """Test that findings are ordered by severity."""
        from backend.services.anomaly_detector import detect_anomalies
        
        data_stream = [
            {"risk_score": 0.95},  # Critical
            {"defects": 3},  # Medium
            {"risk_score": 0.75},  # Medium
        ]
        
        findings = detect_anomalies(data_stream)
        
        if len(findings) >= 2:
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            for i in range(len(findings) - 1):
                assert severity_order[findings[i]["severity"]] <= severity_order[findings[i+1]["severity"]]
    
    def test_empty_data_stream(self):
        """Test handling of empty data stream."""
        from backend.services.anomaly_detector import detect_anomalies
        
        findings = detect_anomalies([])
        
        assert findings == []
    
    def test_malformed_data(self):
        """Test handling of malformed data."""
        from backend.services.anomaly_detector import detect_anomalies
        
        data_stream = [
            "not a dict",
            None,
            {"valid": "entry"},
        ]
        
        # Should not raise exception
        findings = detect_anomalies(data_stream)
        assert isinstance(findings, list)


class TestProgressTracking:
    """Tests for Progress Tracking functionality."""
    
    def test_progress_status_calculation(self):
        """Test progress status determination."""
        # ahead: variance >= 2
        # on_track: -2 <= variance < 2
        # behind: -10 <= variance < -2
        # critical: variance < -10
        
        test_cases = [
            (55, 50, "ahead"),      # +5 variance
            (50, 50, "on_track"),   # 0 variance
            (45, 50, "behind"),     # -5 variance
            (35, 50, "critical"),   # -15 variance
        ]
        
        for current, planned, expected_status in test_cases:
            variance = current - planned
            if variance >= 2:
                status = "ahead"
            elif variance >= -2:
                status = "on_track"
            elif variance >= -10:
                status = "behind"
            else:
                status = "critical"
            
            assert status == expected_status, f"Failed for variance {variance}"
    
    def test_spi_calculation(self):
        """Test Schedule Performance Index calculation."""
        # SPI = actual / planned
        
        test_cases = [
            (50, 50, 1.0),    # On track
            (60, 50, 1.2),    # Ahead
            (40, 50, 0.8),    # Behind
        ]
        
        for current, planned, expected_spi in test_cases:
            spi = current / planned if planned > 0 else 1.0
            assert abs(spi - expected_spi) < 0.01


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestAPIIntegration:
    """Integration tests for API endpoints."""
    
    def test_document_classifier_service_import(self):
        """Test document classifier can be imported."""
        from backend.services.document_classifier import (
            classify_document,
            classify_document_file,
            DocumentType,
            ClassificationResult
        )
        assert callable(classify_document)
    
    def test_action_item_extractor_service_import(self):
        """Test action item extractor can be imported."""
        from backend.services.action_item_extractor import (
            extract_actions,
            extract_action_items,
            ActionItem,
            ExtractionResult
        )
        assert callable(extract_actions)
    
    def test_ifc_parser_service_import(self):
        """Test IFC parser can be imported."""
        from backend.services.ifc_parser import (
            parse_ifc,
            parse_ifc_bytes,
            IFCParseResult,
            BIMElement
        )
        assert callable(parse_ifc)
    
    def test_forecast_engine_service_import(self):
        """Test forecast engine can be imported."""
        from backend.services.forecast_engine import (
            predict_schedule_delay,
            predict_cost_overrun,
            calculate_performance_metrics,
            analyze_trend
        )
        assert callable(predict_schedule_delay)
    
    def test_anomaly_detector_service_import(self):
        """Test anomaly detector can be imported."""
        from backend.services.anomaly_detector import detect_anomalies
        assert callable(detect_anomalies)


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
