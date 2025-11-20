"""
Agent Scheduler

Schedules autonomous agent teams to run during configured hours (1am-8am).
"""

from agents.teams.pattern_learning_council import run_pattern_learning
from agents.teams.knowledge_curation_team import run_knowledge_curation
from agents.teams.code_quality_council import run_code_quality_council
from agents.core.usage_tracker import UsageTracker
from agents.core.daily_digest import send_daily_digest
from agents.core.communication import post_to_discord
import os
import sys
from datetime import datetime
from pathlib import Path

import pytz
import yaml
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class AgentScheduler:
    """Manages scheduling for all agent teams"""

    def __init__(self, config_path: str = "agents/config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

        tz_name = self.config["schedule"]["timezone"]
        self.timezone = pytz.timezone(tz_name)
        self.scheduler = BlockingScheduler(timezone=self.timezone)
        self.usage_tracker = UsageTracker()

    def _load_config(self) -> dict:
        """Load configuration from YAML"""
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def setup_schedules(self):
        """Setup all agent schedules"""
        print("Setting up agent schedules...")

        start_hour = self.config["schedule"]["start_hour"]
        end_hour = self.config["schedule"]["end_hour"]
        teams = self.config["teams"]

        # Code Quality - Every 1.5 hours
        if teams["code_quality_council"]["enabled"]:
            self.scheduler.add_job(
                self._run_code_quality,
                trigger=CronTrigger(
                    hour=f"{start_hour}-{end_hour}",
                    minute="0,30",
                    timezone=self.timezone,
                ),
                id="code_quality",
                name="Code Quality Council",
                max_instances=1,
            )
            print("✓ Code Quality: Every 1.5 hours (1am-8am)")

        # Knowledge - Every 15 minutes
        if teams["knowledge_curation"]["enabled"]:
            self.scheduler.add_job(
                self._run_knowledge_curation,
                trigger=CronTrigger(
                    hour=f"{start_hour}-{end_hour}",
                    minute="*/15",
                    timezone=self.timezone,
                ),
                id="knowledge_curation",
                name="Knowledge Curation",
                max_instances=1,
            )
            print("✓ Knowledge Curation: Every 15 minutes (1am-8am)")

        # Pattern Learning - Every 3 hours
        if teams["pattern_learning"]["enabled"]:
            self.scheduler.add_job(
                self._run_pattern_learning,
                trigger=CronTrigger(
                    hour=f"{start_hour}-{end_hour}", minute="0", timezone=self.timezone
                ),
                id="pattern_learning",
                name="Pattern Learning",
                max_instances=1,
            )
            print("✓ Pattern Learning: Every 3 hours (1am-8am)")

        # Daily Digest - 8:00 AM
        digest_time = self.config["email"]["daily_digest"]["time"]
        hour, minute = digest_time.split(":")
        self.scheduler.add_job(
            self._send_digest,
            trigger=CronTrigger(
                hour=int(hour), minute=int(minute), timezone=self.timezone
            ),
            id="daily_digest",
            name="Daily Digest",
            max_instances=1,
        )
        print(f"✓ Daily Digest: {digest_time}")

    def _run_code_quality(self):
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Running Code Quality...")
            result = run_code_quality_council()
            print(f"✓ Completed: {result.get('proposals_created', 0)} proposals")
        except Exception as e:
            print(f"✗ Error: {e}")
            post_to_discord("code_quality", f"⚠️ Error: {str(e)}", "Scheduler")

    def _run_knowledge_curation(self):
        try:
            print(
                f"\n[{datetime.now().strftime('%H:%M:%S')}] Running Knowledge Curation..."
            )
            result = run_knowledge_curation()
            print(f"✓ Completed: {result.get('proposals_created', 0)} proposals")
        except Exception as e:
            print(f"✗ Error: {e}")
            post_to_discord("knowledge", f"⚠️ Error: {str(e)}", "Scheduler")

    def _run_pattern_learning(self):
        try:
            print(
                f"\n[{datetime.now().strftime('%H:%M:%S')}] Running Pattern Learning..."
            )
            result = run_pattern_learning()
            print(f"✓ Completed: {result.get('proposals_created', 0)} proposals")
        except Exception as e:
            print(f"✗ Error: {e}")
            post_to_discord("patterns", f"⚠️ Error: {str(e)}", "Scheduler")

    def _send_digest(self):
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Sending digest...")
            send_daily_digest()
            print("✓ Digest sent")
        except Exception as e:
            print(f"✗ Error: {e}")

    def start(self):
        """Start the scheduler"""
        self.setup_schedules()

        print("\n" + "=" * 60)
        print("AGENT SCHEDULER STARTED")
        print("=" * 60)
        print(f"Time: {datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(
            f"Hours: {self.config['schedule']['start_hour']
                      }:00 - {self.config['schedule']['end_hour']}:00"
        )
        print("\nPress Ctrl+C to stop\n" + "=" * 60 + "\n")

        post_to_discord(
            "digest",
            f"🤖 **Agent Scheduler Started**\n\n**Time**: {datetime.now(
                self.timezone).strftime('%I:%M %p')}\n**Schedule**: 1am-8am Pacific",
            "Scheduler",
        )

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print("\nShutting down...")
            post_to_discord("digest", "🛑 Scheduler stopped", "Scheduler")


if __name__ == "__main__":
    scheduler = AgentScheduler()
    scheduler.start()
