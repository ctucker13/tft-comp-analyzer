#!/usr/bin/env python3
"""
Riot Games Data Dragon TFT Meta Data Fetcher

Fetches the latest official TFT meta data from Riot's Data Dragon API:
- Champions (units with costs, traits)
- Traits (synergies and effects)
- Items (equipment and effects)
- Augments (power-ups)
- Tacticians and other game data

Replaces hardcoded meta data with official Riot API data.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import polars as pl

# Configuration
BASE_URL = "https://ddragon.leagueoflegends.com"
VERSIONS_URL = f"{BASE_URL}/api/versions.json"
DATA_BASE_URL = f"{BASE_URL}/cdn"
LANGUAGE = "en_US"

# TFT Data Dragon endpoints
TFT_ENDPOINTS = {
    "champions": "tft-champion.json",
    "traits": "tft-trait.json",
    "items": "tft-item.json",
    "augments": "tft-augments.json",
    "tacticians": "tft-tactician.json",
    "queues": "tft-queues.json",
    "regalia": "tft-regalia.json",
    "arena": "tft-arena.json"
}

# Output configuration
OUTPUT_DIR = Path("data/riot_meta_data")
CACHE_DIR = Path("cache/riot_api")


class RiotDataDragonFetcher:
    """Fetches TFT meta data from Riot's Data Dragon API."""

    def __init__(self, timeout: int = 30, retries: int = 3):
        """Initialize the fetcher with configuration."""
        self.timeout = timeout
        self.retries = retries
        self.session: Optional[aiohttp.ClientSession] = None
        self.current_version: Optional[str] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def fetch_latest_version(self) -> str:
        """Fetch the latest TFT version from Riot API."""
        print("🔍 Fetching latest TFT version...")

        for attempt in range(self.retries):
            try:
                async with self.session.get(VERSIONS_URL) as response:
                    if response.status == 200:
                        versions = await response.json()
                        # Get the first version (latest)
                        latest_version = versions[0]
                        print(f"✅ Latest version: {latest_version}")
                        self.current_version = latest_version
                        return latest_version
                    else:
                        print(f"❌ Failed to fetch versions: HTTP {response.status}")
            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1} failed: {e}")
                if attempt < self.retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        raise Exception("Failed to fetch latest version after retries")

    async def fetch_endpoint_data(self, endpoint: str, version: str) -> Dict[str, Any]:
        """Fetch data from a specific TFT endpoint."""
        url = f"{DATA_BASE_URL}/{version}/data/{LANGUAGE}/{endpoint}"
        print(f"📡 Fetching {endpoint} from {url}")

        for attempt in range(self.retries):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Successfully fetched {endpoint}")
                        return data
                    else:
                        print(f"❌ Failed to fetch {endpoint}: HTTP {response.status}")
            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1} failed for {endpoint}: {e}")
                if attempt < self.retries - 1:
                    await asyncio.sleep(2 ** attempt)

        raise Exception(f"Failed to fetch {endpoint} after retries")

    async def fetch_all_tft_data(self) -> Dict[str, Any]:
        """Fetch all TFT meta data from Riot API."""
        print("🎮 Starting TFT Data Dragon fetch...")

        # Get latest version first
        if not self.current_version:
            await self.fetch_latest_version()

        # Fetch all endpoints concurrently
        tasks = []
        for category, endpoint in TFT_ENDPOINTS.items():
            task = asyncio.create_task(
                self.fetch_endpoint_data(endpoint, self.current_version),
                name=category
            )
            tasks.append((category, task))

        # Wait for all tasks to complete
        results = {}
        for category, task in tasks:
            try:
                data = await task
                results[category] = data
                print(f"✅ {category}: {len(data.get('data', {}))} items")
            except Exception as e:
                print(f"❌ Failed to fetch {category}: {e}")
                results[category] = None

        results['metadata'] = {
            'version': self.current_version,
            'fetched_at': datetime.now().isoformat(),
            'source': 'Riot Games Data Dragon API',
            'endpoints_fetched': len([r for r in results.values() if r is not None])
        }

        return results

    def process_champions_data(self, champions_data: Dict[str, Any]) -> pl.DataFrame:
        """Process champions data into structured format."""
        if not champions_data or 'data' not in champions_data:
            return pl.DataFrame()

        champions = []
        for champ_id, champ_data in champions_data['data'].items():
            # Filter for Set 15 champions ONLY - use precise matching to avoid substring issues
            # (TFTSet1 is a substring of TFTSet15, so we need to be more careful)
            if ('TFTTutorial' in champ_id or
                'TFTSet1/' in champ_id or 'TFTSet2/' in champ_id or 'TFTSet3/' in champ_id or
                'TFTSet4/' in champ_id or 'TFTSet5/' in champ_id or 'TFTSet6/' in champ_id or
                'TFTSet7/' in champ_id or 'TFTSet8/' in champ_id or 'TFTSet9/' in champ_id or
                'TFTSet10/' in champ_id or 'TFTSet11/' in champ_id or 'TFTSet12/' in champ_id or
                'TFTSet13/' in champ_id or 'TFTSet14/' in champ_id):
                continue

            # Only include Set 15 champions (TFTSet15)
            if 'TFTSet15' not in champ_id:
                continue

            # Extract clean champion ID
            clean_id = champ_data.get('id', champ_id)
            if 'TFT' in clean_id:
                clean_id = clean_id.split('_')[-1] if '_' in clean_id else clean_id

            champion = {
                'id': clean_id,
                'full_id': champ_id,
                'name': champ_data.get('name', clean_id),
                'cost': champ_data.get('tier', 1),  # 'tier' in Data Dragon = cost in TFT
                'traits': champ_data.get('traits', []),  # This might be empty in Data Dragon
                'stats': json.dumps(champ_data.get('stats', {})) if champ_data.get('stats') else '{}',
                'image': champ_data.get('image', {}).get('full', ''),
                'api_name': champ_data.get('apiName', clean_id)
            }
            champions.append(champion)

        return pl.DataFrame(champions)

    def process_traits_data(self, traits_data: Dict[str, Any]) -> pl.DataFrame:
        """Process traits data into structured format."""
        if not traits_data or 'data' not in traits_data:
            return pl.DataFrame()

        traits = []
        for trait_id, trait_data in traits_data['data'].items():
            # Filter for Set 15 traits ONLY - use precise matching to avoid substring issues
            if ('TFTTutorial' in trait_id or
                'TFTSet1/' in trait_id or 'TFTSet2/' in trait_id or 'TFTSet3/' in trait_id or
                'TFTSet4/' in trait_id or 'TFTSet5/' in trait_id or 'TFTSet6/' in trait_id or
                'TFTSet7/' in trait_id or 'TFTSet8/' in trait_id or 'TFTSet9/' in trait_id or
                'TFTSet10/' in trait_id or 'TFTSet11/' in trait_id or 'TFTSet12/' in trait_id or
                'TFTSet13/' in trait_id or 'TFTSet14/' in trait_id):
                continue

            # Only include Set 15 traits (TFTSet15)
            if 'TFTSet15' not in trait_id:
                continue

            # Extract clean trait ID
            clean_id = trait_data.get('id', trait_id)
            if 'TFT' in clean_id:
                clean_id = clean_id.split('_')[-1] if '_' in clean_id else clean_id

            trait = {
                'id': clean_id,
                'full_id': trait_id,
                'name': trait_data.get('name', clean_id),
                'description': trait_data.get('description', ''),
                'type': trait_data.get('type', 'origin'),  # origin, class, etc.
                'image': trait_data.get('image', {}).get('full', ''),
                'api_name': trait_data.get('apiName', clean_id)
            }
            traits.append(trait)

        return pl.DataFrame(traits)

    def process_items_data(self, items_data: Dict[str, Any]) -> pl.DataFrame:
        """Process items data into structured format."""
        if not items_data or 'data' not in items_data:
            return pl.DataFrame()

        items = []
        for item_id, item_data in items_data['data'].items():
            # Filter for Set 15 items ONLY (exclude old sets, include TFTSet15)
            if ('TFTSet1' in item_id or 'TFTSet2' in item_id or 'TFTSet3' in item_id or
                'TFTSet4' in item_id or 'TFTSet5' in item_id or 'TFTSet6' in item_id or
                'TFTSet7' in item_id or 'TFTSet8' in item_id or 'TFTSet9' in item_id or
                'TFTSet10' in item_id or 'TFTSet11' in item_id or 'TFTSet12' in item_id or
                'TFTSet13' in item_id or 'TFTSet14' in item_id):
                continue

            # Include current set items (Set 15) and generic items
            # (Generic items don't have set numbers)

            # Extract clean item ID
            clean_id = item_data.get('id', item_id)

            item = {
                'id': clean_id,
                'full_id': item_id,
                'name': item_data.get('name', clean_id),
                'description': item_data.get('description', ''),
                'short_desc': item_data.get('shortDesc', ''),
                'from_items': json.dumps(item_data.get('from', [])),  # Components
                'into_items': json.dumps(item_data.get('into', [])),   # Builds into
                'unique': item_data.get('unique', False),
                'image': item_data.get('image', {}).get('full', ''),
                'api_name': item_data.get('apiName', clean_id)
            }
            items.append(item)

        return pl.DataFrame(items)

    def process_augments_data(self, augments_data: Dict[str, Any]) -> pl.DataFrame:
        """Process augments data into structured format."""
        if not augments_data or 'data' not in augments_data:
            return pl.DataFrame()

        augments = []
        for aug_id, aug_data in augments_data['data'].items():
            # Filter for Set 15 augments ONLY (exclude old sets, include TFTSet15)
            if ('TFTSet1' in aug_id or 'TFTSet2' in aug_id or 'TFTSet3' in aug_id or
                'TFTSet4' in aug_id or 'TFTSet5' in aug_id or 'TFTSet6' in aug_id or
                'TFTSet7' in aug_id or 'TFTSet8' in aug_id or 'TFTSet9' in aug_id or
                'TFTSet10' in aug_id or 'TFTSet11' in aug_id or 'TFTSet12' in aug_id or
                'TFTSet13' in aug_id or 'TFTSet14' in aug_id):
                continue

            # Include current set augments (Set 15) and generic augments

            # Extract clean augment ID
            clean_id = aug_data.get('id', aug_id)

            augment = {
                'id': clean_id,
                'full_id': aug_id,
                'name': aug_data.get('name', clean_id),
                'description': aug_data.get('desc', ''),
                'tier': aug_data.get('tier', 1),  # Silver, Gold, Prismatic
                'image': aug_data.get('image', {}).get('full', ''),
                'api_name': aug_data.get('apiName', clean_id)
            }
            augments.append(augment)

        return pl.DataFrame(augments)

    def save_processed_data(self, all_data: Dict[str, Any]) -> Dict[str, Path]:
        """Save processed data to files."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_files = {}

        # Process and save each data type
        processors = {
            'champions': self.process_champions_data,
            'traits': self.process_traits_data,
            'items': self.process_items_data,
            'augments': self.process_augments_data
        }

        for data_type, processor in processors.items():
            if data_type in all_data and all_data[data_type]:
                try:
                    df = processor(all_data[data_type])
                    if not df.is_empty():
                        # Save as both Parquet and JSON
                        parquet_file = OUTPUT_DIR / f"tft_{data_type}_{timestamp}.parquet"
                        json_file = OUTPUT_DIR / f"tft_{data_type}_{timestamp}.json"

                        # Save Parquet for efficient data processing
                        df.write_parquet(parquet_file)

                        # Save JSON for human readability and compatibility
                        df.write_json(json_file)

                        saved_files[data_type] = {
                            'parquet': parquet_file,
                            'json': json_file,
                            'count': len(df)
                        }

                        print(f"✅ Saved {data_type}: {len(df)} items")
                    else:
                        print(f"⚠️ No data to save for {data_type}")
                except Exception as e:
                    print(f"❌ Failed to process {data_type}: {e}")

        # Save complete raw data
        raw_file = OUTPUT_DIR / f"tft_raw_data_{timestamp}.json"
        with open(raw_file, 'w') as f:
            json.dump(all_data, f, indent=2, default=str)
        saved_files['raw_data'] = raw_file

        # Save metadata summary
        summary_file = OUTPUT_DIR / f"tft_data_summary_{timestamp}.json"
        summary = {
            'metadata': all_data.get('metadata', {}),
            'data_counts': {k: v.get('count', 0) if isinstance(v, dict) else 0
                           for k, v in saved_files.items() if k != 'raw_data'},
            'files_created': {k: str(v.get('json', v)) if isinstance(v, dict) else str(v)
                             for k, v in saved_files.items()},
            'generated_at': datetime.now().isoformat()
        }

        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        saved_files['summary'] = summary_file

        return saved_files


async def main():
    """Main execution function."""
    print("🎮 Riot Games TFT Data Dragon Fetcher")
    print("=" * 50)

    start_time = time.time()

    try:
        async with RiotDataDragonFetcher() as fetcher:
            # Fetch all TFT data
            all_data = await fetcher.fetch_all_tft_data()

            # Process and save data
            saved_files = fetcher.save_processed_data(all_data)

            # Print summary
            print("\n📊 Fetch Summary:")
            print("=" * 30)

            metadata = all_data.get('metadata', {})
            print(f"🎯 Version: {metadata.get('version', 'Unknown')}")
            print(f"⏱️ Fetch Time: {time.time() - start_time:.2f}s")
            print(f"📁 Files Created: {len(saved_files)}")

            print("\n📋 Data Retrieved:")
            for data_type, file_info in saved_files.items():
                if data_type not in ['raw_data', 'summary'] and isinstance(file_info, dict):
                    count = file_info.get('count', 0)
                    print(f"  • {data_type.title()}: {count} items")

            print(f"\n💾 Output Directory: {OUTPUT_DIR.absolute()}")

            # Show some sample data
            if 'champions' in all_data and all_data['champions']:
                champ_data = all_data['champions']['data']
                sample_champs = list(champ_data.items())[:3]
                print("\n🔍 Sample Champions:")
                for champ_id, champ_info in sample_champs:
                    name = champ_info.get('name', champ_id)
                    cost = champ_info.get('tier', '?')
                    traits = champ_info.get('traits', [])
                    print(f"  • {name} ({cost}-cost): {', '.join(traits)}")

            return saved_files

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        raise


if __name__ == "__main__":
    # Run the async main function
    saved_files = asyncio.run(main())

    print("\n✅ TFT Data Dragon fetch completed!")
    print("🔄 Next steps:")
    print("  1. Review the fetched data in the output directory")
    print("  2. Update the TFT analyzer to use the new official data")
    print("  3. Test the system with the latest Riot API data")