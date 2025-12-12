"""
JARVIS Explainable AI (XAI) System

Mission: Make earthquake predictions transparent and trustworthy

Components:
- Attention Visualization: Show what the model "sees"
- SHAP Explainer: Feature importance for each prediction
- Uncertainty Quantification: Confidence intervals and calibration
- Counterfactual Engine: "What-if" scenario analysis
"""

from ai_assistant_pro.jarvis.xai.attention_maps import AttentionVisualizer
from ai_assistant_pro.jarvis.xai.shap_explainer import SHAPExplainer
from ai_assistant_pro.jarvis.xai.uncertainty_calibration import UncertaintyQuantifier

__all__ = [
    "AttentionVisualizer",
    "SHAPExplainer",
    "UncertaintyQuantifier",
]
