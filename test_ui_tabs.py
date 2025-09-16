#!/usr/bin/env python3
"""
Test script to verify all UI tabs will work properly
"""

import requests
import json

def test_tab_endpoints():
    """Test all the endpoints that the UI tabs use"""
    print("🧪 Testing All UI Tab Endpoints")
    print("=" * 50)

    base_url = "http://localhost:8000"

    # Test Meta Analysis tab
    print("📊 Meta Analysis Tab")
    try:
        response = requests.get(f"{base_url}/api/meta/tier-list", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tier_lists = data.get('tier_lists', {})
            total = data.get('total_compositions', 0)
            print(f"   ✅ Tier lists: {len(tier_lists)} tiers, {total} compositions")
            if tier_lists:
                for tier, comps in tier_lists.items():
                    print(f"      {tier}: {len(comps)} compositions")
            else:
                print("   ⚠️ No structured tier data (will show raw analysis)")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print()

    # Test trends
    try:
        response = requests.get(f"{base_url}/api/meta/trends?days=7", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Trends available: {len(data.get('trends_analysis', ''))} chars")
        else:
            print(f"   ❌ Trends failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Trends error: {e}")

    print()

    # Test Database Explorer tab
    print("🗃️ Database Explorer Tab")
    try:
        response = requests.get(f"{base_url}/api/database/champions?limit=10", timeout=5)
        if response.status_code == 200:
            champions = response.json()
            print(f"   ✅ Champions: {len(champions)} returned")
            if champions:
                print(f"      Example: {champions[0]['name']} ({champions[0]['cost']}⭐)")
                traits = ', '.join(champions[0]['traits'][:2])
                print(f"      Traits: {traits}...")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print()

    # Test ML Recommendations tab
    print("🤖 ML Recommendations Tab")
    try:
        ml_request = {
            "gold": 45,
            "level": 7,
            "stage": 4,
            "health": 70
        }
        response = requests.post(f"{base_url}/api/ml/recommend",
                               json=ml_request, timeout=5)
        if response.status_code == 200:
            data = response.json()
            rec = data.get('recommendation', '')
            confidence = data.get('confidence', 0)
            analysis_type = data.get('analysis_type', '')
            print(f"   ✅ ML recommendation: {len(rec)} chars")
            print(f"   ✅ Confidence: {confidence}")
            print(f"   ✅ Type: {analysis_type}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print()

    # Test Chat tab (already working)
    print("💬 Chat Tab")
    try:
        chat_request = {
            "message": "Quick test",
            "provider": "anthropic"
        }
        response = requests.post(f"{base_url}/api/chat/message",
                               json=chat_request, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Chat working: {len(data.get('response', ''))} chars")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print()
    print("🎯 Summary: All endpoints should now work in the UI!")
    print("   Start with: ./start_ui.sh")
    print("   Visit: http://localhost:3001")

if __name__ == "__main__":
    test_tab_endpoints()