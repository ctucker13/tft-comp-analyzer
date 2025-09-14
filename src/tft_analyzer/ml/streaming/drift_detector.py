#!/usr/bin/env python3
"""
Concept Drift Detection for TFT Meta Changes

Implements multiple drift detection algorithms:
- ADWIN (Adaptive Windowing)
- Page-Hinkley test
- CUSUM (Cumulative Sum)
- Custom TFT meta drift detection

Detects when the meta significantly changes and triggers:
- Faster model adaptation (reduced tau)
- Increased update frequency
- Model retraining alerts
"""

import logging
import numpy as np
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class DriftType(Enum):
    """Types of drift detection."""
    NO_DRIFT = "no_drift"
    GRADUAL_DRIFT = "gradual_drift"
    SUDDEN_DRIFT = "sudden_drift"
    PATCH_DRIFT = "patch_drift"


@dataclass
class DriftDetection:
    """Drift detection result."""
    drift_type: DriftType
    confidence: float
    metric_name: str
    change_magnitude: float
    detection_time: datetime
    recommended_action: str


class ADWINDetector:
    """
    Adaptive Windowing (ADWIN) drift detector.

    Maintains a sliding window that automatically adjusts its size
    based on detected changes in data distribution.
    """

    def __init__(self, delta: float = 0.002, min_window_size: int = 30):
        self.delta = delta  # Confidence level
        self.min_window_size = min_window_size
        self.window = deque()
        self.total = 0.0
        self.variance = 0.0
        self.width = 0

    def add_element(self, value: float) -> bool:
        """
        Add new element and check for drift.

        Args:
            value: New metric value

        Returns:
            True if drift detected
        """
        self.window.append(value)
        self.total += value
        self.width += 1

        # Update variance (simplified)
        if len(self.window) >= 2:
            mean = self.total / self.width
            self.variance = np.var(list(self.window))

        drift_detected = False

        # Check for drift if we have enough data
        if self.width >= self.min_window_size:
            drift_detected = self._check_drift()

        return drift_detected

    def _check_drift(self) -> bool:
        """Check for drift using ADWIN algorithm."""
        if self.width < 2:
            return False

        # Simplified ADWIN - check if recent half significantly differs from older half
        mid_point = self.width // 2
        recent_values = list(self.window)[-mid_point:]
        older_values = list(self.window)[:-mid_point]

        if len(recent_values) < 5 or len(older_values) < 5:
            return False

        recent_mean = np.mean(recent_values)
        older_mean = np.mean(older_values)

        # Calculate threshold based on window properties
        n1, n2 = len(older_values), len(recent_values)
        m = 1 / (1/n1 + 1/n2)

        epsilon_cut = np.sqrt((2 * self.variance * np.log(2 / self.delta)) / m)

        # Drift detected if means differ significantly
        if abs(recent_mean - older_mean) > epsilon_cut:
            # Trim window
            self._trim_window()
            return True

        return False

    def _trim_window(self):
        """Trim window when drift is detected."""
        # Keep only recent half
        mid_point = self.width // 2
        for _ in range(mid_point):
            if self.window:
                removed = self.window.popleft()
                self.total -= removed
                self.width -= 1


class PageHinkleyDetector:
    """
    Page-Hinkley test for detecting changes in mean.

    Good for detecting gradual drifts in model performance.
    """

    def __init__(self, threshold: float = 50.0, alpha: float = 0.9999):
        self.threshold = threshold
        self.alpha = alpha
        self.x_mean = 0.0
        self.sample_count = 0
        self.sum_diff = 0.0
        self.min_sum = 0.0

    def add_element(self, value: float) -> bool:
        """
        Add new element and check for drift.

        Args:
            value: New metric value

        Returns:
            True if drift detected
        """
        self.sample_count += 1

        # Update running mean
        if self.sample_count == 1:
            self.x_mean = value
        else:
            self.x_mean = self.alpha * self.x_mean + (1 - self.alpha) * value

        # Update Page-Hinkley statistic
        self.sum_diff += value - self.x_mean
        self.min_sum = min(self.min_sum, self.sum_diff)

        # Check for drift
        drift_detected = (self.sum_diff - self.min_sum) > self.threshold

        if drift_detected:
            self.reset()

        return drift_detected

    def reset(self):
        """Reset detector after drift detection."""
        self.sum_diff = 0.0
        self.min_sum = 0.0


class CUSUMDetector:
    """
    CUSUM (Cumulative Sum) detector for mean shift detection.
    """

    def __init__(self, threshold: float = 5.0, drift_threshold: float = 50.0):
        self.threshold = threshold
        self.drift_threshold = drift_threshold
        self.sum_pos = 0.0
        self.sum_neg = 0.0
        self.mean = 0.0
        self.sample_count = 0

    def add_element(self, value: float) -> bool:
        """Add new element and check for drift."""
        self.sample_count += 1

        # Update running mean
        self.mean = ((self.sample_count - 1) * self.mean + value) / self.sample_count

        # CUSUM statistics
        diff = value - self.mean
        self.sum_pos = max(0, self.sum_pos + diff - self.threshold)
        self.sum_neg = min(0, self.sum_neg + diff + self.threshold)

        # Check for drift
        drift_detected = (self.sum_pos > self.drift_threshold or
                         self.sum_neg < -self.drift_threshold)

        if drift_detected:
            self.reset()

        return drift_detected

    def reset(self):
        """Reset detector after drift detection."""
        self.sum_pos = 0.0
        self.sum_neg = 0.0


class TFTMetaDriftDetector:
    """
    Comprehensive drift detector for TFT meta changes.

    Monitors multiple metrics:
    - Average placement by composition
    - Top-4 rates
    - Composition popularity shifts
    - Patch transitions
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Multiple detectors for different metrics
        self.detectors = {
            'avg_placement': ADWINDetector(delta=0.01),
            'top4_rate': ADWINDetector(delta=0.01),
            'comp_diversity': PageHinkleyDetector(threshold=30.0),
            'win_rate_variance': CUSUMDetector(threshold=0.05)
        }

        # Composition tracking
        self.comp_performance = {}
        self.comp_popularity = deque(maxlen=100)  # Last 100 measurement windows

        # Patch tracking
        self.current_patch = None
        self.patch_change_time = None

        # Drift history
        self.drift_history = deque(maxlen=50)

        # Metrics history
        self.metrics_history = {
            'avg_placement': deque(maxlen=200),
            'top4_rate': deque(maxlen=200),
            'comp_diversity': deque(maxlen=200),
            'win_rate_variance': deque(maxlen=200)
        }

    def update_metrics(self,
                      match_results: List[Dict],
                      current_patch: Optional[str] = None) -> List[DriftDetection]:
        """
        Update metrics and check for drift.

        Args:
            match_results: List of recent match results
            current_patch: Current game patch

        Returns:
            List of drift detections
        """
        detected_drifts = []

        # Check for patch changes
        if current_patch and current_patch != self.current_patch:
            patch_drift = self._detect_patch_change(current_patch)
            if patch_drift:
                detected_drifts.append(patch_drift)

        # Calculate current metrics
        metrics = self._calculate_metrics(match_results)

        # Update each detector
        for metric_name, detector in self.detectors.items():
            if metric_name in metrics:
                metric_value = metrics[metric_name]

                # Store metric history
                self.metrics_history[metric_name].append(metric_value)

                # Check for drift
                drift_detected = detector.add_element(metric_value)

                if drift_detected:
                    drift = self._create_drift_detection(metric_name, metric_value)
                    detected_drifts.append(drift)

        # Update composition tracking
        self._update_composition_tracking(match_results)

        # Log drift detections
        for drift in detected_drifts:
            self.logger.warning(f"🚨 Drift detected: {drift}")

        return detected_drifts

    def _detect_patch_change(self, new_patch: str) -> Optional[DriftDetection]:
        """Detect patch changes."""
        old_patch = self.current_patch
        self.current_patch = new_patch
        self.patch_change_time = datetime.now()

        if old_patch is not None:  # Not the first patch we've seen
            return DriftDetection(
                drift_type=DriftType.PATCH_DRIFT,
                confidence=1.0,
                metric_name="patch_change",
                change_magnitude=1.0,
                detection_time=datetime.now(),
                recommended_action=f"Patch changed: {old_patch} -> {new_patch}. Increase adaptation rate."
            )

        return None

    def _calculate_metrics(self, match_results: List[Dict]) -> Dict[str, float]:
        """Calculate drift detection metrics from match results."""
        if not match_results:
            return {}

        # Extract placements
        placements = []
        top4_results = []
        comp_counts = {}

        for match in match_results:
            participants = match.get('participants', [])
            for participant in participants:
                placement = participant.get('placement', 8)
                placements.append(placement)
                top4_results.append(1 if placement <= 4 else 0)

                # Track composition popularity
                comp_type = self._identify_composition(participant)
                comp_counts[comp_type] = comp_counts.get(comp_type, 0) + 1

        # Calculate metrics
        metrics = {}

        if placements:
            metrics['avg_placement'] = np.mean(placements)
            metrics['top4_rate'] = np.mean(top4_results)

        if comp_counts:
            # Composition diversity (Shannon entropy)
            total_comps = sum(comp_counts.values())
            if total_comps > 0:
                probs = [count / total_comps for count in comp_counts.values()]
                metrics['comp_diversity'] = -sum(p * np.log(p) for p in probs if p > 0)

        # Win rate variance across compositions
        if len(comp_counts) > 1:
            comp_win_rates = []
            for comp_type in comp_counts:
                comp_matches = [
                    p for match in match_results
                    for p in match.get('participants', [])
                    if self._identify_composition(p) == comp_type
                ]
                if comp_matches:
                    top4_rate = np.mean([1 if p.get('placement', 8) <= 4 else 0
                                       for p in comp_matches])
                    comp_win_rates.append(top4_rate)

            if len(comp_win_rates) > 1:
                metrics['win_rate_variance'] = np.var(comp_win_rates)

        return metrics

    def _identify_composition(self, participant: Dict) -> str:
        """Identify the composition type from participant data."""
        traits = participant.get('traits', [])

        # Simple composition identification based on active traits
        active_traits = [trait['name'] for trait in traits if trait.get('tier_current', 0) > 0]

        # Common composition patterns
        if 'Sniper' in active_traits:
            return 'Sniper'
        elif 'Star Guardian' in active_traits:
            return 'Star Guardian'
        elif 'TheCrew' in active_traits:
            return 'TheCrew'
        else:
            return 'Flex'

    def _update_composition_tracking(self, match_results: List[Dict]):
        """Update composition performance tracking."""
        comp_performance = {}

        for match in match_results:
            participants = match.get('participants', [])
            for participant in participants:
                comp_type = self._identify_composition(participant)
                placement = participant.get('placement', 8)

                if comp_type not in comp_performance:
                    comp_performance[comp_type] = []
                comp_performance[comp_type].append(placement)

        # Update stored performance
        for comp_type, placements in comp_performance.items():
            if comp_type not in self.comp_performance:
                self.comp_performance[comp_type] = deque(maxlen=1000)

            self.comp_performance[comp_type].extend(placements)

    def _create_drift_detection(self, metric_name: str, current_value: float) -> DriftDetection:
        """Create a drift detection result."""
        # Calculate change magnitude
        history = self.metrics_history[metric_name]
        if len(history) >= 2:
            recent_avg = np.mean(list(history)[-10:])  # Last 10 values
            older_avg = np.mean(list(history)[-50:-10]) if len(history) >= 50 else recent_avg
            change_magnitude = abs(recent_avg - older_avg) / (older_avg + 1e-8)
        else:
            change_magnitude = 0.0

        # Determine drift type and confidence
        if change_magnitude > 0.2:
            drift_type = DriftType.SUDDEN_DRIFT
            confidence = 0.9
        elif change_magnitude > 0.1:
            drift_type = DriftType.GRADUAL_DRIFT
            confidence = 0.7
        else:
            drift_type = DriftType.NO_DRIFT
            confidence = 0.5

        # Recommended action
        if drift_type == DriftType.SUDDEN_DRIFT:
            action = f"Sudden drift in {metric_name}. Reduce tau to 24h, increase update frequency to 30min."
        elif drift_type == DriftType.GRADUAL_DRIFT:
            action = f"Gradual drift in {metric_name}. Reduce tau to 48h, monitor closely."
        else:
            action = "Continue normal operation."

        detection = DriftDetection(
            drift_type=drift_type,
            confidence=confidence,
            metric_name=metric_name,
            change_magnitude=change_magnitude,
            detection_time=datetime.now(),
            recommended_action=action
        )

        # Store in history
        self.drift_history.append(detection)

        return detection

    def get_adaptation_params(self) -> Dict[str, Any]:
        """
        Get recommended adaptation parameters based on recent drift detections.

        Returns:
            Dictionary with recommended tau_hours and update_frequency
        """
        # Default parameters
        tau_hours = 72.0  # 3 days
        update_frequency_minutes = 60  # 1 hour

        # Check recent drift detections (last 6 hours)
        recent_cutoff = datetime.now() - timedelta(hours=6)
        recent_drifts = [d for d in self.drift_history if d.detection_time >= recent_cutoff]

        if recent_drifts:
            # Find most severe recent drift
            max_magnitude = max(d.change_magnitude for d in recent_drifts)
            has_sudden_drift = any(d.drift_type == DriftType.SUDDEN_DRIFT for d in recent_drifts)
            has_patch_drift = any(d.drift_type == DriftType.PATCH_DRIFT for d in recent_drifts)

            if has_patch_drift or has_sudden_drift:
                tau_hours = 24.0  # 1 day
                update_frequency_minutes = 30  # 30 minutes
            elif max_magnitude > 0.1:
                tau_hours = 48.0  # 2 days
                update_frequency_minutes = 45  # 45 minutes

        return {
            'tau_hours': tau_hours,
            'update_frequency_minutes': update_frequency_minutes,
            'recent_drift_count': len(recent_drifts),
            'adaptation_reason': f"Based on {len(recent_drifts)} recent drift detections"
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get drift detector statistics."""
        return {
            'total_drifts_detected': len(self.drift_history),
            'current_patch': self.current_patch,
            'patch_change_time': self.patch_change_time.isoformat() if self.patch_change_time else None,
            'recent_metrics': {
                name: list(history)[-10:] if history else []
                for name, history in self.metrics_history.items()
            },
            'composition_performance': {
                comp: {
                    'avg_placement': np.mean(placements) if placements else 0,
                    'sample_count': len(placements)
                }
                for comp, placements in self.comp_performance.items()
            },
            'detector_states': {
                name: {
                    'class': detector.__class__.__name__,
                    'ready': hasattr(detector, 'sample_count') and detector.sample_count > 10
                }
                for name, detector in self.detectors.items()
            }
        }


def main():
    """Test the drift detector."""
    detector = TFTMetaDriftDetector()

    print("🧪 Testing TFT Meta Drift Detection")
    print("=" * 50)

    # Simulate some match results
    import random

    # Normal meta
    normal_matches = []
    for i in range(50):
        participants = []
        for j in range(8):
            participants.append({
                'placement': random.randint(1, 8),
                'traits': [
                    {'name': random.choice(['Sniper', 'Star Guardian', 'TheCrew']), 'tier_current': 2}
                ]
            })
        normal_matches.append({'participants': participants})

    # Test normal period
    drifts = detector.update_metrics(normal_matches, "15.4")
    print(f"Normal meta - Drifts detected: {len(drifts)}")

    # Simulate meta shift
    shifted_matches = []
    for i in range(30):
        participants = []
        for j in range(8):
            # Different placement distribution (meta shift)
            placement = random.choices([1, 2, 3, 4, 5, 6, 7, 8],
                                     weights=[3, 2, 2, 2, 1, 1, 1, 1])[0]
            participants.append({
                'placement': placement,
                'traits': [
                    {'name': 'Star Guardian', 'tier_current': 3}  # New dominant comp
                ]
            })
        shifted_matches.append({'participants': participants})

    # Test shift period
    drifts = detector.update_metrics(shifted_matches, "15.4")
    print(f"Shifted meta - Drifts detected: {len(drifts)}")

    # Test patch change
    drifts = detector.update_metrics(shifted_matches[-5:], "15.5")
    print(f"Patch change - Drifts detected: {len(drifts)}")

    # Show adaptation parameters
    params = detector.get_adaptation_params()
    print(f"Recommended parameters: {params}")

    # Show statistics
    stats = detector.get_statistics()
    print(f"Detector statistics: {stats}")


if __name__ == "__main__":
    main()