# Archived Scripts

These scripts have been archived because they were replaced by newer, better implementations.

## Archived on 2025-11-23

### extract_patterns_to_json.py
**Reason**: Replaced by newer extraction system with quality filtering

**Replaced by**:
- `scripts/extract_patterns_from_phase2.py` - Phase 2 extraction with filtering
- `scripts/extract_patterns_from_denodo.py` - Denodo extraction with filtering
- `scripts/extract_patterns_from_use_tax.py` - Use tax extraction
- `scripts/pattern_filters.py` - Shared quality filtering module

**Why deprecated**:
- No quality filtering (included PDFs, invoice numbers, junk data)
- Didn't separate sales tax vs use tax
- Monolithic approach (no shared filtering module)

### import_patterns_from_json.py
**Reason**: Replaced by newer Supabase upload script

**Replaced by**:
- `scripts/upload_patterns_to_supabase.py` - New uploader with dry-run support

**Why deprecated**:
- Less robust error handling
- No dry-run preview mode
- Doesn't handle new pattern table schema

### train_pattern_learner.py
**Reason**: Superseded by direct pattern extraction approach

**Replaced by**:
- Pattern extraction scripts (above) now directly create usable JSON patterns
- No intermediate "training" step needed

**Why deprecated**:
- Overcomplicated - patterns can be extracted directly from Excel
- Not actually "training" a model, just counting/aggregating
- Functionality now covered by extract_patterns_from_phase2.py

## Migration Notes

If you need the old functionality:
1. The git history preserves these files
2. You can checkout from commit `cfe2bd3` or earlier
3. Or use: `git show HEAD~1:scripts/ai_training/extract_patterns_to_json.py`

The new pattern extraction system provides:
- 86.6% noise reduction through quality filtering
- Separation of sales tax vs use tax patterns
- Complete vendor coverage (not just top 5 examples)
- Better integration with Supabase pattern tables
