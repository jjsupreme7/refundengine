#!/usr/bin/env python3
"""
Async Invoice Analyzer
Uses Celery workers to process invoices in parallel

Usage:
    # Start Redis
    redis-server

    # Start Celery workers (in another terminal)
    celery -A tasks worker --loglevel=info --concurrency=10

    # Queue invoices for processing
    python scripts/async_analyzer.py --excel Master_Refunds.xlsx --workers 10

    # Check progress
    python scripts/async_analyzer.py --check-progress <batch_id>
"""
import argparse
import os
import sys
import time
from pathlib import Path
from typing import List
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from tasks import analyze_batch, get_batch_progress, analyze_single_invoice
from celery.result import AsyncResult


def queue_batch(excel_path: str, start_row: int = 0, num_rows: int = None):
    """Queue Excel file for batch processing"""
    print(f"📋 Queuing invoices from: {excel_path}")
    print(f"   Start row: {start_row}")
    print(f"   Rows to process: {num_rows if num_rows else 'ALL'}")

    # Queue the batch
    result = analyze_batch.delay(excel_path, start_row, num_rows)

    print(f"\n✅ Batch queued successfully!")
    print(f"   Batch ID: {result.id}")
    print(f"\nTo check progress, run:")
    print(f"   python scripts/async_analyzer.py --check-progress {result.id}")

    return result.id


def check_progress(batch_id: str, watch: bool = False):
    """Check progress of a batch"""
    from celery.result import AsyncResult

    result = AsyncResult(batch_id)

    if watch:
        print("👀 Watching batch progress (Ctrl+C to exit)...")
        print()

    try:
        while True:
            if result.ready():
                batch_result = result.result

                if batch_result.get('status') == 'queued':
                    task_ids = batch_result.get('task_ids', [])
                    progress = get_batch_progress.delay(task_ids).get()

                    total = progress['total']
                    completed = progress['completed']
                    failed = progress['failed']
                    pending = progress['pending']
                    pct = progress['progress_pct']

                    # Progress bar
                    bar_length = 50
                    filled = int(bar_length * pct / 100)
                    bar = '█' * filled + '░' * (bar_length - filled)

                    print(f"\r[{bar}] {pct:.1f}%  |  ", end='')
                    print(f"Completed: {completed}/{total}  |  ", end='')
                    print(f"Failed: {failed}  |  ", end='')
                    print(f"Pending: {pending}    ", end='', flush=True)

                    if pending == 0:
                        print(f"\n\n✅ Batch processing complete!")
                        print(f"   Total processed: {completed}")
                        print(f"   Failed: {failed}")
                        break

                else:
                    print(f"❌ Batch error: {batch_result.get('error')}")
                    break

            if not watch:
                break

            time.sleep(2)  # Update every 2 seconds

    except KeyboardInterrupt:
        print("\n\n⏸️  Progress monitoring stopped")


def list_active_workers():
    """List active Celery workers"""
    from celery import Celery

    app = Celery('refund_engine', broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
    inspect = app.control.inspect()

    active = inspect.active()
    stats = inspect.stats()

    if not active:
        print("❌ No active workers found")
        print("\nTo start workers, run:")
        print("   celery -A tasks worker --loglevel=info --concurrency=10")
        return

    print("✅ Active Celery Workers:")
    print()

    for worker, tasks in active.items():
        worker_stats = stats.get(worker, {})
        print(f"🔧 {worker}")
        print(f"   Active tasks: {len(tasks)}")
        print(f"   Total processed: {worker_stats.get('total', 'N/A')}")
        print()


def main():
    parser = argparse.ArgumentParser(description='Async Invoice Analyzer')

    # Command group
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--excel', help='Excel file to process')
    group.add_argument('--check-progress', metavar='BATCH_ID', help='Check batch progress')
    group.add_argument('--list-workers', action='store_true', help='List active workers')

    # Options
    parser.add_argument('--start-row', type=int, default=0, help='Starting row (default: 0)')
    parser.add_argument('--num-rows', type=int, help='Number of rows to process (default: all)')
    parser.add_argument('--watch', action='store_true', help='Watch progress in real-time')

    args = parser.parse_args()

    if args.excel:
        queue_batch(args.excel, args.start_row, args.num_rows)

    elif args.check_progress:
        check_progress(args.check_progress, watch=args.watch)

    elif args.list_workers:
        list_active_workers()


if __name__ == '__main__':
    main()
