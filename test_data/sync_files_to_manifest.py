#!/usr/bin/env python3
"""
Sync Test Data Files to Manifest
================================

Moves any files in invoices/ and purchase_orders/ folders that are NOT
referenced in the manifest Excel files to a backup folder.

Usage:
    python test_data/sync_files_to_manifest.py
"""

import pandas as pd
from pathlib import Path
import shutil

# Base paths
BASE_DIR = Path(__file__).parent
BACKUP_DIR = BASE_DIR / "backup"

# Tax types and their manifests
TAX_TYPES = {
    "sales_tax": BASE_DIR / "SalesTax_Claims.xlsx",
    "use_tax": BASE_DIR / "UseTax_Claims.xlsx",
}


def get_referenced_files(manifest_path: Path) -> tuple[set, set]:
    """Get sets of invoice and PO filenames referenced in a manifest."""
    df = pd.read_excel(manifest_path)

    # Get invoice filenames (from Inv-1 FileName and Inv-2 FileName)
    invoices = set()
    for col in ["Inv-1 FileName", "Inv-2 FileName"]:
        if col in df.columns:
            invoices.update(df[col].dropna().astype(str).tolist())

    # Get PO filenames
    pos = set()
    if "PO_FileName" in df.columns:
        pos.update(df["PO_FileName"].dropna().astype(str).tolist())

    return invoices, pos


def sync_folder(source_dir: Path, backup_dir: Path, referenced_files: set, folder_type: str) -> tuple[int, int]:
    """Move files not in referenced_files to backup folder."""
    if not source_dir.exists():
        print(f"  Source folder does not exist: {source_dir}")
        return 0, 0

    # Create backup folder if needed
    backup_dir.mkdir(parents=True, exist_ok=True)

    kept = 0
    moved = 0

    for file_path in source_dir.iterdir():
        if not file_path.is_file():
            continue

        if file_path.name in referenced_files:
            kept += 1
        else:
            # Move to backup
            dest_path = backup_dir / file_path.name
            shutil.move(str(file_path), str(dest_path))
            moved += 1
            print(f"    Moved: {file_path.name}")

    return kept, moved


def main():
    print("=" * 60)
    print("Syncing test data files to manifest references")
    print("=" * 60)

    total_kept = 0
    total_moved = 0

    for tax_type, manifest_path in TAX_TYPES.items():
        print(f"\n{tax_type.upper()}")
        print("-" * 40)

        if not manifest_path.exists():
            print(f"  Manifest not found: {manifest_path}")
            continue

        # Get referenced files
        invoices_ref, pos_ref = get_referenced_files(manifest_path)
        print(f"  Manifest references: {len(invoices_ref)} invoices, {len(pos_ref)} POs")

        # Sync invoices folder
        invoices_src = BASE_DIR / tax_type / "invoices"
        invoices_backup = BACKUP_DIR / tax_type / "invoices"

        print(f"\n  Invoices folder: {invoices_src}")
        kept, moved = sync_folder(invoices_src, invoices_backup, invoices_ref, "invoices")
        print(f"    Kept: {kept}, Moved to backup: {moved}")
        total_kept += kept
        total_moved += moved

        # Sync purchase_orders folder
        po_src = BASE_DIR / tax_type / "purchase_orders"
        po_backup = BACKUP_DIR / tax_type / "purchase_orders"

        print(f"\n  Purchase Orders folder: {po_src}")
        kept, moved = sync_folder(po_src, po_backup, pos_ref, "purchase_orders")
        print(f"    Kept: {kept}, Moved to backup: {moved}")
        total_kept += kept
        total_moved += moved

    print("\n" + "=" * 60)
    print(f"SUMMARY: Kept {total_kept} files, Moved {total_moved} to backup")
    print(f"Backup location: {BACKUP_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
