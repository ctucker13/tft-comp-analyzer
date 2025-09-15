"""
Training pipeline manager for abstracting ML training from UI components.

This module provides a high-level interface for training operations,
decoupling the UI from the underlying training implementation.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

try:
    from .data_collector import TFTTrainingDataCollector, TrainingDataPoint
    from .trainer import TFTModelTrainer
    from config.settings import Settings
except ImportError:
    from src.tft_analyzer.ml.training.data_collector import TFTTrainingDataCollector, TrainingDataPoint
    from src.tft_analyzer.ml.training.trainer import TFTModelTrainer
    from config.settings import Settings


class TrainingStatus:
    """Training status tracking."""
    IDLE = "idle"
    COLLECTING_DATA = "collecting_data"
    TRAINING_MODEL = "training_model"
    COMPLETED = "completed"
    ERROR = "error"


class TrainingJob:
    """Training job with progress tracking."""

    def __init__(self, job_id: str, job_type: str):
        self.job_id = job_id
        self.job_type = job_type
        self.status = TrainingStatus.IDLE
        self.progress = 0.0
        self.message = ""
        self.results = None
        self.error = None
        self.start_time = None
        self.end_time = None

    def start(self):
        """Mark job as started."""
        self.start_time = datetime.now()
        self.progress = 0.0
        self.message = f"Starting {self.job_type}..."

    def update_progress(self, progress: float, message: str = ""):
        """Update job progress."""
        self.progress = max(0.0, min(1.0, progress))
        if message:
            self.message = message

    def complete(self, results: Any = None):
        """Mark job as completed."""
        self.status = TrainingStatus.COMPLETED
        self.progress = 1.0
        self.end_time = datetime.now()
        self.results = results
        self.message = f"{self.job_type} completed successfully"

    def fail(self, error: str):
        """Mark job as failed."""
        self.status = TrainingStatus.ERROR
        self.end_time = datetime.now()
        self.error = error
        self.message = f"{self.job_type} failed: {error}"


class TFTTrainingManager:
    """High-level training pipeline manager."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.active_jobs: Dict[str, TrainingJob] = {}

        # Initialize components
        self.data_collector = TFTTrainingDataCollector(settings)
        self.trainer = TFTModelTrainer(settings)

    def create_job(self, job_type: str) -> str:
        """Create a new training job."""
        job_id = f"{job_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        job = TrainingJob(job_id, job_type)
        self.active_jobs[job_id] = job
        return job_id

    def get_job_status(self, job_id: str) -> Optional[TrainingJob]:
        """Get job status."""
        return self.active_jobs.get(job_id)

    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available trained models."""
        models_dir = Path("models")
        models = []

        if not models_dir.exists():
            return models

        for model_dir in models_dir.iterdir():
            if model_dir.is_dir():
                config_file = model_dir / "config.json"
                if config_file.exists():
                    try:
                        import json
                        with open(config_file, 'r') as f:
                            config = json.load(f)

                        models.append({
                            'name': model_dir.name,
                            'path': str(model_dir),
                            'timestamp': config.get('training_timestamp', ''),
                            'metrics': config.get('evaluation_metrics', {}),
                            'hyperparameters': config.get('hyperparameters', {}),
                            'feature_count': config.get('feature_count', 0)
                        })

                    except Exception as e:
                        self.logger.error(f"Error loading model config {model_dir}: {e}")

        # Sort by timestamp (newest first)
        models.sort(key=lambda x: x['timestamp'], reverse=True)
        return models

    def list_training_data_files(self) -> List[Dict[str, Any]]:
        """List available training data files."""
        data_dir = Path("data/training")
        files = []

        if not data_dir.exists():
            return files

        for data_file in data_dir.glob("*.json"):
            try:
                stat = data_file.stat()
                files.append({
                    'filename': data_file.stem,
                    'path': str(data_file),
                    'size_mb': stat.st_size / (1024 * 1024),
                    'created': datetime.fromtimestamp(stat.st_ctime),
                    'modified': datetime.fromtimestamp(stat.st_mtime)
                })

            except Exception as e:
                self.logger.error(f"Error reading data file {data_file}: {e}")

        # Sort by creation time (newest first)
        files.sort(key=lambda x: x['created'], reverse=True)
        return files

    async def collect_training_data(
        self,
        num_matches: int = 50,
        min_rank: str = "MASTER",
        days_back: int = 3,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        """Collect training data with progress tracking."""

        job_id = self.create_job("data_collection")
        job = self.active_jobs[job_id]

        try:
            job.status = TrainingStatus.COLLECTING_DATA
            job.start()

            if progress_callback:
                progress_callback(0.1, "Testing API connection...")

            # Test API connection
            api_test = await self.data_collector.riot_client.test_api_connection()
            if not api_test:
                raise Exception("API connection failed. Check your Riot API key.")

            if progress_callback:
                progress_callback(0.2, "API connection successful")

            # Collect data with progress updates
            if progress_callback:
                progress_callback(0.3, f"Collecting data from {min_rank}+ players...")

            training_data = await self.data_collector.collect_training_data(
                num_matches=num_matches,
                min_rank=min_rank,
                days_back=days_back
            )

            if not training_data:
                raise Exception("No training data collected. Check API key and match criteria.")

            if progress_callback:
                progress_callback(0.8, f"Collected {len(training_data)} data points")

            # Save data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"training_data_{min_rank}_{len(training_data)}samples_{timestamp}"
            self.data_collector.save_training_data(training_data, filename)

            if progress_callback:
                progress_callback(1.0, f"Data saved as {filename}.json")

            # Complete job
            results = {
                'filename': filename,
                'samples_collected': len(training_data),
                'min_rank': min_rank,
                'num_matches_requested': num_matches,
                'days_back': days_back,
                'data_summary': self._summarize_training_data(training_data)
            }

            job.complete(results)
            return job_id

        except Exception as e:
            error_msg = str(e)
            job.fail(error_msg)
            self.logger.error(f"Data collection failed: {error_msg}")
            raise

    async def train_model(
        self,
        training_data_file: Optional[str] = None,
        model_name: Optional[str] = None,
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.001,
        optimize_hyperparams: bool = True,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        """Train model with progress tracking."""

        job_id = self.create_job("model_training")
        job = self.active_jobs[job_id]

        try:
            job.status = TrainingStatus.TRAINING_MODEL
            job.start()

            # Load training data if specified
            training_data = None
            if training_data_file:
                if progress_callback:
                    progress_callback(0.1, f"Loading training data: {training_data_file}")

                training_data = self.data_collector.load_training_data(training_data_file)
                if not training_data:
                    raise Exception(f"Failed to load training data: {training_data_file}")

            if progress_callback:
                progress_callback(0.2, "Starting model training...")

            # Generate model name
            if not model_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                model_name = f"tft_strategy_{timestamp}"

            # Train model
            training_results = await self.trainer.train_model(
                training_data=training_data,
                model_name=model_name,
                epochs=epochs,
                batch_size=batch_size,
                learning_rate=learning_rate,
                optimize_hyperparams=optimize_hyperparams
            )

            if progress_callback:
                progress_callback(1.0, "Model training completed")

            # Complete job
            results = {
                'model_name': model_name,
                'training_results': training_results
            }

            job.complete(results)
            return job_id

        except Exception as e:
            error_msg = str(e)
            job.fail(error_msg)
            self.logger.error(f"Model training failed: {error_msg}")
            raise

    async def full_training_pipeline(
        self,
        num_matches: int = 50,
        min_rank: str = "MASTER",
        days_back: int = 3,
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.001,
        optimize_hyperparams: bool = True,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        """Run complete training pipeline."""

        job_id = self.create_job("full_pipeline")
        job = self.active_jobs[job_id]

        try:
            job.status = TrainingStatus.COLLECTING_DATA
            job.start()

            # Step 1: Data collection
            if progress_callback:
                progress_callback(0.0, "Starting data collection...")

            data_job_id = await self.collect_training_data(
                num_matches=num_matches,
                min_rank=min_rank,
                days_back=days_back,
                progress_callback=lambda p, m: progress_callback(p * 0.5, f"Data: {m}") if progress_callback else None
            )

            data_job = self.get_job_status(data_job_id)
            if data_job.status != TrainingStatus.COMPLETED:
                raise Exception("Data collection failed")

            training_data_file = data_job.results['filename']

            # Step 2: Model training
            job.status = TrainingStatus.TRAINING_MODEL
            if progress_callback:
                progress_callback(0.5, "Starting model training...")

            train_job_id = await self.train_model(
                training_data_file=training_data_file,
                epochs=epochs,
                batch_size=batch_size,
                learning_rate=learning_rate,
                optimize_hyperparams=optimize_hyperparams,
                progress_callback=lambda p, m: progress_callback(0.5 + p * 0.5, f"Training: {m}") if progress_callback else None
            )

            train_job = self.get_job_status(train_job_id)
            if train_job.status != TrainingStatus.COMPLETED:
                raise Exception("Model training failed")

            # Complete pipeline
            results = {
                'data_collection': data_job.results,
                'model_training': train_job.results,
                'pipeline_summary': {
                    'data_samples': data_job.results['samples_collected'],
                    'model_name': train_job.results['model_name'],
                    'final_accuracy': train_job.results['training_results']['evaluation_metrics']['comp_type_accuracy']
                }
            }

            job.complete(results)
            return job_id

        except Exception as e:
            error_msg = str(e)
            job.fail(error_msg)
            self.logger.error(f"Training pipeline failed: {error_msg}")
            raise

    def _summarize_training_data(self, training_data: List[TrainingDataPoint]) -> Dict[str, Any]:
        """Create summary statistics for training data."""
        if not training_data:
            return {}

        placements = [point.placement for point in training_data]
        comp_types = [point.comp_type for point in training_data]

        summary = {
            'total_samples': len(training_data),
            'avg_placement': sum(placements) / len(placements),
            'unique_comp_types': len(set(comp_types)),
            'comp_distribution': {},
            'placement_distribution': {}
        }

        # Comp type distribution
        for comp_type in set(comp_types):
            summary['comp_distribution'][comp_type] = comp_types.count(comp_type)

        # Placement distribution
        for placement in range(1, 9):
            count = placements.count(placement)
            if count > 0:
                summary['placement_distribution'][placement] = count

        return summary

    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old completed jobs."""
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)

        jobs_to_remove = []
        for job_id, job in self.active_jobs.items():
            if job.end_time and job.end_time.timestamp() < cutoff:
                jobs_to_remove.append(job_id)

        for job_id in jobs_to_remove:
            del self.active_jobs[job_id]

        if jobs_to_remove:
            self.logger.info(f"Cleaned up {len(jobs_to_remove)} old training jobs")