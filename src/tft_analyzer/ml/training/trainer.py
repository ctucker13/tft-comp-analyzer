"""
ML model training pipeline for TFT strategy prediction.

This module handles training the TFT strategy model with collected data,
including preprocessing, hyperparameter optimization, and model persistence.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, mean_squared_error, classification_report
import optuna
from optuna.trial import Trial

try:
    from .data_collector import TrainingDataPoint, TFTTrainingDataCollector
    from ..models.strategy_model import TFTStrategyModel
    from config.settings import Settings
except ImportError:
    from src.tft_analyzer.ml.training.data_collector import TrainingDataPoint, TFTTrainingDataCollector
    from src.tft_analyzer.ml.models.strategy_model import TFTStrategyModel
    from config.settings import Settings


class TFTModelTrainer:
    """Handles training of TFT strategy prediction models."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)

        # Training configuration
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger.info(f"Using device: {self.device}")

        # Model and data paths
        self.models_dir = Path("models")
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Training state
        self.model = None
        self.feature_scaler = None
        self.label_encoders = {}
        self.feature_names = []

    async def train_model(
        self,
        training_data: Optional[List[TrainingDataPoint]] = None,
        model_name: str = "tft_strategy_model",
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.001,
        optimize_hyperparams: bool = True
    ) -> Dict[str, Any]:
        """
        Train the TFT strategy model.

        Args:
            training_data: Training data points (if None, will collect new data)
            model_name: Name for saved model
            epochs: Number of training epochs
            batch_size: Training batch size
            learning_rate: Learning rate
            optimize_hyperparams: Whether to run hyperparameter optimization

        Returns:
            Training results and metrics
        """
        self.logger.info("Starting TFT model training...")

        # Collect or use provided training data
        if training_data is None:
            collector = TFTTrainingDataCollector(self.settings)
            training_data = await collector.collect_training_data(num_matches=50)

        if not training_data:
            raise ValueError("No training data available")

        # Preprocess data
        X, y = self._preprocess_training_data(training_data)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y['placement_category']
        )

        # Optimize hyperparameters if requested
        if optimize_hyperparams:
            best_params = self._optimize_hyperparameters(X_train, y_train, X_test, y_test)
            self.logger.info(f"Best hyperparameters: {best_params}")
        else:
            best_params = {
                'hidden_dim': 256,
                'num_layers': 3,
                'dropout': 0.3,
                'learning_rate': learning_rate
            }

        # Train final model with best parameters
        model, training_history = self._train_model_with_params(
            X_train, y_train, X_test, y_test,
            best_params, epochs, batch_size
        )

        # Evaluate model
        evaluation_metrics = self._evaluate_model(model, X_test, y_test)

        # Save model and training artifacts
        self._save_model(model, model_name, best_params, evaluation_metrics)

        results = {
            'model_name': model_name,
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'hyperparameters': best_params,
            'training_history': training_history,
            'evaluation_metrics': evaluation_metrics,
            'feature_count': len(self.feature_names),
            'training_completed': datetime.now().isoformat()
        }

        self.logger.info("Model training completed successfully!")
        return results

    def _preprocess_training_data(self, training_data: List[TrainingDataPoint]) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """Preprocess training data into features and labels."""
        self.logger.info(f"Preprocessing {len(training_data)} training samples...")

        # Extract features
        feature_dicts = []
        labels = {
            'placement': [],
            'comp_type': [],
            'risk_level': [],
            'placement_category': []  # For stratification
        }

        for point in training_data:
            # Combine all features
            features = point.features.copy()
            features.update({
                'round_number': point.round_number,
                'stage': point.stage,
                'player_level': point.player_level,
                'gold': point.gold,
                'health': point.health
            })
            feature_dicts.append(features)

            # Extract labels
            labels['placement'].append(point.placement)
            labels['comp_type'].append(point.comp_type)
            labels['risk_level'].append(point.risk_level)

            # Create placement category for stratification
            if point.placement <= 2:
                labels['placement_category'].append('top2')
            elif point.placement <= 4:
                labels['placement_category'].append('top4')
            else:
                labels['placement_category'].append('bot4')

        # Convert to DataFrame for easier processing
        features_df = pd.DataFrame(feature_dicts)

        # Handle missing values
        features_df = features_df.fillna(0)

        # Get consistent feature names
        self.feature_names = sorted(features_df.columns.tolist())
        features_df = features_df[self.feature_names]

        # Scale features
        self.feature_scaler = StandardScaler()
        X = self.feature_scaler.fit_transform(features_df.values)

        # Encode categorical labels
        self.label_encoders['comp_type'] = LabelEncoder()
        encoded_comp_type = self.label_encoders['comp_type'].fit_transform(labels['comp_type'])

        # Prepare target dictionary
        y = {
            'placement': np.array(labels['placement'], dtype=np.float32),
            'comp_type': encoded_comp_type.astype(np.int64),
            'risk_level': np.array(labels['risk_level'], dtype=np.float32),
            'placement_category': np.array(labels['placement_category'])  # For stratification only
        }

        self.logger.info(f"Preprocessed data: {X.shape[0]} samples, {X.shape[1]} features")
        return X, y

    def _optimize_hyperparameters(
        self,
        X_train: np.ndarray,
        y_train: Dict[str, np.ndarray],
        X_test: np.ndarray,
        y_test: Dict[str, np.ndarray],
        n_trials: int = 20
    ) -> Dict[str, Any]:
        """Optimize hyperparameters using Optuna."""
        self.logger.info(f"Starting hyperparameter optimization with {n_trials} trials...")

        def objective(trial: Trial) -> float:
            # Suggest hyperparameters
            params = {
                'hidden_dim': trial.suggest_int('hidden_dim', 64, 512, step=64),
                'num_layers': trial.suggest_int('num_layers', 2, 5),
                'dropout': trial.suggest_float('dropout', 0.1, 0.5),
                'learning_rate': trial.suggest_float('learning_rate', 1e-4, 1e-2, log=True)
            }

            # Train model with these parameters
            model, _ = self._train_model_with_params(
                X_train, y_train, X_test, y_test,
                params, epochs=20, batch_size=32
            )

            # Evaluate on validation set
            metrics = self._evaluate_model(model, X_test, y_test)

            # Return composite score (lower is better)
            placement_mse = metrics['placement_mse']
            comp_type_accuracy = metrics['comp_type_accuracy']
            risk_mse = metrics['risk_mse']

            # Weighted combination (minimize placement error, maximize accuracy)
            score = placement_mse + (1 - comp_type_accuracy) + risk_mse

            return score

        # Run optimization
        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=n_trials)

        best_params = study.best_params
        self.logger.info(f"Hyperparameter optimization completed. Best score: {study.best_value:.4f}")

        return best_params

    def _train_model_with_params(
        self,
        X_train: np.ndarray,
        y_train: Dict[str, np.ndarray],
        X_test: np.ndarray,
        y_test: Dict[str, np.ndarray],
        params: Dict[str, Any],
        epochs: int,
        batch_size: int
    ) -> Tuple[TFTStrategyModel, Dict[str, List[float]]]:
        """Train model with specific parameters."""

        # Create model
        input_dim = X_train.shape[1]
        num_comp_types = len(np.unique(y_train['comp_type']))

        model = TFTStrategyModel(
            input_dim=input_dim,
            hidden_dim=params['hidden_dim'],
            num_layers=params['num_layers'],
            dropout=params['dropout'],
            num_comp_types=num_comp_types
        ).to(self.device)

        # Setup training
        optimizer = optim.Adam(model.parameters(), lr=params['learning_rate'])

        # Loss functions
        placement_loss_fn = nn.MSELoss()
        comp_type_loss_fn = nn.CrossEntropyLoss()
        risk_loss_fn = nn.MSELoss()

        # Training history
        history = {
            'train_loss': [],
            'val_loss': [],
            'placement_mse': [],
            'comp_type_acc': [],
            'risk_mse': []
        }

        # Convert to tensors
        X_train_tensor = torch.FloatTensor(X_train).to(self.device)
        y_placement_train = torch.FloatTensor(y_train['placement']).to(self.device)
        y_comp_type_train = torch.LongTensor(y_train['comp_type']).to(self.device)
        y_risk_train = torch.FloatTensor(y_train['risk_level']).to(self.device)

        X_test_tensor = torch.FloatTensor(X_test).to(self.device)
        y_placement_test = torch.FloatTensor(y_test['placement']).to(self.device)
        y_comp_type_test = torch.LongTensor(y_test['comp_type']).to(self.device)
        y_risk_test = torch.FloatTensor(y_test['risk_level']).to(self.device)

        # Training loop
        model.train()
        for epoch in range(epochs):
            # Forward pass
            outputs = model(X_train_tensor)

            # Calculate losses
            placement_loss = placement_loss_fn(outputs['placement'].squeeze(), y_placement_train)
            comp_type_loss = comp_type_loss_fn(outputs['comp_type'], y_comp_type_train)
            risk_loss = risk_loss_fn(outputs['risk_level'].squeeze(), y_risk_train)

            # Combined loss
            total_loss = placement_loss + comp_type_loss + risk_loss

            # Backward pass
            optimizer.zero_grad()
            total_loss.backward()
            optimizer.step()

            # Validation
            if epoch % 10 == 0:
                model.eval()
                with torch.no_grad():
                    val_outputs = model(X_test_tensor)

                    val_placement_loss = placement_loss_fn(
                        val_outputs['placement'].squeeze(), y_placement_test
                    )
                    val_comp_type_loss = comp_type_loss_fn(
                        val_outputs['comp_type'], y_comp_type_test
                    )
                    val_risk_loss = risk_loss_fn(
                        val_outputs['risk_level'].squeeze(), y_risk_test
                    )
                    val_total_loss = val_placement_loss + val_comp_type_loss + val_risk_loss

                    # Calculate accuracy
                    _, predicted = torch.max(val_outputs['comp_type'], 1)
                    comp_type_acc = (predicted == y_comp_type_test).float().mean().item()

                    history['train_loss'].append(total_loss.item())
                    history['val_loss'].append(val_total_loss.item())
                    history['placement_mse'].append(val_placement_loss.item())
                    history['comp_type_acc'].append(comp_type_acc)
                    history['risk_mse'].append(val_risk_loss.item())

                model.train()

        return model, history

    def _evaluate_model(self, model: TFTStrategyModel, X_test: np.ndarray, y_test: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Evaluate trained model performance."""
        model.eval()

        with torch.no_grad():
            X_test_tensor = torch.FloatTensor(X_test).to(self.device)
            outputs = model(X_test_tensor)

            # Placement MSE
            placement_pred = outputs['placement'].squeeze().cpu().numpy()
            placement_mse = mean_squared_error(y_test['placement'], placement_pred)

            # Comp type accuracy
            _, comp_type_pred = torch.max(outputs['comp_type'], 1)
            comp_type_pred = comp_type_pred.cpu().numpy()
            comp_type_accuracy = accuracy_score(y_test['comp_type'], comp_type_pred)

            # Risk level MSE
            risk_pred = outputs['risk_level'].squeeze().cpu().numpy()
            risk_mse = mean_squared_error(y_test['risk_level'], risk_pred)

        return {
            'placement_mse': float(placement_mse),
            'comp_type_accuracy': float(comp_type_accuracy),
            'risk_mse': float(risk_mse),
            'samples_evaluated': len(X_test)
        }

    def _save_model(self, model: TFTStrategyModel, model_name: str, params: Dict, metrics: Dict):
        """Save trained model and artifacts."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = self.models_dir / f"{model_name}_{timestamp}"
        model_path.mkdir(exist_ok=True)

        # Save model weights
        torch.save(model.state_dict(), model_path / "model_weights.pt")

        # Save model config
        config = {
            'input_dim': model.input_dim,
            'hidden_dim': model.hidden_dim,
            'num_layers': model.num_layers,
            'dropout': model.dropout,
            'num_comp_types': model.num_comp_types,
            'feature_names': self.feature_names,
            'hyperparameters': params,
            'evaluation_metrics': metrics,
            'training_timestamp': timestamp
        }

        with open(model_path / "config.json", 'w') as f:
            json.dump(config, f, indent=2)

        # Save preprocessing artifacts
        import joblib
        if self.feature_scaler:
            joblib.dump(self.feature_scaler, model_path / "feature_scaler.pkl")

        if self.label_encoders:
            joblib.dump(self.label_encoders, model_path / "label_encoders.pkl")

        self.logger.info(f"Model saved to {model_path}")

    def load_model(self, model_path: str) -> TFTStrategyModel:
        """Load a trained model."""
        model_path = Path(model_path)

        # Load config
        with open(model_path / "config.json", 'r') as f:
            config = json.load(f)

        # Create model
        model = TFTStrategyModel(
            input_dim=config['input_dim'],
            hidden_dim=config['hidden_dim'],
            num_layers=config['num_layers'],
            dropout=config['dropout'],
            num_comp_types=config['num_comp_types']
        ).to(self.device)

        # Load weights
        model.load_state_dict(torch.load(model_path / "model_weights.pt", map_location=self.device))

        # Load preprocessing artifacts
        import joblib
        self.feature_scaler = joblib.load(model_path / "feature_scaler.pkl")
        self.label_encoders = joblib.load(model_path / "label_encoders.pkl")
        self.feature_names = config['feature_names']

        self.logger.info(f"Model loaded from {model_path}")
        return model


async def main():
    """Test training pipeline."""
    settings = Settings()
    trainer = TFTModelTrainer(settings)

    # Test with small dataset
    results = await trainer.train_model(
        epochs=10,
        optimize_hyperparams=False
    )

    print("Training Results:")
    for key, value in results.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())