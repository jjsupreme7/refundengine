"""
Test Discord Webhooks

Verifies all 6 Discord webhooks are properly configured and working.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add agents module to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.core.communication import test_webhook

def main():
    """Test all configured Discord webhooks"""

    print("=" * 60)
    print("Discord Webhook Testing")
    print("=" * 60)
    print()

    channels = [
        "discussions",
        "code_quality",
        "knowledge",
        "patterns",
        "approvals",
        "digest"
    ]

    results = {}

    for channel in channels:
        print(f"Testing {channel} webhook...", end=" ")
        success = test_webhook(channel)
        results[channel] = success

        if success:
            print("✅ SUCCESS")
        else:
            print("❌ FAILED")

    print()
    print("=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = sum(1 for success in results.values() if success)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("✅ All webhooks configured correctly!")
        print()
        print("Next Steps:")
        print("1. Check your Discord server to see the test messages")
        print("2. Verify messages appear in the correct channels")
        print("3. Ready to build agent teams!")
    else:
        print("❌ Some webhooks failed. Please check:")
        print()
        for channel, success in results.items():
            if not success:
                env_var = f"DISCORD_WEBHOOK_{channel.upper()}"
                print(f"  - {env_var} in .env file")
        print()
        print("Ensure webhook URLs are valid and Discord server is accessible.")

    print()
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit(main())
