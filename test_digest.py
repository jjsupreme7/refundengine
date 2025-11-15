"""Test daily digest generation"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.core.daily_digest import DailyDigest

if __name__ == "__main__":
    print("Testing daily digest generation...\n")

    digest = DailyDigest()
    summary = digest.generate_digest()

    print(summary)
    print("\n" + "="*60)
    print("Testing Discord delivery...")

    success = digest.send_digest()

    if success:
        print("✅ Digest sent to Discord successfully!")
        print("\nCheck your Discord 'digest' channel for the message")
    else:
        print("❌ Failed to send digest")
