"""
Attention Visualization for Seismic Models

Shows WHERE and WHEN the model focuses during prediction

Capabilities:
- Temporal attention (which time windows matter most)
- Spatial attention (which seismic frequencies matter)
- Channel attention (X/Y/Z axis importance)
- Layer-wise attention progression
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AttentionType(str, Enum):
    """Types of attention mechanisms"""
    TEMPORAL = "temporal"  # Attention across time
    SPATIAL = "spatial"  # Attention across space/frequencies
    CHANNEL = "channel"  # Attention across input channels (X/Y/Z)
    MULTI_HEAD = "multi_head"  # Multi-head self-attention


@dataclass
class AttentionMap:
    """Attention weights visualization"""
    attention_type: AttentionType
    weights: np.ndarray  # Attention weights (normalized 0-1)
    input_shape: Tuple[int, ...]  # Shape of input data

    # Interpretable regions
    high_attention_regions: List[Dict[str, Any]]  # Regions with >0.8 attention
    low_attention_regions: List[Dict[str, Any]]  # Regions with <0.2 attention

    # Metadata
    layer_name: str = "unknown"
    head_index: Optional[int] = None  # For multi-head attention


class AttentionVisualizer:
    """
    Visualize attention mechanisms in neural networks

    Works with:
    - U-Net (encoder-decoder attention)
    - Transformers (self-attention)
    - CNNs with attention modules
    """

    def __init__(self, model: Any = None):
        """
        Initialize attention visualizer

        Args:
            model: Neural network model (PyTorch/TensorFlow)
        """
        self.model = model
        self.attention_hooks = []
        self.attention_cache = {}

        logger.info("Attention visualizer initialized")

    def extract_attention(
        self,
        input_data: np.ndarray,
        layer_names: Optional[List[str]] = None
    ) -> Dict[str, AttentionMap]:
        """
        Extract attention maps from model

        Args:
            input_data: Input seismic data (B, C, T) or (B, C, H, W)
            layer_names: Specific layers to extract attention from

        Returns:
            Dictionary of layer_name -> AttentionMap
        """
        if self.model is None:
            return self._mock_attention_maps(input_data)

        # In production: Register forward hooks to capture attention
        # attention_maps = {}
        # for name, module in self.model.named_modules():
        #     if 'attention' in name.lower():
        #         hook = module.register_forward_hook(self._attention_hook)
        #         self.attention_hooks.append(hook)
        #
        # # Forward pass
        # output = self.model(input_data)
        #
        # # Extract attention from cache
        # attention_maps = self._process_attention_cache()
        #
        # # Remove hooks
        # for hook in self.attention_hooks:
        #     hook.remove()

        return self._mock_attention_maps(input_data)

    def visualize_temporal_attention(
        self,
        seismic_data: np.ndarray,
        attention_weights: np.ndarray
    ) -> Dict[str, Any]:
        """
        Visualize attention across time

        Args:
            seismic_data: Seismic waveform (channels, time)
            attention_weights: Temporal attention weights (time,)

        Returns:
            Visualization data for plotting
        """
        # Normalize attention weights
        att_norm = attention_weights / (attention_weights.max() + 1e-8)

        # Find high attention periods
        threshold_high = 0.8
        threshold_low = 0.2

        high_attention_periods = []
        low_attention_periods = []

        for i, weight in enumerate(att_norm):
            if weight > threshold_high:
                high_attention_periods.append({
                    "time_index": i,
                    "weight": float(weight),
                    "description": f"High focus at t={i}"
                })
            elif weight < threshold_low:
                low_attention_periods.append({
                    "time_index": i,
                    "weight": float(weight),
                    "description": f"Low focus at t={i}"
                })

        return {
            "attention_weights": att_norm.tolist(),
            "high_attention_periods": high_attention_periods,
            "low_attention_periods": low_attention_periods,
            "interpretation": self._interpret_temporal_attention(high_attention_periods)
        }

    def visualize_frequency_attention(
        self,
        spectrogram: np.ndarray,
        attention_weights: np.ndarray
    ) -> Dict[str, Any]:
        """
        Visualize attention across frequency bands

        Args:
            spectrogram: Frequency spectrogram (freq, time)
            attention_weights: Frequency attention (freq,)

        Returns:
            Visualization data showing which frequencies matter
        """
        att_norm = attention_weights / (attention_weights.max() + 1e-8)

        # Define seismic frequency bands
        freq_bands = {
            "ultra_low": (0.001, 0.01),  # <0.01 Hz
            "very_low": (0.01, 0.1),     # 0.01-0.1 Hz
            "low": (0.1, 1.0),           # 0.1-1 Hz (P-waves, S-waves)
            "medium": (1.0, 10.0),       # 1-10 Hz (local earthquakes)
            "high": (10.0, 100.0),       # 10-100 Hz (near-field)
        }

        # Map attention to frequency bands
        band_importance = {}
        n_freqs = len(att_norm)

        for band_name, (f_min, f_max) in freq_bands.items():
            # Simplified: Map indices to frequency ranges
            idx_min = int(f_min / 100.0 * n_freqs)
            idx_max = int(f_max / 100.0 * n_freqs)

            if idx_max > n_freqs:
                idx_max = n_freqs

            if idx_min < idx_max:
                band_att = att_norm[idx_min:idx_max].mean()
                band_importance[band_name] = float(band_att)

        return {
            "frequency_attention": att_norm.tolist(),
            "band_importance": band_importance,
            "interpretation": self._interpret_frequency_attention(band_importance)
        }

    def visualize_channel_attention(
        self,
        attention_weights: np.ndarray
    ) -> Dict[str, Any]:
        """
        Visualize attention across seismic channels (X/Y/Z axes)

        Args:
            attention_weights: Channel attention (3,) for X, Y, Z

        Returns:
            Channel importance visualization
        """
        channels = ["X", "Y", "Z"]
        att_norm = attention_weights / (attention_weights.sum() + 1e-8)

        channel_importance = {
            channels[i]: {
                "weight": float(att_norm[i]),
                "percentage": float(att_norm[i] * 100)
            }
            for i in range(len(channels))
        }

        # Determine dominant axis
        dominant_idx = np.argmax(att_norm)
        dominant_axis = channels[dominant_idx]

        return {
            "channel_importance": channel_importance,
            "dominant_axis": dominant_axis,
            "interpretation": f"Model focuses most on {dominant_axis}-axis ({att_norm[dominant_idx]*100:.1f}%)"
        }

    def _interpret_temporal_attention(
        self,
        high_attention_periods: List[Dict]
    ) -> str:
        """Interpret temporal attention in human-readable form"""
        if not high_attention_periods:
            return "Model shows uniform attention across all time periods."

        time_indices = [p["time_index"] for p in high_attention_periods]

        if time_indices:
            early_focus = min(time_indices)
            late_focus = max(time_indices)

            interpretation = f"Model focuses on periods t={early_focus} to t={late_focus}. "

            # Seismic interpretation
            if early_focus < 10:
                interpretation += "Early P-wave arrival detected. "
            if late_focus > 50:
                interpretation += "Sustained attention suggests significant event. "

        return interpretation

    def _interpret_frequency_attention(
        self,
        band_importance: Dict[str, float]
    ) -> str:
        """Interpret frequency attention"""
        # Find most important band
        max_band = max(band_importance, key=band_importance.get)
        max_importance = band_importance[max_band]

        interpretations = {
            "ultra_low": "Very low frequency focus suggests tectonic movement",
            "very_low": "Low frequency focus indicates deep earthquake source",
            "low": "1-10 Hz band suggests P-wave and S-wave detection",
            "medium": "Medium frequency indicates local earthquake",
            "high": "High frequency suggests near-field strong motion"
        }

        return f"{interpretations.get(max_band, 'Unknown pattern')} ({max_importance*100:.1f}% attention)"

    def _mock_attention_maps(self, input_data: np.ndarray) -> Dict[str, AttentionMap]:
        """Generate mock attention maps for demo"""
        # Simulate attention patterns
        time_steps = 100

        # Temporal attention (focus on specific time windows)
        temporal_att = np.zeros(time_steps)
        temporal_att[20:40] = 0.8  # High attention on P-wave arrival
        temporal_att[60:80] = 0.9  # Very high attention on mainshock

        # Spatial/frequency attention
        freq_bins = 50
        spatial_att = np.random.rand(freq_bins) * 0.3
        spatial_att[5:15] = 0.9  # High attention on 1-5 Hz (earthquake band)

        # Channel attention (X/Y/Z)
        channel_att = np.array([0.35, 0.25, 0.40])  # Z-axis most important

        return {
            "temporal": AttentionMap(
                attention_type=AttentionType.TEMPORAL,
                weights=temporal_att,
                input_shape=(3, time_steps),
                high_attention_regions=[
                    {"start": 20, "end": 40, "weight": 0.8},
                    {"start": 60, "end": 80, "weight": 0.9}
                ],
                low_attention_regions=[],
                layer_name="encoder_layer3"
            ),
            "spatial": AttentionMap(
                attention_type=AttentionType.SPATIAL,
                weights=spatial_att,
                input_shape=(freq_bins,),
                high_attention_regions=[
                    {"start": 5, "end": 15, "weight": 0.9}
                ],
                low_attention_regions=[],
                layer_name="frequency_attention"
            ),
            "channel": AttentionMap(
                attention_type=AttentionType.CHANNEL,
                weights=channel_att,
                input_shape=(3,),
                high_attention_regions=[],
                low_attention_regions=[],
                layer_name="channel_attention"
            )
        }

    def create_heatmap_data(
        self,
        seismic_waveform: np.ndarray,
        attention_map: AttentionMap
    ) -> Dict[str, Any]:
        """
        Create heatmap overlay for visualization

        Args:
            seismic_waveform: Original waveform (channels, time)
            attention_map: Attention weights to overlay

        Returns:
            Heatmap data for plotting
        """
        return {
            "waveform": seismic_waveform.tolist(),
            "attention_overlay": attention_map.weights.tolist(),
            "colormap": "hot",  # Matplotlib colormap
            "alpha": 0.6,  # Transparency
            "high_attention_markers": attention_map.high_attention_regions
        }
