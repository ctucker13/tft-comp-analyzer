#!/usr/bin/env python3
"""
Model testing and evaluation script for TFT strategy prediction.

This script provides comprehensive testing and evaluation of trained models,
including performance metrics, prediction analysis, and model comparisons.

Usage:
    python scripts/test_model.py --model-path models/tft_strategy_20250913_180000
    python scripts/test_model.py --compare-models --models-dir models/
    python scripts/test_model.py --generate-predictions --input-file test_scenarios.json
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from src.tft_analyzer.ml.training.trainer import TFTModelTrainer
from src.tft_analyzer.ml.training.data_collector import TFTTrainingDataCollector, TrainingDataPoint

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class ModelTester:
    """Comprehensive model testing and evaluation."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.trainer = TFTModelTrainer(settings)

    def load_model_info(self, model_path: str) -> Dict[str, Any]:
        """Load model configuration and metadata."""
        model_path = Path(model_path)
        config_file = model_path / "config.json"

        if not config_file.exists():
            raise FileNotFoundError(f"Model config not found: {config_file}")

        with open(config_file, 'r') as f:
            config = json.load(f)

        return config

    def evaluate_model_performance(self, model_path: str, test_data: List[TrainingDataPoint]) -> Dict[str, Any]:
        """Evaluate model performance on test data."""
        logger.info(f"Evaluating model: {model_path}")

        # Load model
        model = self.trainer.load_model(model_path)
        model.eval()

        # Preprocess test data
        X_test, y_test = self.trainer._preprocess_training_data(test_data)

        # Evaluate
        metrics = self.trainer._evaluate_model(model, X_test, y_test)

        # Additional detailed analysis
        import torch
        with torch.no_grad():
            X_test_tensor = torch.FloatTensor(X_test).to(self.trainer.device)
            outputs = model(X_test_tensor)

            # Placement predictions
            placement_pred = outputs['placement'].squeeze().cpu().numpy()
            placement_true = y_test['placement']

            # Comp type predictions
            _, comp_type_pred = torch.max(outputs['comp_type'], 1)
            comp_type_pred = comp_type_pred.cpu().numpy()
            comp_type_true = y_test['comp_type']

            # Risk predictions
            risk_pred = outputs['risk_level'].squeeze().cpu().numpy()
            risk_true = y_test['risk_level']

        # Detailed metrics
        detailed_metrics = {
            **metrics,
            'placement_mae': float(np.mean(np.abs(placement_pred - placement_true))),
            'placement_std': float(np.std(placement_pred - placement_true)),
            'risk_mae': float(np.mean(np.abs(risk_pred - risk_true))),
            'risk_std': float(np.std(risk_pred - risk_true)),
            'predictions': {
                'placement': placement_pred.tolist(),
                'comp_type': comp_type_pred.tolist(),
                'risk': risk_pred.tolist()
            },
            'ground_truth': {
                'placement': placement_true.tolist(),
                'comp_type': comp_type_true.tolist(),
                'risk': risk_true.tolist()
            }
        }

        return detailed_metrics

    def analyze_prediction_patterns(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze prediction patterns and biases."""
        preds = metrics['predictions']
        truth = metrics['ground_truth']

        analysis = {}

        # Placement analysis
        placement_pred = np.array(preds['placement'])
        placement_true = np.array(truth['placement'])

        analysis['placement'] = {
            'bias': float(np.mean(placement_pred - placement_true)),
            'correlation': float(np.corrcoef(placement_pred, placement_true)[0, 1]),
            'top4_accuracy': float(np.mean((placement_pred <= 4) == (placement_true <= 4))),
            'distribution_match': self._compare_distributions(placement_pred, placement_true)
        }

        # Comp type analysis
        comp_pred = np.array(preds['comp_type'])
        comp_true = np.array(truth['comp_type'])

        analysis['comp_type'] = {
            'per_class_accuracy': self._per_class_accuracy(comp_pred, comp_true),
            'confusion_stats': self._confusion_matrix_stats(comp_pred, comp_true)
        }

        # Risk analysis
        risk_pred = np.array(preds['risk'])
        risk_true = np.array(truth['risk'])

        analysis['risk'] = {
            'correlation': float(np.corrcoef(risk_pred, risk_true)[0, 1]),
            'calibration': self._risk_calibration_analysis(risk_pred, risk_true)
        }

        return analysis

    def _compare_distributions(self, pred: np.ndarray, true: np.ndarray) -> Dict:
        """Compare predicted vs true distributions."""
        from scipy import stats

        # KS test
        ks_stat, ks_pvalue = stats.ks_2samp(pred, true)

        return {
            'ks_statistic': float(ks_stat),
            'ks_pvalue': float(ks_pvalue),
            'mean_diff': float(np.mean(pred) - np.mean(true)),
            'std_diff': float(np.std(pred) - np.std(true))
        }

    def _per_class_accuracy(self, pred: np.ndarray, true: np.ndarray) -> Dict:
        """Calculate per-class accuracy."""
        unique_classes = np.unique(true)
        accuracies = {}

        for cls in unique_classes:
            cls_mask = (true == cls)
            if np.sum(cls_mask) > 0:
                accuracies[int(cls)] = float(np.mean(pred[cls_mask] == cls))

        return accuracies

    def _confusion_matrix_stats(self, pred: np.ndarray, true: np.ndarray) -> Dict:
        """Calculate confusion matrix statistics."""
        from sklearn.metrics import confusion_matrix, classification_report

        cm = confusion_matrix(true, pred)
        report = classification_report(true, pred, output_dict=True)

        return {
            'confusion_matrix': cm.tolist(),
            'classification_report': report
        }

    def _risk_calibration_analysis(self, pred: np.ndarray, true: np.ndarray) -> Dict:
        """Analyze risk prediction calibration."""
        # Binned calibration analysis
        n_bins = 10
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]

        calibration_data = []
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            in_bin = (pred > bin_lower) & (pred <= bin_upper)
            if np.sum(in_bin) > 0:
                prop_in_bin = np.mean(in_bin)
                accuracy_in_bin = np.mean(true[in_bin])
                avg_confidence_in_bin = np.mean(pred[in_bin])

                calibration_data.append({
                    'bin_lower': float(bin_lower),
                    'bin_upper': float(bin_upper),
                    'proportion': float(prop_in_bin),
                    'accuracy': float(accuracy_in_bin),
                    'confidence': float(avg_confidence_in_bin),
                    'count': int(np.sum(in_bin))
                })

        return calibration_data

    def generate_test_scenarios(self) -> List[Dict]:
        """Generate test scenarios for model predictions."""
        scenarios = [
            # Early game scenarios
            {
                'name': 'Early Game Reroll',
                'features': {
                    'level': 4,
                    'gold': 20,
                    'health': 80,
                    'round_number': 8,
                    'stage': 2,
                    'units_count': 4,
                    'trait_count': 2
                }
            },
            {
                'name': 'Mid Game Transition',
                'features': {
                    'level': 6,
                    'gold': 30,
                    'health': 60,
                    'round_number': 15,
                    'stage': 3,
                    'units_count': 6,
                    'trait_count': 3
                }
            },
            {
                'name': 'Fast 8 Economic',
                'features': {
                    'level': 7,
                    'gold': 50,
                    'health': 40,
                    'round_number': 21,
                    'stage': 4,
                    'units_count': 6,
                    'trait_count': 2
                }
            },
            {
                'name': 'Late Game Positioning',
                'features': {
                    'level': 8,
                    'gold': 20,
                    'health': 30,
                    'round_number': 28,
                    'stage': 5,
                    'units_count': 8,
                    'trait_count': 4
                }
            }
        ]

        return scenarios

    def test_model_predictions(self, model_path: str, scenarios: List[Dict] = None) -> Dict[str, Any]:
        """Test model predictions on specific scenarios."""
        if scenarios is None:
            scenarios = self.generate_test_scenarios()

        # Load model
        model = self.trainer.load_model(model_path)
        model.eval()

        results = {}

        import torch
        for scenario in scenarios:
            # Prepare feature vector
            features = scenario['features'].copy()

            # Ensure all expected features are present
            for feature_name in self.trainer.feature_names:
                if feature_name not in features:
                    features[feature_name] = 0

            # Create feature vector in correct order
            feature_vector = [features.get(fname, 0) for fname in self.trainer.feature_names]

            # Scale features
            feature_vector = self.trainer.feature_scaler.transform([feature_vector])

            # Make prediction
            with torch.no_grad():
                X_tensor = torch.FloatTensor(feature_vector).to(self.trainer.device)
                outputs = model(X_tensor)

                placement_pred = outputs['value_estimate'].squeeze().cpu().numpy()
                # Clamp comp_type predictions to valid range for label encoder
                comp_logits = outputs['comp_logits']
                if 'comp_type' in self.trainer.label_encoders:
                    n_classes = len(self.trainer.label_encoders['comp_type'].classes_)
                    comp_logits = comp_logits[:, :n_classes]  # Only use the classes the encoder knows
                comp_type_pred = torch.max(comp_logits, 1)[1].cpu().numpy()
                risk_pred = outputs['pivot_urgency'].squeeze().cpu().numpy()

            # Decode predictions
            comp_type_name = None
            if 'comp_type' in self.trainer.label_encoders:
                comp_type_name = self.trainer.label_encoders['comp_type'].inverse_transform(comp_type_pred)[0]

            results[scenario['name']] = {
                'features': features,
                'predictions': {
                    'placement': float(placement_pred.item() if placement_pred.ndim == 0 else placement_pred[0]),
                    'comp_type': comp_type_name,
                    'risk_level': float(risk_pred.item() if risk_pred.ndim == 0 else risk_pred[0])
                }
            }

        return results

    def compare_models(self, models_dir: str) -> Dict[str, Any]:
        """Compare multiple trained models."""
        models_dir = Path(models_dir)
        model_dirs = [d for d in models_dir.iterdir() if d.is_dir() and (d / "config.json").exists()]

        if len(model_dirs) < 2:
            logger.warning("Need at least 2 models for comparison")
            return {}

        comparison = {
            'models': {},
            'rankings': {}
        }

        for model_dir in model_dirs:
            try:
                config = self.load_model_info(str(model_dir))
                model_name = model_dir.name

                comparison['models'][model_name] = {
                    'config': config,
                    'metrics': config.get('evaluation_metrics', {}),
                    'training_time': config.get('training_timestamp', ''),
                    'hyperparameters': config.get('hyperparameters', {})
                }

            except Exception as e:
                logger.error(f"Error loading model {model_dir}: {e}")

        # Rank models by different metrics
        metrics_to_rank = ['placement_mse', 'comp_type_accuracy', 'risk_mse']

        for metric in metrics_to_rank:
            model_scores = []
            for name, data in comparison['models'].items():
                score = data['metrics'].get(metric)
                if score is not None:
                    model_scores.append((name, score))

            if model_scores:
                # Sort based on metric (lower is better for MSE, higher for accuracy)
                reverse = 'accuracy' in metric
                model_scores.sort(key=lambda x: x[1], reverse=reverse)
                comparison['rankings'][metric] = model_scores

        return comparison

    def generate_report(self, results: Dict[str, Any], output_file: str = None):
        """Generate comprehensive evaluation report."""
        report_lines = [
            "# TFT ML Model Evaluation Report",
            f"Generated: {pd.Timestamp.now()}",
            "",
            "## Model Performance Summary"
        ]

        if 'evaluation_metrics' in results:
            metrics = results['evaluation_metrics']
            report_lines.extend([
                f"- **Placement MSE**: {metrics.get('placement_mse', 'N/A'):.4f}",
                f"- **Comp Type Accuracy**: {metrics.get('comp_type_accuracy', 'N/A'):.1%}",
                f"- **Risk Level MSE**: {metrics.get('risk_mse', 'N/A'):.4f}",
                f"- **Test Samples**: {metrics.get('samples_evaluated', 'N/A')}",
                ""
            ])

        if 'prediction_analysis' in results:
            analysis = results['prediction_analysis']
            report_lines.extend([
                "## Prediction Analysis",
                f"- **Placement Bias**: {analysis['placement'].get('bias', 'N/A'):.3f}",
                f"- **Placement Correlation**: {analysis['placement'].get('correlation', 'N/A'):.3f}",
                f"- **Top 4 Accuracy**: {analysis['placement'].get('top4_accuracy', 'N/A'):.1%}",
                ""
            ])

        if 'test_scenarios' in results:
            report_lines.extend([
                "## Test Scenario Predictions",
                ""
            ])

            for scenario_name, data in results['test_scenarios'].items():
                preds = data['predictions']
                report_lines.extend([
                    f"### {scenario_name}",
                    f"- **Predicted Placement**: {preds['placement']:.1f}",
                    f"- **Comp Type**: {preds['comp_type']}",
                    f"- **Risk Level**: {preds['risk_level']:.2f}",
                    ""
                ])

        report_content = "\n".join(report_lines)

        if output_file:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(report_content)
            logger.info(f"Report saved to: {output_file}")

        return report_content

def main():
    """Main script entry point."""
    parser = argparse.ArgumentParser(description="TFT ML Model Testing and Evaluation")

    parser.add_argument('--model-path', type=str, help='Path to trained model directory')
    parser.add_argument('--test-data', type=str, help='Test data file (without .json extension)')
    parser.add_argument('--compare-models', action='store_true', help='Compare multiple models')
    parser.add_argument('--models-dir', type=str, default='models', help='Directory containing models')
    parser.add_argument('--generate-predictions', action='store_true', help='Generate predictions on test scenarios')
    parser.add_argument('--output-report', type=str, help='Output report file')

    args = parser.parse_args()

    # Validate arguments
    if not any([args.model_path, args.compare_models]):
        logger.error("Must specify --model-path or --compare-models")
        parser.print_help()
        sys.exit(1)

    # Initialize
    settings = Settings()
    tester = ModelTester(settings)

    results = {}

    try:
        if args.compare_models:
            # Compare models
            logger.info("Comparing models...")
            comparison = tester.compare_models(args.models_dir)

            if comparison:
                logger.info("Model Comparison Results:")
                for metric, rankings in comparison['rankings'].items():
                    logger.info(f"\n{metric.upper()} Rankings:")
                    for i, (name, score) in enumerate(rankings, 1):
                        logger.info(f"  {i}. {name}: {score:.4f}")

                results['model_comparison'] = comparison

        elif args.model_path:
            # Single model evaluation
            logger.info(f"Testing model: {args.model_path}")

            # Load test data if specified
            test_data = None
            if args.test_data:
                collector = TFTTrainingDataCollector(settings)
                test_data = collector.load_training_data(args.test_data)

                if not test_data:
                    logger.error(f"Failed to load test data: {args.test_data}")
                    sys.exit(1)

                # Evaluate on test data
                metrics = tester.evaluate_model_performance(args.model_path, test_data)
                analysis = tester.analyze_prediction_patterns(metrics)

                results['evaluation_metrics'] = metrics
                results['prediction_analysis'] = analysis

                logger.info("Evaluation Results:")
                logger.info(f"  Placement MSE: {metrics['placement_mse']:.4f}")
                logger.info(f"  Comp Accuracy: {metrics['comp_type_accuracy']:.1%}")
                logger.info(f"  Risk MSE: {metrics['risk_mse']:.4f}")

            # Generate predictions on test scenarios
            if args.generate_predictions:
                logger.info("Generating test scenario predictions...")
                scenarios = tester.test_model_predictions(args.model_path)

                results['test_scenarios'] = scenarios

                logger.info("Test Scenario Predictions:")
                for name, data in scenarios.items():
                    preds = data['predictions']
                    logger.info(f"  {name}:")
                    logger.info(f"    Placement: {preds['placement']:.1f}")
                    logger.info(f"    Comp: {preds['comp_type']}")
                    logger.info(f"    Risk: {preds['risk_level']:.2f}")

        # Generate report
        if results:
            report = tester.generate_report(results, args.output_report)

            if not args.output_report:
                print("\n" + report)

        logger.info("✅ Testing completed successfully!")

    except Exception as e:
        logger.error(f"❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()