# ML/AI Service - ITEM 120
# Machine learning model integration for predictions, classifications, and insights

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import pickle
from datetime import datetime
import numpy as np

from ..core.logging_config import get_logger
from ..core.config_enhanced import settings

logger = get_logger(__name__)


class ModelType(str, Enum):
    """Types of ML models."""
    CLASSIFIER = "classifier"
    REGRESSOR = "regressor"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"
    TIME_SERIES = "time_series"
    NLP = "nlp"
    COMPUTER_VISION = "computer_vision"


class PredictionType(str, Enum):
    """Types of predictions."""
    COST_OVERRUN = "cost_overrun"
    SCHEDULE_DELAY = "schedule_delay"
    SAFETY_RISK = "safety_risk"
    QUALITY_ISSUE = "quality_issue"
    RESOURCE_DEMAND = "resource_demand"
    CLASH_PROBABILITY = "clash_probability"
    DOCUMENT_CATEGORY = "document_category"
    SENTIMENT = "sentiment"


@dataclass
class ModelMetadata:
    """Metadata for ML model."""
    name: str
    version: str
    type: ModelType
    prediction_type: PredictionType
    trained_date: datetime
    accuracy: float
    feature_names: List[str]
    model_path: Path
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Prediction:
    """ML model prediction."""
    prediction_type: PredictionType
    value: Any  # Could be class label, numeric value, etc.
    confidence: float
    probabilities: Optional[Dict[str, float]] = None
    explanation: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TrainingResult:
    """Result of model training."""
    model_id: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_time_seconds: float
    samples_trained: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class MLService:
    """
    Machine Learning service for construction AI.

    Features:
    - Cost overrun prediction
    - Schedule delay forecasting
    - Safety risk assessment
    - Quality issue detection
    - Resource demand forecasting
    - Document classification
    - Sentiment analysis
    - Anomaly detection
    """

    def __init__(self, models_directory: Optional[Path] = None):
        """
        Initialize ML service.

        Args:
            models_directory: Directory containing trained models
        """
        self.logger = get_logger(self.__class__.__name__)
        self.models_directory = models_directory or Path("models")
        self.loaded_models: Dict[str, Any] = {}
        self.model_metadata: Dict[str, ModelMetadata] = {}

    def load_model(self, model_id: str) -> bool:
        """
        Load a trained model.

        Args:
            model_id: Model identifier

        Returns:
            True if loaded successfully
        """
        try:
            model_path = self.models_directory / f"{model_id}.pkl"

            if not model_path.exists():
                self.logger.warning(f"Model not found: {model_path}")
                return False

            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)

            self.loaded_models[model_id] = model_data['model']
            self.model_metadata[model_id] = model_data['metadata']

            self.logger.info(f"Loaded model: {model_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load model {model_id}: {e}")
            return False

    def predict_cost_overrun(
        self,
        project_features: Dict[str, Any]
    ) -> Prediction:
        """
        Predict probability of cost overrun.

        Args:
            project_features: Project characteristics (budget, complexity, duration, etc.)

        Returns:
            Prediction with overrun probability
        """
        model_id = "cost_overrun_classifier"

        # For demo: simulate prediction
        # In production, use actual trained model
        features = self._extract_features(project_features, [
            'budget', 'duration_months', 'team_size', 'complexity_score'
        ])

        # Simulated prediction
        risk_score = np.random.random()  # Replace with actual model.predict()

        if risk_score > 0.7:
            prediction_class = "high_risk"
            confidence = risk_score
        elif risk_score > 0.4:
            prediction_class = "medium_risk"
            confidence = 0.7
        else:
            prediction_class = "low_risk"
            confidence = 0.8

        return Prediction(
            prediction_type=PredictionType.COST_OVERRUN,
            value=prediction_class,
            confidence=confidence,
            probabilities={
                "low_risk": 1 - risk_score if risk_score < 0.4 else 0.2,
                "medium_risk": 0.5 if 0.4 <= risk_score <= 0.7 else 0.3,
                "high_risk": risk_score if risk_score > 0.7 else 0.1,
            },
            explanation={
                "top_risk_factors": ["budget_size", "team_experience", "complexity"],
                "risk_score": float(risk_score)
            }
        )

    def predict_schedule_delay(
        self,
        project_features: Dict[str, Any],
        current_progress: float
    ) -> Prediction:
        """
        Predict probability and magnitude of schedule delay.

        Args:
            project_features: Project characteristics
            current_progress: Current completion percentage (0-100)

        Returns:
            Prediction with delay probability and estimated days
        """
        # Simulated prediction logic
        delay_days = 0

        if current_progress < 50 and project_features.get('complexity_score', 0) > 7:
            delay_days = np.random.randint(10, 30)
            confidence = 0.75
        elif current_progress < 75:
            delay_days = np.random.randint(0, 15)
            confidence = 0.6
        else:
            delay_days = 0
            confidence = 0.85

        return Prediction(
            prediction_type=PredictionType.SCHEDULE_DELAY,
            value=delay_days,
            confidence=confidence,
            explanation={
                "current_progress": current_progress,
                "critical_path_risk": "medium" if delay_days > 10 else "low"
            }
        )

    def assess_safety_risk(
        self,
        site_conditions: Dict[str, Any],
        weather_data: Optional[Dict[str, Any]] = None
    ) -> Prediction:
        """
        Assess safety risk based on site conditions.

        Args:
            site_conditions: Current site conditions
            weather_data: Optional weather forecast data

        Returns:
            Safety risk prediction
        """
        risk_factors = []
        risk_score = 0.0

        # Check site conditions
        if site_conditions.get('working_at_height', False):
            risk_score += 0.3
            risk_factors.append('working_at_height')

        if site_conditions.get('heavy_equipment_active', False):
            risk_score += 0.2
            risk_factors.append('heavy_equipment')

        # Check weather
        if weather_data:
            if weather_data.get('wind_speed_mph', 0) > 25:
                risk_score += 0.3
                risk_factors.append('high_winds')

            if weather_data.get('precipitation', False):
                risk_score += 0.2
                risk_factors.append('precipitation')

        risk_level = "high" if risk_score > 0.7 else "medium" if risk_score > 0.4 else "low"

        return Prediction(
            prediction_type=PredictionType.SAFETY_RISK,
            value=risk_level,
            confidence=0.8,
            explanation={
                "risk_score": risk_score,
                "risk_factors": risk_factors,
                "recommendations": self._get_safety_recommendations(risk_factors)
            }
        )

    def classify_document(
        self,
        document_text: str,
        document_metadata: Optional[Dict[str, Any]] = None
    ) -> Prediction:
        """
        Classify document type.

        Args:
            document_text: Document content
            document_metadata: Optional metadata

        Returns:
            Document classification prediction
        """
        text_lower = document_text.lower()

        # Simple rule-based classification (replace with ML model)
        if 'rfi' in text_lower or 'request for information' in text_lower:
            category = 'rfi'
            confidence = 0.9
        elif 'submittal' in text_lower:
            category = 'submittal'
            confidence = 0.85
        elif 'change order' in text_lower:
            category = 'change_order'
            confidence = 0.9
        elif 'invoice' in text_lower or 'payment' in text_lower:
            category = 'invoice'
            confidence = 0.8
        else:
            category = 'other'
            confidence = 0.5

        return Prediction(
            prediction_type=PredictionType.DOCUMENT_CATEGORY,
            value=category,
            confidence=confidence,
            probabilities={
                category: confidence,
                'other': 1 - confidence
            }
        )

    def predict_resource_demand(
        self,
        project_schedule: Dict[str, Any],
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, List[Tuple[datetime, float]]]:
        """
        Forecast resource demand over time.

        Args:
            project_schedule: Project schedule data
            historical_data: Historical resource usage data

        Returns:
            Resource demand forecasts by resource type
        """
        # Simulate time-series forecasting
        forecasts = {}

        resource_types = ['labor', 'equipment', 'materials']

        for resource_type in resource_types:
            # Generate simulated forecast
            forecast_points = []
            base_demand = np.random.uniform(50, 100)

            for i in range(30):  # 30-day forecast
                date = datetime.utcnow()
                demand = base_demand * (1 + np.random.uniform(-0.2, 0.2))
                forecast_points.append((date, float(demand)))

            forecasts[resource_type] = forecast_points

        return forecasts

    def detect_anomalies(
        self,
        data: List[float],
        threshold: float = 2.0
    ) -> List[int]:
        """
        Detect anomalies in time series data.

        Args:
            data: Time series data points
            threshold: Standard deviation threshold

        Returns:
            Indices of anomalous points
        """
        if len(data) < 3:
            return []

        data_array = np.array(data)
        mean = np.mean(data_array)
        std = np.std(data_array)

        anomalies = []
        for i, value in enumerate(data):
            z_score = abs((value - mean) / std) if std > 0 else 0
            if z_score > threshold:
                anomalies.append(i)

        return anomalies

    def analyze_sentiment(self, text: str) -> Prediction:
        """
        Analyze sentiment of text (e.g., meeting notes, communications).

        Args:
            text: Text to analyze

        Returns:
            Sentiment prediction
        """
        # Simple sentiment analysis (replace with trained model)
        positive_words = ['good', 'excellent', 'great', 'satisfied', 'progress', 'success']
        negative_words = ['issue', 'problem', 'delay', 'concern', 'risk', 'failure']

        text_lower = text.lower()

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            sentiment = 'positive'
            score = min(0.9, 0.5 + (positive_count - negative_count) * 0.1)
        elif negative_count > positive_count:
            sentiment = 'negative'
            score = min(0.9, 0.5 + (negative_count - positive_count) * 0.1)
        else:
            sentiment = 'neutral'
            score = 0.6

        return Prediction(
            prediction_type=PredictionType.SENTIMENT,
            value=sentiment,
            confidence=score,
            probabilities={
                'positive': score if sentiment == 'positive' else 0.2,
                'neutral': score if sentiment == 'neutral' else 0.3,
                'negative': score if sentiment == 'negative' else 0.2,
            }
        )

    def train_model(
        self,
        model_type: ModelType,
        prediction_type: PredictionType,
        training_data: List[Dict[str, Any]],
        labels: List[Any],
        model_id: str
    ) -> TrainingResult:
        """
        Train a new ML model.

        Args:
            model_type: Type of model to train
            prediction_type: What to predict
            training_data: Training features
            labels: Training labels
            model_id: Identifier for saving the model

        Returns:
            Training results
        """
        start_time = datetime.utcnow()

        # Simulated training (replace with actual ML training)
        self.logger.info(f"Training {model_type.value} model for {prediction_type.value}")

        # Simulate metrics
        accuracy = np.random.uniform(0.75, 0.95)
        precision = np.random.uniform(0.70, 0.90)
        recall = np.random.uniform(0.70, 0.90)
        f1_score = 2 * (precision * recall) / (precision + recall)

        training_time = (datetime.utcnow() - start_time).total_seconds()

        result = TrainingResult(
            model_id=model_id,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            training_time_seconds=training_time,
            samples_trained=len(training_data),
            metadata={
                'model_type': model_type.value,
                'prediction_type': prediction_type.value
            }
        )

        self.logger.info(f"Model trained: {model_id} (accuracy: {accuracy:.2%})")
        return result

    def _extract_features(
        self,
        data: Dict[str, Any],
        feature_names: List[str]
    ) -> List[float]:
        """Extract feature values from data dict."""
        features = []
        for name in feature_names:
            value = data.get(name, 0)
            features.append(float(value) if isinstance(value, (int, float)) else 0.0)
        return features

    def _get_safety_recommendations(self, risk_factors: List[str]) -> List[str]:
        """Get safety recommendations based on risk factors."""
        recommendations = []

        if 'working_at_height' in risk_factors:
            recommendations.append("Ensure fall protection systems are in place")

        if 'heavy_equipment' in risk_factors:
            recommendations.append("Maintain clear exclusion zones around equipment")

        if 'high_winds' in risk_factors:
            recommendations.append("Suspend crane operations if winds exceed limits")

        if 'precipitation' in risk_factors:
            recommendations.append("Ensure slip-resistant surfaces and drainage")

        return recommendations or ["Continue monitoring site conditions"]


# Singleton instance
_ml_service = None


def get_ml_service() -> MLService:
    """Get or create ML service singleton."""
    global _ml_service
    if _ml_service is None:
        _ml_service = MLService()
    return _ml_service
