# TFT ML Training Pipeline

## Training Pipeline Abstraction

The ML training has been abstracted from the UI into standalone scripts and a training manager for better separation of concerns.

## Issue Resolution

**Problem**: Data collection was returning 0 training points.
**Root Cause**: Expired Riot API key (Development keys expire every 24 hours).
**Solution**: Update your `RIOT_API_KEY` in `.env` with a fresh key from [Riot Developer Portal](https://developer.riotgames.com/).

## Standalone Training Scripts

### 1. Debug Data Collection
Test your API connection and data collection process:
```bash
uv run python scripts/debug_data_collection.py
```

### 2. Collect Training Data Only
```bash
# Collect 50 matches from Master+ players
uv run python scripts/train_model.py --collect-data --num-matches 50 --min-rank MASTER

# Collect from Challenger players (smaller dataset)
uv run python scripts/train_model.py --collect-data --num-matches 20 --min-rank CHALLENGER
```

### 3. Train Model with Existing Data
```bash
# Train using collected data
uv run python scripts/train_model.py --train --training-data training_data_MASTER_45samples_20250913_180000

# Train with custom parameters
uv run python scripts/train_model.py --train --training-data your_data_file --epochs 200 --batch-size 64
```

### 4. Full Training Pipeline
Run complete pipeline (data collection + training):
```bash
# Quick pipeline for testing
uv run python scripts/train_model.py --full-pipeline --num-matches 30 --epochs 50

# Production pipeline
uv run python scripts/train_model.py --full-pipeline --num-matches 100 --epochs 200 --model-name production_v1
```

### 5. Model Testing and Evaluation
```bash
# Test a specific model
uv run python scripts/test_model.py --model-path models/tft_strategy_20250913_180000

# Generate predictions on test scenarios
uv run python scripts/test_model.py --model-path models/your_model --generate-predictions

# Compare multiple models
uv run python scripts/test_model.py --compare-models --models-dir models/

# Comprehensive evaluation with test data
uv run python scripts/test_model.py --model-path models/your_model --test-data test_data_file --output-report evaluation_report.md
```

## Training Parameters

### Data Collection
- `--num-matches`: Number of matches to collect (10-500)
- `--min-rank`: Minimum player rank (CHALLENGER, GRANDMASTER, MASTER)
- `--days-back`: How many days back to look for matches (1-14)

### Model Training
- `--epochs`: Number of training epochs (10-500)
- `--batch-size`: Training batch size (16, 32, 64, 128)
- `--learning-rate`: Learning rate (0.0001, 0.001, 0.01)
- `--no-hyperopt`: Skip hyperparameter optimization (faster training)

## File Organization

```
data/
├── training/           # Raw training data files
└── processed/         # Processed training data

models/
├── tft_strategy_*/    # Trained model directories
│   ├── config.json    # Model configuration
│   ├── model_weights.pt  # PyTorch model weights
│   ├── feature_scaler.pkl  # Feature scaling
│   └── label_encoders.pkl  # Label encoders

scripts/
├── results/           # Training results and reports
└── *.log             # Training logs
```

## Training Manager API

For programmatic access, use the `TFTTrainingManager`:

```python
from src.tft_analyzer.ml.training.training_manager import TFTTrainingManager
from config.settings import Settings

# Initialize
settings = Settings()
manager = TFTTrainingManager(settings)

# List available models
models = manager.list_available_models()

# Run training with progress tracking
async def train_with_progress():
    def progress_callback(progress, message):
        print(f"Progress: {progress:.1%} - {message}")

    job_id = await manager.full_training_pipeline(
        num_matches=50,
        epochs=100,
        progress_callback=progress_callback
    )

    job = manager.get_job_status(job_id)
    return job.results

# Run it
import asyncio
results = asyncio.run(train_with_progress())
```

## Getting Started

1. **Update your Riot API key** in `.env` (get from [Riot Developer Portal](https://developer.riotgames.com/))

2. **Test your setup**:
   ```bash
   uv run python scripts/debug_data_collection.py
   ```

3. **Run a quick test**:
   ```bash
   uv run python scripts/train_model.py --full-pipeline --num-matches 20 --epochs 30
   ```

4. **Test your model**:
   ```bash
   uv run python scripts/test_model.py --model-path models/your_model --generate-predictions
   ```

## Model Performance Tips

- **Start small**: Use 20-30 matches for initial testing
- **Quality over quantity**: Master+ players provide better training data
- **Recent data**: Use `--days-back 3` for current meta
- **Hyperparameter optimization**: Enable for production models (takes longer)
- **Multiple models**: Train several models and compare performance

## Troubleshooting

**"API connection failed"**: Update your Riot API key in `.env`
**"No training data collected"**: Check if matches meet Set 15 and date criteria
**"Model training failed"**: Ensure you have enough training samples (minimum 10)
**"Import errors"**: Run `uv sync` to install all dependencies