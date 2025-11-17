"""
Celery Tasks for Async Processing
Handles async processing of invoices with parallel workers
"""
import os
import sys
from pathlib import Path
from celery import Celery, Task
from celery.signals import task_failure, task_success
from typing import Dict, Any
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Initialize Celery app
app = Celery(
    'refund_engine',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Los_Angeles',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # 9 minutes soft limit
    worker_prefetch_multiplier=1,  # One task at a time per worker
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
)


class CallbackTask(Task):
    """Base task with callbacks for logging and monitoring"""

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        print(f"✅ Task {task_id} completed successfully")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        print(f"❌ Task {task_id} failed: {exc}")


@app.task(
    bind=True,
    base=CallbackTask,
    max_retries=3,
    default_retry_delay=60  # Retry after 1 minute
)
def analyze_single_invoice(self, row_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a single invoice row asynchronously

    Args:
        row_data: Dict containing invoice data (vendor, amount, tax, invoice_file, etc.)

    Returns:
        Dict with analysis results
    """
    try:
        from analysis.analyze_refunds_enhanced import EnhancedRefundAnalyzer

        # Initialize analyzer (using Enhanced RAG with decision intelligence)
        analyzer = EnhancedRefundAnalyzer()

        # Extract invoice file path
        invoice_file = row_data.get('invoice_file', '')
        if not invoice_file:
            return {
                'row_id': row_data.get('row_id', 'unknown'),
                'status': 'error',
                'error': 'No invoice file specified'
            }

        # Read PDF
        pdf_path = Path('client_documents') / invoice_file
        if not pdf_path.exists():
            return {
                'row_id': row_data.get('row_id', 'unknown'),
                'status': 'error',
                'error': f'Invoice file not found: {invoice_file}'
            }

        invoice_text = analyzer.extract_text_from_pdf(pdf_path)

        if not invoice_text:
            return {
                'row_id': row_data.get('row_id', 'unknown'),
                'status': 'error',
                'error': 'Could not extract text from PDF'
            }

        # Find line item
        amount = float(row_data.get('amount', 0))
        tax = float(row_data.get('tax', 0))

        line_item = analyzer.find_line_item_in_invoice(invoice_text, amount, tax)

        # Check vendor learning
        vendor_name = row_data.get('vendor', '')
        vendor_learning = analyzer.check_vendor_learning(
            vendor_name,
            line_item.get('product_desc', '')
        )

        # Search legal knowledge
        search_query = f"{line_item.get('product_desc', '')} {line_item.get('product_type', '')} Washington tax"
        legal_context = analyzer.search_legal_knowledge(search_query, top_k=5)

        # Analyze with AI (simplified - full implementation would call AI analysis)
        # For now, just return the extracted info
        result = {
            'row_id': row_data.get('row_id', 'unknown'),
            'status': 'success',
            'vendor': vendor_name,
            'product_desc': line_item.get('product_desc', 'Unknown'),
            'product_type': line_item.get('product_type', 'Unknown'),
            'confidence': line_item.get('confidence', 0),
            'legal_citations': [doc.get('citation', '') for doc in legal_context[:3]],
            'vendor_learning_used': vendor_learning is not None,
        }

        return result

    except Exception as exc:
        # Retry on failure
        print(f"Error processing row {row_data.get('row_id')}: {exc}")
        raise self.retry(exc=exc)


@app.task(bind=True, base=CallbackTask)
def analyze_batch(self, excel_path: str, start_row: int = 0, num_rows: int = None):
    """
    Queue entire Excel file for batch processing

    Args:
        excel_path: Path to Excel file
        start_row: Starting row index
        num_rows: Number of rows to process (None = all)

    Returns:
        Dict with batch status
    """
    try:
        import pandas as pd

        # Read Excel
        df = pd.read_excel(excel_path)

        if num_rows:
            df = df.iloc[start_row:start_row + num_rows]
        else:
            df = df.iloc[start_row:]

        # Queue individual tasks
        task_ids = []
        for idx, row in df.iterrows():
            row_data = {
                'row_id': idx,
                'vendor': row.get('Vendor', ''),
                'invoice_number': row.get('Invoice_Number', ''),
                'amount': row.get('Amount', 0),
                'tax': row.get('Tax', 0),
                'invoice_file': row.get('Inv_1_File', ''),
                'date': str(row.get('Date', '')),
            }

            # Queue task
            result = analyze_single_invoice.delay(row_data)
            task_ids.append(result.id)

        return {
            'status': 'queued',
            'total_tasks': len(task_ids),
            'task_ids': task_ids
        }

    except Exception as exc:
        print(f"Error queuing batch: {exc}")
        return {
            'status': 'error',
            'error': str(exc)
        }


@app.task
def get_batch_progress(task_ids: list) -> Dict[str, Any]:
    """
    Check progress of a batch of tasks

    Args:
        task_ids: List of Celery task IDs

    Returns:
        Dict with progress stats
    """
    from celery.result import AsyncResult

    completed = 0
    failed = 0
    pending = 0

    for task_id in task_ids:
        result = AsyncResult(task_id, app=app)
        if result.ready():
            if result.successful():
                completed += 1
            else:
                failed += 1
        else:
            pending += 1

    total = len(task_ids)
    progress_pct = (completed / total * 100) if total > 0 else 0

    return {
        'total': total,
        'completed': completed,
        'failed': failed,
        'pending': pending,
        'progress_pct': progress_pct
    }


# Monitoring signals
@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """Log successful task completions"""
    print(f"✅ Task completed: {sender.name}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """Log failed tasks"""
    print(f"❌ Task failed: {sender.name} - {exception}")
