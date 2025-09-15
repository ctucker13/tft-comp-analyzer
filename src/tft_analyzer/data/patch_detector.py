#!/usr/bin/env python3
"""
TFT Patch Detection Module

Detects the current TFT patch from various sources for training data filtering.
"""

import aiohttp
import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any

try:
    from ...config.settings import Settings
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
    from config.settings import Settings


class TFTPatchDetector:
    """Detects current TFT patch from multiple sources."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = Settings()

    async def get_current_patch(self) -> str:
        """
        Detect the current TFT patch from multiple sources.

        Returns:
            Current patch version (e.g., "15.4")
        """
        # Try multiple detection methods
        methods = [
            self._detect_from_config,
            self._detect_from_meta_sites,
            self._detect_from_fallback
        ]

        for method in methods:
            try:
                patch = await method()
                if patch:
                    self.logger.info(f"Detected current patch: {patch}")
                    return patch
            except Exception as e:
                self.logger.debug(f"Patch detection method failed: {e}")
                continue

        # Final fallback
        fallback_patch = self.settings.current_patch
        self.logger.warning(f"Using fallback patch: {fallback_patch}")
        return fallback_patch

    async def _detect_from_config(self) -> Optional[str]:
        """Get patch from current configuration."""
        patch = self.settings.current_patch
        if patch and patch != "15.17":  # Don't use the old default
            return patch
        return None

    async def _detect_from_meta_sites(self) -> Optional[str]:
        """Detect patch from TFT meta sites."""
        sites = [
            {
                'url': 'https://tactics.tools/api/patch',
                'parser': self._parse_tactics_tools_patch
            },
            {
                'url': 'https://www.metatft.com/api/set/15/patch',
                'parser': self._parse_metatft_patch
            }
        ]

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for site in sites:
                try:
                    async with session.get(site['url']) as response:
                        if response.status == 200:
                            data = await response.text()
                            patch = site['parser'](data)
                            if patch:
                                return patch
                except Exception as e:
                    self.logger.debug(f"Failed to get patch from {site['url']}: {e}")
                    continue

        return None

    def _parse_tactics_tools_patch(self, data: str) -> Optional[str]:
        """Parse patch from tactics.tools API response."""
        try:
            json_data = json.loads(data)
            if 'patch' in json_data:
                patch = json_data['patch']
                # Extract patch number (e.g., "15.4" from various formats)
                match = re.search(r'15\.(\d+)', str(patch))
                if match:
                    return f"15.{match.group(1)}"
        except:
            pass
        return None

    def _parse_metatft_patch(self, data: str) -> Optional[str]:
        """Parse patch from MetaTFT API response."""
        try:
            json_data = json.loads(data)
            if 'current_patch' in json_data:
                patch = json_data['current_patch']
                match = re.search(r'15\.(\d+)', str(patch))
                if match:
                    return f"15.{match.group(1)}"
        except:
            pass
        return None

    async def _detect_from_fallback(self) -> Optional[str]:
        """Fallback patch detection based on date."""
        # Simple date-based fallback - you can customize this
        current_date = datetime.now()

        # This is a rough estimate - adjust based on patch schedule
        if current_date >= datetime(2025, 1, 1):  # Update this based on patch dates
            return "15.4"  # Current known patch

        return None

    async def get_patch_info(self) -> Dict[str, Any]:
        """
        Get comprehensive patch information.

        Returns:
            Dictionary with patch details
        """
        patch = await self.get_current_patch()

        return {
            'patch': patch,
            'set_number': 15,
            'set_name': 'K.O. Coliseum',
            'detected_at': datetime.now().isoformat(),
            'major_version': '15',
            'minor_version': patch.split('.')[1] if '.' in patch else '4'
        }

    def is_patch_current(self, match_patch: str, current_patch: str = None) -> bool:
        """
        Check if a match patch is considered current.

        Args:
            match_patch: Patch version from match data
            current_patch: Current patch (detected automatically if None)

        Returns:
            True if match is from current patch
        """
        if not current_patch:
            # For synchronous check, use the configured patch
            current_patch = self.settings.current_patch

        # Extract version numbers
        current_match = re.search(r'15\.(\d+)', current_patch)
        match_match = re.search(r'15\.(\d+)', match_patch)

        if current_match and match_match:
            current_minor = int(current_match.group(1))
            match_minor = int(match_match.group(1))

            # Allow current patch and previous patch for transition periods
            return match_minor >= current_minor - 1

        return False


async def main():
    """Test patch detection."""
    detector = TFTPatchDetector()

    print("🔍 Testing TFT Patch Detection")
    print("=" * 40)

    patch_info = await detector.get_patch_info()

    print(f"Current Patch: {patch_info['patch']}")
    print(f"Set: {patch_info['set_number']} ({patch_info['set_name']})")
    print(f"Detected at: {patch_info['detected_at']}")

    # Test patch comparison
    test_patches = ["15.3", "15.4", "15.5", "14.23"]
    print("\nPatch Currency Tests:")
    for test_patch in test_patches:
        is_current = detector.is_patch_current(test_patch, patch_info['patch'])
        status = "✅ Current" if is_current else "❌ Old"
        print(f"  {test_patch}: {status}")


if __name__ == "__main__":
    asyncio.run(main())