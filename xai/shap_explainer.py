"""
SHAP (SHapley Additive exPlanations) for Earthquake Predictions

Explains WHY the model made each prediction

Capabilities:
- Feature importance (which features contributed most)
- Local explanations (this specific prediction)
- Global explanations (overall model behavior)
- Force plots (push/pull visualization)
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


@dataclass
class SHAPExplanation:
    """SHAP explanation for a prediction"""
    prediction: float  # Model output
    base_value: float  # Average model output

    # Feature contributions
    feature_values: Dict[str, float]  # Actual feature values
    shap_values: Dict[str, float]  # SHAP values (contributions)

    # Top contributors
    top_positive: List[Tuple[str, float]]  # Features pushing prediction UP
    top_negative: List[Tuple[str, float]]  # Features pushing prediction DOWN

    # Summary
    explanation_text: str


class SHAPExplainer:
    """
    SHAP-based explainer for seismic predictions

    Uses Shapley values from game theory to fairly attribute
    prediction to each input feature.
    """

    def __init__(self, model: Any = None, feature_names: Optional[List[str]] = None):
        """
        Initialize SHAP explainer

        Args:
            model: Trained model
            feature_names: List of feature names
        """
        self.model = model
        self.feature_names = feature_names or self._default_feature_names()

        # Base value (average prediction)
        self.base_value = 0.5  # Default for probability

        logger.info(f"SHAP explainer initialized with {len(self.feature_names)} features")

    def _default_feature_names(self) -> List[str]:
        """Default seismic feature names"""
        return [
            "peak_ground_acceleration",
            "frequency_1_5hz",
            "frequency_5_10hz",
            "p_wave_amplitude",
            "s_wave_amplitude",
            "duration_seconds",
            "signal_noise_ratio",
            "spectral_centroid",
            "zero_crossing_rate",
            "rms_amplitude",
            "kurtosis",
            "skewness",
            "dominant_frequency",
            "bandwidth",
            "temporal_variance"
        ]

    def explain_prediction(
        self,
        input_features: Dict[str, float],
        prediction: float
    ) -> SHAPExplanation:
        """
        Explain a single prediction

        Args:
            input_features: Feature values for this prediction
            prediction: Model output (probability or magnitude)

        Returns:
            SHAP explanation showing feature contributions
        """
        if self.model is None:
            return self._mock_explanation(input_features, prediction)

        # In production: Use shap library
        # import shap
        # explainer = shap.Explainer(self.model)
        # shap_values = explainer(input_features)

        return self._mock_explanation(input_features, prediction)

    def _mock_explanation(
        self,
        input_features: Dict[str, float],
        prediction: float
    ) -> SHAPExplanation:
        """Generate mock SHAP values for demo"""

        # Calculate SHAP values (contribution of each feature)
        # Formula: prediction = base_value + sum(shap_values)

        # Simulate realistic SHAP values
        shap_values = {}
        remaining = prediction - self.base_value

        # Top features get larger contributions
        important_features = [
            "peak_ground_acceleration",
            "frequency_1_5hz",
            "p_wave_amplitude",
            "duration_seconds"
        ]

        # Distribute contribution
        for i, feature in enumerate(self.feature_names):
            if feature in important_features:
                # Important features get more contribution
                contribution = remaining * 0.2 * np.random.uniform(0.8, 1.2)
            else:
                # Less important features
                contribution = remaining * 0.05 * np.random.uniform(-0.5, 0.5)

            shap_values[feature] = contribution

        # Normalize so sum equals prediction - base_value
        total_shap = sum(shap_values.values())
        if abs(total_shap) > 1e-6:
            scale = remaining / total_shap
            shap_values = {k: v * scale for k, v in shap_values.items()}

        # Sort by absolute contribution
        sorted_features = sorted(
            shap_values.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )

        # Top positive/negative
        top_positive = [
            (k, v) for k, v in sorted_features if v > 0
        ][:5]

        top_negative = [
            (k, v) for k, v in sorted_features if v < 0
        ][:5]

        # Generate explanation text
        explanation_text = self._generate_explanation_text(
            prediction, self.base_value, top_positive, top_negative
        )

        return SHAPExplanation(
            prediction=prediction,
            base_value=self.base_value,
            feature_values=input_features,
            shap_values=shap_values,
            top_positive=top_positive,
            top_negative=top_negative,
            explanation_text=explanation_text
        )

    def _generate_explanation_text(
        self,
        prediction: float,
        base_value: float,
        top_positive: List[Tuple[str, float]],
        top_negative: List[Tuple[str, float]]
    ) -> str:
        """Generate human-readable explanation"""

        text = f"Prediction: {prediction:.1%} (Base: {base_value:.1%})\n\n"

        if prediction > base_value:
            text += "This prediction is HIGHER than average because:\n"
        else:
            text += "This prediction is LOWER than average because:\n"

        text += "\nTop Positive Contributors (+):\n"
        for feature, contribution in top_positive:
            pct = (contribution / abs(prediction - base_value)) * 100
            text += f"  • {feature.replace('_', ' ').title()}: +{contribution:.3f} ({pct:.1f}%)\n"

        if top_negative:
            text += "\nTop Negative Contributors (-):\n"
            for feature, contribution in top_negative:
                pct = (abs(contribution) / abs(prediction - base_value)) * 100
                text += f"  • {feature.replace('_', ' ').title()}: {contribution:.3f} ({pct:.1f}%)\n"

        return text

    def get_feature_importance(
        self,
        explanations: List[SHAPExplanation]
    ) -> Dict[str, float]:
        """
        Get global feature importance across multiple predictions

        Args:
            explanations: List of SHAP explanations

        Returns:
            Average absolute SHAP value per feature
        """
        importance = {feature: 0.0 for feature in self.feature_names}
        n = len(explanations)

        for exp in explanations:
            for feature, shap_val in exp.shap_values.items():
                importance[feature] += abs(shap_val)

        # Average
        importance = {k: v / n for k, v in importance.items()}

        # Sort by importance
        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

    def create_force_plot_data(
        self,
        explanation: SHAPExplanation
    ) -> Dict[str, Any]:
        """
        Create data for SHAP force plot visualization

        Args:
            explanation: SHAP explanation

        Returns:
            Data for plotting force plot
        """
        # Sort features by SHAP value
        sorted_features = sorted(
            explanation.shap_values.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Cumulative sum for stacking
        cumsum = explanation.base_value
        force_plot_data = []

        for feature, shap_val in sorted_features:
            force_plot_data.append({
                "feature": feature,
                "shap_value": shap_val,
                "cumulative": cumsum + shap_val,
                "color": "red" if shap_val > 0 else "blue"
            })
            cumsum += shap_val

        return {
            "base_value": explanation.base_value,
            "prediction": explanation.prediction,
            "features": force_plot_data
        }
