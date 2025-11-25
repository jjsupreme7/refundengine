Batch research all unresearched vendors using AI. Skips already-researched vendors.

Arguments: $ARGUMENTS (optional)
- --batch-size N (default: 30)
- --start-from N (start at specific index)

Examples:
- /research-vendors (resume from where left off)
- /research-vendors --batch-size 50
- /research-vendors --start-from 100

Runtime: ~30-60 minutes for full batch

```bash
python scripts/ai_training/research_all_vendors.py --resume $ARGUMENTS
```
