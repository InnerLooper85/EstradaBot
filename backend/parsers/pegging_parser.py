"""
Pegging Report Parser
Parses the Pegging Report Excel file to extract Actual Start Dates.
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Optional


def parse_pegging_actual_start_dates(filepath: str) -> Dict[str, datetime]:
    """
    Load actual start dates from Pegging Report.

    Args:
        filepath: Path to the Pegging Report Excel file

    Returns:
        Dict mapping Work Order number (as string) to Actual Start Date
    """
    try:
        df = pd.read_excel(filepath)

        print(f"Loaded {len(df)} rows from Pegging Report")

        # The Work Order is in '(Sup)Order Number' column
        # The Actual Start Date is in '(Sup)PrOrd Actual start date' column

        actual_starts = {}
        matched_count = 0

        for _, row in df.iterrows():
            wo_number = row.get('(Sup)Order Number')
            actual_start = row.get('(Sup)PrOrd Actual start date')

            if pd.notna(wo_number) and pd.notna(actual_start):
                # Convert WO number to string format matching other parsers
                try:
                    wo_str = str(int(float(wo_number)))
                    actual_starts[wo_str] = pd.to_datetime(actual_start)
                    matched_count += 1
                except (ValueError, TypeError):
                    continue

        print(f"  Extracted {matched_count} actual start dates")

        return actual_starts

    except Exception as e:
        print(f"Error reading Pegging Report: {str(e)}")
        return {}


if __name__ == "__main__":
    # Test the parser
    import sys
    from pathlib import Path

    print("Testing Pegging Report Parser")
    print("=" * 60)

    # Find most recent pegging report
    data_dir = Path(__file__).parent.parent.parent / "Scheduler Bot Info"
    import glob
    import os

    pattern = str(data_dir / "Pegging Report*.XLSX")
    matches = list(glob.glob(pattern))

    if not matches:
        pattern = str(data_dir / "Pegging Report*.xlsx")
        matches = list(glob.glob(pattern))

    if not matches:
        print("No Pegging Report file found")
        sys.exit(1)

    # Get most recent
    matches.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    filepath = matches[0]

    print(f"Loading: {filepath}")

    actual_starts = parse_pegging_actual_start_dates(filepath)

    print(f"\nSample entries (first 5):")
    for i, (wo, date) in enumerate(list(actual_starts.items())[:5]):
        print(f"  WO# {wo}: {date}")
