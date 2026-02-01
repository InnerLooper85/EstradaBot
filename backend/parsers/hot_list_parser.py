"""
Hot List Parser
Parses the Hot List Excel file for priority scheduling.
"""

import pandas as pd
import re
from datetime import datetime
from typing import List, Dict, Any, Optional


def parse_redline_rubber_override(comments: str) -> Optional[str]:
    """
    Detect rubber override from COMMENTS field.

    Pattern: "REDLINE FOR [XE/HR/XR/XD/XP] INJECTION"

    Args:
        comments: COMMENTS field value

    Returns:
        Rubber type code (e.g., "XE", "HR") or None if no override detected
    """
    if not comments or pd.isna(comments):
        return None

    # Pattern: REDLINE FOR [rubber_type] INJECTION
    match = re.search(r'REDLINE\s+FOR\s+(XE|HR|XR|XD|XP)\s+INJECTION', str(comments), re.IGNORECASE)
    if match:
        return match.group(1).upper()

    return None


def parse_hot_list(filepath: str, sheet_name: str = None) -> List[Dict[str, Any]]:
    """
    Parse the Hot List Excel file.

    Expected columns (after header row):
    - WO# - Work order number
    - NEED BY DATE - "ASAP" or actual date
    - DATE REQ MADE - For FIFO tiebreaker
    - COMMENTS - May contain redline rubber override

    Args:
        filepath: Path to the Excel file
        sheet_name: Name of the sheet to read (default: first sheet)

    Returns:
        List of hot list entry dictionaries
    """
    try:
        # Read the Excel file - first row is headers
        if sheet_name:
            df = pd.read_excel(filepath, sheet_name=sheet_name, header=1)
        else:
            df = pd.read_excel(filepath, header=1)

        print(f"Loaded {len(df)} rows from Hot List")
        print(f"Columns found: {list(df.columns)}")

        entries = []
        errors = []

        for index, row in df.iterrows():
            try:
                # Get WO#
                wo_number = row.get('WO#')
                if pd.isna(wo_number):
                    continue
                wo_number = str(int(wo_number)) if isinstance(wo_number, float) else str(wo_number)

                # Get NEED BY DATE - check for "ASAP" or actual date
                need_by_raw = row.get('NEED BY DATE')
                is_asap = False
                need_by_date = None

                if pd.notna(need_by_raw):
                    if isinstance(need_by_raw, str) and need_by_raw.upper().strip() == 'ASAP':
                        is_asap = True
                    elif isinstance(need_by_raw, datetime):
                        need_by_date = need_by_raw
                    elif hasattr(need_by_raw, 'to_pydatetime'):
                        need_by_date = need_by_raw.to_pydatetime()

                # Get DATE REQ MADE for FIFO tiebreaker
                date_req_made = row.get('DATE REQ MADE')
                if pd.notna(date_req_made):
                    if isinstance(date_req_made, datetime):
                        pass  # Already datetime
                    elif hasattr(date_req_made, 'to_pydatetime'):
                        date_req_made = date_req_made.to_pydatetime()
                    else:
                        try:
                            date_req_made = pd.to_datetime(date_req_made)
                        except:
                            date_req_made = None
                else:
                    date_req_made = None

                # Get COMMENTS and check for rubber override
                comments = row.get('COMMENTS')
                rubber_override = parse_redline_rubber_override(comments)

                entry = {
                    'wo_number': wo_number,
                    'is_asap': is_asap,
                    'need_by_date': need_by_date,
                    'date_req_made': date_req_made,
                    'rubber_override': rubber_override,
                    'row_position': index + 1,  # 1-indexed position in spreadsheet
                    'comments': str(comments) if pd.notna(comments) else None,
                    'core': row.get('CORE'),
                    'item': row.get('ITEM'),
                    'description': row.get('DESCRIPTION'),
                    'customer': row.get('CUSTOMER NAME'),
                }

                entries.append(entry)

            except Exception as e:
                errors.append(f"Row {index}: Error parsing - {str(e)}")
                continue

        # Print summary
        asap_count = sum(1 for e in entries if e['is_asap'])
        dated_count = sum(1 for e in entries if e['need_by_date'])
        override_count = sum(1 for e in entries if e['rubber_override'])

        print(f"\nHot List Parsing complete:")
        print(f"  - Total entries: {len(entries)}")
        print(f"  - ASAP entries: {asap_count}")
        print(f"  - Dated entries: {dated_count}")
        print(f"  - With rubber override: {override_count}")
        print(f"  - Errors: {len(errors)}")

        if errors:
            print("\nErrors encountered:")
            for error in errors[:10]:
                print(f"  - {error}")

        return entries

    except Exception as e:
        print(f"Error reading Hot List file: {str(e)}")
        raise


def sort_hot_list_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort hot list entries by priority:
    1. ASAP first (sorted by DATE REQ MADE, then row position)
    2. Dated entries (sorted by NEED BY DATE, then DATE REQ MADE, then row position)

    Args:
        entries: List of hot list entry dictionaries

    Returns:
        Sorted list of entries
    """
    asap_entries = [e for e in entries if e['is_asap']]
    dated_entries = [e for e in entries if not e['is_asap'] and e['need_by_date']]
    other_entries = [e for e in entries if not e['is_asap'] and not e['need_by_date']]

    def get_date_req_key(entry):
        """Get sort key for DATE REQ MADE (earlier dates first)."""
        date_req = entry.get('date_req_made')
        if date_req and hasattr(date_req, 'timestamp'):
            return date_req.timestamp()
        return float('inf')

    def get_need_by_key(entry):
        """Get sort key for NEED BY DATE (earlier dates first)."""
        need_by = entry.get('need_by_date')
        if need_by and hasattr(need_by, 'timestamp'):
            return need_by.timestamp()
        return float('inf')

    # Sort ASAP entries by DATE REQ MADE, then row position
    asap_entries.sort(key=lambda e: (get_date_req_key(e), e.get('row_position', 0)))

    # Sort dated entries by NEED BY DATE, then DATE REQ MADE, then row position
    dated_entries.sort(key=lambda e: (get_need_by_key(e), get_date_req_key(e), e.get('row_position', 0)))

    # Sort other entries by DATE REQ MADE, then row position
    other_entries.sort(key=lambda e: (get_date_req_key(e), e.get('row_position', 0)))

    return asap_entries + dated_entries + other_entries


def get_hot_list_wo_numbers(entries: List[Dict[str, Any]]) -> set:
    """
    Get a set of WO numbers from hot list entries for quick lookup.

    Args:
        entries: List of hot list entry dictionaries

    Returns:
        Set of WO numbers
    """
    return {e['wo_number'] for e in entries}


def get_hot_list_lookup(entries: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Create a lookup dictionary from WO# to hot list entry.

    Args:
        entries: List of hot list entry dictionaries

    Returns:
        Dictionary mapping WO# to entry
    """
    return {e['wo_number']: e for e in entries}


if __name__ == "__main__":
    import sys

    # Test the parser
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    else:
        test_file = "../../Scheduler Bot Info/HOT LIST STA-ROT.xlsx"

    print("Testing Hot List Parser")
    print("=" * 60)

    try:
        entries = parse_hot_list(test_file)

        # Sort entries
        sorted_entries = sort_hot_list_entries(entries)

        # Show priority breakdown
        asap_entries = [e for e in sorted_entries if e['is_asap']]
        dated_entries = [e for e in sorted_entries if not e['is_asap'] and e['need_by_date']]

        print(f"\nPriority Breakdown:")
        print(f"  ASAP: {len(asap_entries)} orders")
        print(f"  Dated: {len(dated_entries)} orders")

        # Show rubber overrides
        overrides = [e for e in entries if e['rubber_override']]
        if overrides:
            print(f"\nRubber Overrides ({len(overrides)}):")
            for e in overrides[:5]:
                print(f"  WO# {e['wo_number']}: {e['rubber_override']} (from: {e['comments']})")

        # Show sample sorted entries
        print("\nSorted Hot List (first 10):")
        print("-" * 80)
        for i, entry in enumerate(sorted_entries[:10], 1):
            priority = "ASAP" if entry['is_asap'] else f"Date: {entry['need_by_date'].strftime('%m/%d') if entry['need_by_date'] else 'N/A'}"
            override = f" [REDLINE: {entry['rubber_override']}]" if entry['rubber_override'] else ""
            print(f"  {i}. WO# {entry['wo_number']} - {priority}{override}")

    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
