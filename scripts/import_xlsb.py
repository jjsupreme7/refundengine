#!/usr/bin/env python3
"""
Import xlsb files with version tracking.

Copies xlsb to versions folder and fixes hyperlinks via Excel AppleScript.
No format conversion - stays xlsb to preserve all formatting.

Usage:
    python scripts/import_xlsb.py [xlsb_path]

If no path provided, looks for most recent xlsb in ~/Downloads/
"""

import shutil
import subprocess
import sys
import time
import re
from datetime import datetime
from pathlib import Path


# Paths
DOWNLOADS = Path.home() / "Downloads"
FILES_TO_ANALYZE = Path.home() / "Desktop" / "Files" / "Files to be Analyzed"
VERSIONS_DIR = FILES_TO_ANALYZE / "versions"
INVOICE_SERVER_URL = "http://localhost:8888"


def find_latest_xlsb(directory: Path = DOWNLOADS) -> Path | None:
    """Find the most recently modified xlsb file in directory."""
    xlsb_files = list(directory.glob("*.xlsb"))
    if not xlsb_files:
        return None
    return max(xlsb_files, key=lambda p: p.stat().st_mtime)


def generate_output_name(xlsb_path: Path, include_date: bool = True) -> str:
    """Generate output filename with optional date stamp."""
    base_name = xlsb_path.stem

    # Remove existing date patterns if present (e.g., "Dec 15 2025")
    base_name = re.sub(r'\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{4}$', '', base_name)

    # Replace spaces with underscores
    base_name = base_name.replace(" ", "_")

    if include_date:
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"{base_name}_{date_str}.xlsb"
    return f"{base_name}.xlsb"


def fix_hyperlinks_via_excel(xlsb_path: Path) -> dict:
    """
    Fix invoice hyperlinks in xlsb file using Excel AppleScript.

    Uses fill-down to quickly replace Windows paths with localhost URLs.

    Returns dict with stats.
    """
    stats = {"hyperlinks_fixed": 0}

    print("  Opening in Excel...")
    subprocess.run(["open", "-a", "Microsoft Excel", str(xlsb_path)], check=True)

    # Wait for file to load
    time.sleep(10)

    # Verify file is open
    result = subprocess.run(
        ["osascript", "-e", 'tell application "Microsoft Excel" to return name of active workbook'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise Exception("Failed to open file in Excel")

    workbook_name = result.stdout.strip()
    print(f"  Loaded: {workbook_name}")

    # Find column positions and fix hyperlinks using fill-down (fast)
    print("  Finding invoice columns and fixing hyperlinks...")

    fix_script = f'''
    tell application "Microsoft Excel"
        tell active workbook
            tell active sheet
                set headerRow to value of range "1:1"
                set inv1FormulaCol to 0
                set inv1FileCol to 0
                set inv2FormulaCol to 0
                set inv2FileCol to 0

                -- Find Inv 1 and Inv 2 columns
                repeat with colIdx from 1 to count of item 1 of headerRow
                    set cellVal to item colIdx of item 1 of headerRow
                    if cellVal is "Inv 1" then
                        set testFormula to formula of cell colIdx of row 2
                        if testFormula contains "HYPERLINK" then
                            set inv1FormulaCol to colIdx
                        else
                            set inv1FileCol to colIdx
                        end if
                    else if cellVal is "Inv 2" then
                        set testFormula to formula of cell colIdx of row 2
                        if testFormula contains "HYPERLINK" then
                            set inv2FormulaCol to colIdx
                        else
                            set inv2FileCol to colIdx
                        end if
                    end if
                end repeat

                set lastRow to first row index of used range + (count of rows of used range) - 1
                set fixCount to 0

                -- Fix Inv 1 using fill-down (much faster than row-by-row)
                if inv1FormulaCol > 0 and inv1FileCol > 0 then
                    -- Convert column numbers to letters
                    set inv1FormulaLetter to ""
                    set inv1FileLetter to ""

                    -- Simple conversion for columns up to ZZ
                    if inv1FormulaCol <= 26 then
                        set inv1FormulaLetter to character inv1FormulaCol of "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    else
                        set firstChar to character ((inv1FormulaCol - 1) div 26) of "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                        set secondChar to character (((inv1FormulaCol - 1) mod 26) + 1) of "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                        set inv1FormulaLetter to firstChar & secondChar
                    end if

                    if inv1FileCol <= 26 then
                        set inv1FileLetter to character inv1FileCol of "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    else
                        set firstChar to character ((inv1FileCol - 1) div 26) of "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                        set secondChar to character (((inv1FileCol - 1) mod 26) + 1) of "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                        set inv1FileLetter to firstChar & secondChar
                    end if

                    -- Set formula and fill down
                    set newFormula to "=HYPERLINK(\\"{INVOICE_SERVER_URL}/\\"&" & inv1FileLetter & "2," & inv1FileLetter & "2)"
                    set formula of cell inv1FormulaCol of row 2 to newFormula

                    set sourceRange to range (inv1FormulaLetter & "2")
                    set destRange to range (inv1FormulaLetter & "2:" & inv1FormulaLetter & lastRow)
                    copy range sourceRange
                    paste special destRange what paste formulas

                    set fixCount to fixCount + (lastRow - 1)
                end if

                -- Fix Inv 2 using fill-down
                if inv2FormulaCol > 0 and inv2FileCol > 0 then
                    if inv2FormulaCol <= 26 then
                        set inv2FormulaLetter to character inv2FormulaCol of "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    else
                        set firstChar to character ((inv2FormulaCol - 1) div 26) of "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                        set secondChar to character (((inv2FormulaCol - 1) mod 26) + 1) of "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                        set inv2FormulaLetter to firstChar & secondChar
                    end if

                    if inv2FileCol <= 26 then
                        set inv2FileLetter to character inv2FileCol of "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    else
                        set firstChar to character ((inv2FileCol - 1) div 26) of "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                        set secondChar to character (((inv2FileCol - 1) mod 26) + 1) of "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                        set inv2FileLetter to firstChar & secondChar
                    end if

                    set newFormula to "=HYPERLINK(\\"{INVOICE_SERVER_URL}/\\"&" & inv2FileLetter & "2," & inv2FileLetter & "2)"
                    set formula of cell inv2FormulaCol of row 2 to newFormula

                    set sourceRange to range (inv2FormulaLetter & "2")
                    set destRange to range (inv2FormulaLetter & "2:" & inv2FormulaLetter & lastRow)
                    copy range sourceRange
                    paste special destRange what paste formulas

                    set fixCount to fixCount + (lastRow - 1)
                end if

                return fixCount
            end tell
        end tell
    end tell
    '''

    result = subprocess.run(["osascript", "-e", fix_script], capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip().isdigit():
        stats["hyperlinks_fixed"] = int(result.stdout.strip())
    else:
        print(f"  Warning: {result.stderr}")

    print(f"  Fixed {stats['hyperlinks_fixed']:,} hyperlinks")

    # Save the file
    print("  Saving...")
    save_script = 'tell application "Microsoft Excel" to save active workbook'
    subprocess.run(["osascript", "-e", save_script], capture_output=True)

    # Close workbook
    subprocess.run(
        ["osascript", "-e", 'tell application "Microsoft Excel" to close active workbook saving no'],
        capture_output=True
    )

    return stats


def import_xlsb(xlsb_path: Path | str | None = None, dry_run: bool = False) -> dict:
    """
    Import an xlsb file to versions folder and fix hyperlinks.

    Copies the xlsb file (no format conversion) and uses Excel to fix
    hyperlinks to work on Mac with localhost invoice server.

    Args:
        xlsb_path: Path to xlsb file, or None to auto-detect from Downloads
        dry_run: If True, just report what would be done

    Returns:
        Dict with import results
    """
    # Find the xlsb file
    if xlsb_path is None:
        xlsb_path = find_latest_xlsb()
        if xlsb_path is None:
            return {"error": "No xlsb files found in Downloads"}
    else:
        xlsb_path = Path(xlsb_path)
        if not xlsb_path.exists():
            return {"error": f"File not found: {xlsb_path}"}

    # Ensure versions directory exists
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate output path
    output_name = generate_output_name(xlsb_path)
    output_path = VERSIONS_DIR / output_name

    result = {
        "source": str(xlsb_path),
        "destination": str(output_path),
        "source_size_mb": round(xlsb_path.stat().st_size / 1024 / 1024, 2),
    }

    if dry_run:
        result["dry_run"] = True
        return result

    # Check if output already exists
    if output_path.exists():
        result["warning"] = f"File already exists, adding timestamp"
        timestamp = datetime.now().strftime("%H%M%S")
        output_name = output_name.replace(".xlsb", f"_{timestamp}.xlsb")
        output_path = VERSIONS_DIR / output_name
        result["destination"] = str(output_path)

    try:
        # Copy xlsb to versions folder
        print("  Copying to versions folder...")
        shutil.copy2(xlsb_path, output_path)
        result["destination_size_mb"] = round(output_path.stat().st_size / 1024 / 1024, 2)

        # Fix hyperlinks using Excel
        hyperlink_stats = fix_hyperlinks_via_excel(output_path)
        result.update(hyperlink_stats)

    except Exception as e:
        result["error"] = str(e)

    return result


def main():
    """CLI entry point."""
    xlsb_path = sys.argv[1] if len(sys.argv) > 1 else None

    print("Importing xlsb file (no format conversion)...\n")
    result = import_xlsb(xlsb_path)

    if "error" in result:
        print(f"\nError: {result['error']}")
        sys.exit(1)

    print(f"\nSource: {result['source']}")
    print(f"Source size: {result['source_size_mb']} MB")
    print(f"\nDestination: {result['destination']}")
    print(f"Destination size: {result.get('destination_size_mb', 'N/A')} MB")
    print(f"\nFormat: xlsb (unchanged)")
    print(f"Hyperlinks fixed: {result.get('hyperlinks_fixed', 0):,}")

    if "warning" in result:
        print(f"\nWarning: {result['warning']}")

    print("\n✓ Import complete!")
    print(f"\nTo view invoices, run: python scripts/invoice_server.py")


if __name__ == "__main__":
    main()
