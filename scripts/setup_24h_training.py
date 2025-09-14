#!/usr/bin/env python3
"""
Setup script for 24-hour training configuration.

This script configures the environment for optimal 24-hour training.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def setup_24h_environment():
    """Setup environment variables for 24-hour training."""
    print("🔧 Setting up 24-hour training configuration...")

    # Environment variables for 24-hour training
    env_vars = {
        'USE_24H_FILTER': 'true',
        'REQUIRE_PATCH_15_3': 'true',
        'PRIORITIZE_WINNERS': 'true',
        'USE_CACHE': 'false'  # Don't use cache for real-time training
    }

    env_file = project_root / '.env'

    # Read existing .env file
    existing_vars = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    existing_vars[key] = value

    # Update with 24-hour training settings
    updated = False
    for key, value in env_vars.items():
        if key not in existing_vars or existing_vars[key] != value:
            existing_vars[key] = value
            updated = True
            print(f"✅ Set {key}={value}")

    if updated:
        # Write updated .env file
        with open(env_file, 'w') as f:
            f.write("# TFT Analyzer Configuration\n")
            f.write("# Updated for 24-hour training\n\n")

            for key, value in existing_vars.items():
                f.write(f"{key}={value}\n")

        print(f"📝 Updated {env_file}")
    else:
        print("✅ Environment already configured for 24-hour training")

    return True


def create_training_directories():
    """Create necessary directories for 24-hour training."""
    print("📁 Creating training directories...")

    dirs = [
        'data/training',
        'models',
        'logs',
        'scripts/results'
    ]

    for dir_name in dirs:
        dir_path = project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ {dir_path}")


def show_usage_instructions():
    """Show how to use the 24-hour training system."""
    print("\n🚀 24-Hour Training System Ready!")
    print("=" * 50)
    print()
    print("📖 Usage Instructions:")
    print()
    print("1. Quick Daily Retrain (Recommended):")
    print("   uv run python scripts/quick_retrain.py")
    print()
    print("2. Full 24-Hour Pipeline:")
    print("   uv run python scripts/train_model_24h.py --full-pipeline")
    print()
    print("3. Collect Data Only:")
    print("   uv run python scripts/train_model_24h.py --collect-data --num-matches 150")
    print()
    print("4. Train with Existing Data:")
    print("   uv run python scripts/train_model_24h.py --train")
    print()
    print("💡 Tips:")
    print("• Run during peak hours for more high-rank games")
    print("• Use --rank CHALLENGER for highest quality data")
    print("• Models are saved with timestamps for easy tracking")
    print("• Each model is trained only on the last 24 hours of matches")
    print()
    print("🎯 Benefits:")
    print("• Always up-to-date with current meta")
    print("• Responds quickly to patch changes")
    print("• Higher quality strategic advice")
    print("• Reflects latest player strategies")


def main():
    """Main setup function."""
    print("🏗️ TFT 24-Hour Training Setup")
    print("=" * 40)
    print()

    try:
        # Setup environment
        setup_24h_environment()
        print()

        # Create directories
        create_training_directories()
        print()

        # Test API connection
        print("🔌 Testing API connection...")
        try:
            from config.settings import Settings
            settings = Settings()

            if settings.riot_api_key and not settings.riot_api_key.startswith('your_'):
                print("✅ Riot API key configured")
            else:
                print("⚠️ Riot API key not found - set RIOT_API_KEY in .env")

            if settings.anthropic_api_key and settings.anthropic_api_key.startswith('sk-ant-'):
                print("✅ Anthropic API key configured")
            elif settings.openai_api_key and settings.openai_api_key.startswith('sk-'):
                print("✅ OpenAI API key configured")
            else:
                print("⚠️ No LLM API keys found - set ANTHROPIC_API_KEY or OPENAI_API_KEY")

        except Exception as e:
            print(f"⚠️ Could not validate API keys: {e}")

        print()

        # Show instructions
        show_usage_instructions()

        return True

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)